# Backup & Recovery

## What needs backing up

| Store | Durable data? | Backup approach |
|---|---|---|
| PostgreSQL (`db`) | Yes — the source of truth for every user, submission, roast, and audit row | `pg_dump`/managed snapshots (below) |
| Media/storage (`media/`, `LocalFileSystemStorage`) | Yes — uploaded resume bytes (`SubmissionAsset.storage_key`) | Filesystem-level backup or, better, move to an object-storage backend with versioning (below) |
| Redis (`redis`) | **No** — treat as fully ephemeral | Not backed up; see "Why Redis doesn't need backup" below |

If both Postgres and media are restored to a mutually consistent point in
time, the application recovers completely. Redis loss requires no restore
step at all.

## PostgreSQL

### Backup

`scripts/backup_db.sh` wraps `pg_dump` in the custom (`-Fc`) format
(compressed, supports selective/parallel restore, works with `pg_restore`
regardless of whether you dump the whole DB or need to restore just one
table later). Reads the same `POSTGRES_*` env vars the app itself uses:

```bash
POSTGRES_HOST=... POSTGRES_PORT=... POSTGRES_USER=... POSTGRES_PASSWORD=... \
  ./scripts/backup_db.sh ./backups
```

This is a manual/cron-triggered convenience, not a scheduler — run it from
whatever triggers periodic jobs in your environment (a `cron` entry next
to the deployment, a scheduled CI job, a Kubernetes `CronJob`, etc.). If
you're on a managed database (RDS, Cloud SQL, etc.), prefer that
provider's automated snapshot/point-in-time-recovery feature over this
script — it's continuous (point-in-time restore, not just daily
snapshots) and doesn't require you to manage backup storage/retention
yourself.

### Recommended schedule/retention

- **Daily** full dumps, retained **30 days**, is a reasonable default for
  most deployments this size.
- If using a managed database with point-in-time recovery, prefer that —
  it gives you restore granularity down to a specific transaction, not
  just "as of last night's dump."
- Store backups somewhere independent of the database host itself
  (object storage with versioning, a separate region/account) — a backup
  that lives on the same disk as the database it protects doesn't protect
  against host/volume loss.

### Restore

```bash
pg_restore \
  --host=<host> --port=<port> --username=<user> --dbname=<db> \
  --clean --if-exists \
  roast_anything_<timestamp>.dump
```

`--clean --if-exists` drops existing objects before recreating them, so
this is safe to run against a database that already has (stale/wrong)
data in it — but it **is** destructive to whatever's currently there, so
double-check you're pointed at the right target before running it against
anything but a fresh/scratch database.

## Media (submission asset files)

Today's default storage backend is `LocalFileSystemStorage`
(`apps/common/storage/local.py`), rooted at `MEDIA_ROOT` — files live on
whatever disk the app container/host has mounted at that path
(`media_data` volume in the Docker Compose files).

Two options, in increasing order of robustness:

1. **Filesystem backup**: back up `MEDIA_ROOT` the same way you'd back up
   any other persistent volume (snapshot, `rsync`/`restic` to a remote
   target, etc.), ideally on the same schedule as the database dump above
   so a restore can bring both back to a consistent point in time.
2. **Move to object storage** (recommended for real production use):
   `apps.common.storage.StorageBackend` (`apps/common/storage/base.py`)
   is the whole reason this is a config change, not a rewrite — add an
   S3-compatible `StorageBackend` implementation, register it in
   `apps.common.storage.factory._BACKENDS`, and set
   `STORAGE_BACKEND=s3` (or similar). Object storage with versioning
   (S3 versioning, or equivalent) gives you both durability and backup
   for free — no separate backup job needed for media at all.

## Why Redis doesn't need backup

Redis here is purely the Celery broker/result backend and the DRF
throttle-counter cache (`config/settings/base.py`'s `CACHES`) — nothing
stored there is authoritative:

- **In-flight Celery messages** lost on a Redis restart correspond to
  `ExtractionTask`/`RoastRun` rows that would otherwise be stuck
  `queued`/`processing` — the Beat reconciliation sweeps
  (`apps.roasts.tasks.reconcile_stuck_roast_runs`,
  `apps.extraction.tasks.reconcile_stuck_extraction_tasks`) already exist
  to fail those rows cleanly so a user can retry; Redis loss just makes
  that happen sooner (once Redis comes back and the sweep next runs)
  rather than after a worker crash.
- **Throttle counters** resetting on Redis loss just means rate limits
  restart from zero — a minor, self-correcting availability nicety at
  worst, never a correctness issue.

If you'd still like continuity across a planned Redis restart (rather
than relying on the reconciliation sweep), Redis's own RDB/AOF
persistence can be enabled — but it's an availability optimization, not
a backup requirement, since nothing in this store is the durable record
of anything.

## Restore drill checklist

Practice this periodically — a backup you've never restored isn't a
verified backup:

1. Provision a scratch Postgres instance (never restore-test against
   production).
2. `pg_restore` the most recent dump into it (see above).
3. Restore the corresponding media backup (or point `MEDIA_ROOT`/
   `STORAGE_BACKEND` at the matching object-storage snapshot) to the same
   point in time as the DB dump.
4. Point a scratch app instance's `DATABASES`/`MEDIA_ROOT` at the
   restored copies and run `python manage.py check` +
   `python manage.py migrate --check` (confirms the restored schema
   matches what the current codebase expects — a mismatch here means the
   backup predates a migration that's since landed, which is fine to
   know about but should inform your restore runbook).
5. Spot-check: log in as a known test user, confirm their submissions
   list, confirm a known submission's asset downloads correctly (proves
   DB and media are consistent with each other, not just individually
   intact).
6. Record how long the drill took — that's your realistic RTO (recovery
   time objective), not whatever number was assumed before actually
   trying it.
