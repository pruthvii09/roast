# Production Readiness Report

Phase 8 output: a security review of the backend built across all prior phases, the concrete
fixes that came out of it, the new features it added (weekly roast quota, account deletion),
and what's left before a real production launch. Written to be read standalone — it doesn't
assume you've read the phase history.

## 1. Completed security checks

Organized by the audit categories this phase covered. "Fixed this phase" items link back to
the file that changed; "already correct" items existed before this phase and were verified,
not modified.

### Authentication
- JWT via `djangorestframework-simplejwt`: 15 min access / 7 day refresh (env-configurable),
  `ROTATE_REFRESH_TOKENS` + `BLACKLIST_AFTER_ROTATION` (a rotated refresh token is one-time-use
  — reuse is rejected). *Already correct.*
- Logout blacklists the presented refresh token; password change blacklists **every**
  outstanding refresh token for the user (all sessions), atomically. *Already correct*
  (`apps/accounts/services.py`).
- Standard Django password hashing (PBKDF2) + `AUTH_PASSWORD_VALIDATORS` (similarity, min
  length 10, common-password, not-fully-numeric). *Already correct.*
- Login gives no distinct error for "wrong password" vs. "no such account" (simplejwt's
  generic message + Django's dummy-hasher timing-parity behavior for nonexistent users).
  *Already correct.*
- **Fixed this phase**: minimal audit logging (register/login success-or-failure/logout/
  password-change/account-deletion) — event + user id/email + outcome, never
  password/token content (`apps/accounts/views.py`). There was previously no audit trail for
  these events at all.

### Authorization / object-level permissions
- Every owner-scoped resource (submissions, assets, roast runs) is scoped at the **queryset**
  level (never relies on object-permission checks alone) and returns 404, not 403, for another
  user's resource — this avoids confirming a resource's existence via status code.
  `apps.common.permissions.IsOwner` is explicit defense-in-depth layered on top, not the
  primary mechanism. *Already correct*, verified across `apps/accounts`, `apps/submissions`,
  `apps/roasts` (full endpoint-by-endpoint table in §6 below).
- **New this phase**: `RoastRun.owner` (denormalized from `submission.owner`) is used
  consistently for ownership checks where it's now the more direct path (`apps/roasts/services.py`).

### File uploads
- Real content-type sniffing via `libmagic` (`apps.common.validation.files`) — never trusts
  the client's `Content-Type` header or filename extension, defeating a renamed-extension
  spoofing attack. *Already correct.*
- Server-generated, opaque storage keys (`apps.common.validation.keys.generate_storage_key`)
  — never derived from client input (filename, content). *Already correct.*
- Path-traversal-proof local storage backend (`apps.common.storage.local.LocalFileSystemStorage`
  — resolves and validates every path stays under `MEDIA_ROOT`). *Already correct.*
- Size caps enforced both at Django's request-body level (`FILE_UPLOAD_MAX_MEMORY_SIZE`) and
  explicitly in application code (`validate_file_size` against `MAX_UPLOAD_SIZE_BYTES`).
  *Already correct.*
- **Fixed this phase**: JSON/form body size is now capped independently and much lower
  (`MAX_JSON_BODY_SIZE_BYTES`, 1 MiB default) than the file-upload cap (10 MiB default) — see
  §"Request validation / maximum request sizes" below.

### SSRF
- `apps.extraction.http.is_safe_public_url()` (built in an earlier phase, unchanged this
  phase): scheme allowlist (http/https only) + every resolved IP checked against
  private/loopback/link-local/reserved/multicast ranges, applied to `WebsiteProcessor`'s
  arbitrary-URL fetch. Not airtight against DNS rebinding (documented as such — a practical
  guard, not a bulletproof one). `GitHubProcessor` deliberately does **not** need this guard:
  its requests always target a fixed, hardcoded host (`EXTRACTION_GITHUB_API_BASE_URL`), never
  one derived from user input. *Already correct, re-verified this phase.*

### XSS
- Not applicable to the API surface: every endpoint returns JSON via DRF renderers, no server
  templates render user-submitted content as HTML. Django admin auto-escapes displayed field
  values by default. *Reviewed, no gap found.*

### CSRF
- The API is pure JWT-bearer auth (`DEFAULT_AUTHENTICATION_CLASSES` = `JWTAuthentication`
  only; `SessionAuthentication` is never enabled anywhere) — CSRF doesn't apply to it by
  design. The Django admin (`/admin/`) does use session+CSRF cookie auth, correctly, since
  it's a separate, cookie-based surface. *Already correct.*

### CORS
- Default-deny: `CORS_ALLOWED_ORIGINS` defaults to an empty allowlist, `CORS_ALLOW_CREDENTIALS`
  defaults to `False`. `prod.py` explicitly sets `CORS_ALLOW_ALL_ORIGINS = False`. *Already
  correct.*

### SQL injection
- Pure Django ORM throughout — no `.raw()`, `.extra()`, `RawSQL`, or manual `cursor.execute()`
  calls anywhere in the codebase (verified by repo-wide grep). *No exposure; reviewed, no gap.*

### Rate limiting
- **Fixed this phase**: previously, only auth endpoints were throttled at all — submissions
  and roasts (the actual cost/resource-intensive endpoints — file upload + async extraction,
  and paid AI provider calls) had zero rate limiting. Now: a generous global default
  (`UserRateThrottle`/`AnonRateThrottle`) covers every endpoint without its own scope, plus
  dedicated `submission-create` and `roast-create` scopes (`config/settings/base.py`,
  `apps/submissions/views.py`, `apps/roasts/views.py`).
- **Fixed this phase**: the throttle cache itself was previously unconfigured (defaulting to
  per-process `LocMemCache`), which means throttling would have silently not worked correctly
  across multiple gunicorn worker processes in any real deployment. Now backed by Redis on a
  dedicated DB index (`CACHES` in `config/settings/base.py`).
- **New this phase**: the weekly roast quota (§ below) is a *business-rule* limit, layered on
  top of (not instead of) the burst-rate `roast-create` throttle.

### Object-level permissions
- See "Authorization" above — full endpoint table in §6.

### API enumeration
- Registration reveals whether an email is already registered
  (`apps/accounts/serializers.py: validate_email`) — a working enumeration oracle, throttled at
  10/hour/IP by default. **Accepted risk, not changed this phase** — see §2.
- Login gives no such signal (see "Authentication" above).
- Every owner-scoped resource returns 404 (not 403) for another user's ID, so ownership can't
  be probed via status-code difference. *Already correct.*

### UUID exposure
- Every model uses a UUIDv4 primary key (`TimeStampedUUIDModel`), not a sequential integer —
  IDs aren't enumerable/guessable by incrementing. *By design, already correct.*

### Public share links
- `apps/sharing` has **no models, no views, no URLs** — confirmed via direct inspection, not
  just the README's description. `Submission.visibility` (private/link/public) is a schema
  placeholder for a future sharing surface; nothing currently reads or enforces it — setting
  it today has no effect on access control. **Not a vulnerability today** (there is no public
  endpoint to exploit), but a hard requirement for whoever builds `apps/sharing`: it must
  explicitly implement its own access-control check against `visibility`, since none of the
  existing owner-scoped views will do it for free.

### AI prompt injection
- **Fixed this phase**: `extracted_text`/`submission.title` (structurally untrusted —
  arbitrary resume/website/GitHub content) are now wrapped in `<submitted_content>` delimiters
  (`apps/ai/prompts/renderer.py`), and the active system prompt (v2,
  `apps/ai/migrations/0003_seed_prompt_versions_v2.py`) has an explicit rule telling the model
  to treat that block as data only, never instructions, and to roast an embedded manipulation
  attempt rather than obey it. Mitigates, doesn't eliminate — see the README's "Prompt
  injection resistance" section for what's still possible (bounded to influencing roast
  content/tone; output is always schema-validated, so it can't escape the response shape).

### AI output validation
- `RoastResponseSchema` (Pydantic, `extra="forbid"`) strictly validates every AI response
  before anything is persisted — unknown fields rejected, severity restricted to 5 known
  values, score bounded 0-100, minimum section/finding counts enforced. A response that fails
  validation is retried like any other transient failure. *Already correct, unchanged this
  phase.*

### Celery retries
- **Fixed this phase**: the codebase's own docstrings assumed "at-least-once delivery" as the
  basis for its idempotent claim-and-process pattern, but `CELERY_TASK_ACKS_LATE` was never
  actually set — the real (default) behavior is closer to at-most-once (a worker killed
  mid-task loses the message entirely). Now `CELERY_TASK_ACKS_LATE=True` +
  `CELERY_TASK_REJECT_ON_WORKER_LOST=True` + `CELERY_WORKER_PREFETCH_MULTIPLIER=1`
  (`config/settings/base.py`) make delivery actually match what the code already assumed.
- **Fixed this phase**: `process_roast_run` had no `soft_time_limit`/`time_limit` at all
  (unlike `extract_submission_task`, which already did) — added
  (`ROAST_TASK_SOFT_TIME_LIMIT_SECONDS`/`ROAST_TASK_TIME_LIMIT_SECONDS`).
- **New this phase**: Beat-scheduled reconciliation sweeps
  (`apps.roasts.tasks.reconcile_stuck_roast_runs`,
  `apps.extraction.tasks.reconcile_stuck_extraction_tasks`) fail any row stuck
  `queued`/`processing` past a generous staleness threshold — the actual backstop for a task
  that dies *after* claiming its row, a case `acks_late` alone cannot recover (see the code
  comment above `CELERY_TASK_ACKS_LATE` for the full reasoning — a naive Celery-level
  `self.retry()` was considered and rejected during this phase's planning because it would
  silently no-op against the existing claim pattern).

### Idempotency
- Roast creation: partial unique DB constraint on `(submission, language, intensity)` for
  in-flight rows — a duplicate request returns the existing run rather than racing to create a
  second one, enforced by Postgres, not just application logic. *Already correct.*
- Both processing tasks: idempotent claim via conditional `UPDATE ... WHERE status='queued'`
  — safe against Celery's at-least-once redelivery. *Already correct.*
- **New this phase**: the weekly quota check is itself made concurrency-safe via
  `select_for_update()` on the owner's `User` row (see §3) — without it, N simultaneous
  requests from one user could each observe "under quota" and all proceed.

### Database transactions
- Reviewed every multi-step write across `apps/accounts`, `apps/submissions`, `apps/roasts`,
  `apps/extraction`: all are correctly wrapped in `transaction.atomic()`, with one documented,
  accepted risk (`delete_submission`: a storage-delete failure partway through rolls back the
  DB but doesn't "un-delete" files already removed from disk — inherent to mixing filesystem
  side effects with DB transactions, low-risk for the local backend's simple unlink).
  *Already correct; `delete_user_account` (new this phase) follows the same
  purge-storage-then-delete-DB pattern.*

### Sensitive logging
- `apps.common.logging_formatters.JSONFormatter` has an explicit "never log file bytes/
  extracted text/prompts/AI outputs" policy, enforced by convention/review (not tooling) —
  and, having re-audited every `logger.*` call site added or touched this phase, none violate
  it. The new audit-log lines (`apps/accounts/views.py`) intentionally include email addresses
  (standard for an auth audit trail — see the code comment there) but never
  passwords/tokens.
- **Fixed this phase**: `apps.ai.services.roasting` now logs the raw per-attempt AI provider
  error detail server-side (`logger.warning`/`logger.error`) instead of only in the
  client-facing field — see "internal provider errors" below.

### Secrets
- **Fixed this phase**: `config.settings.base.SECRET_KEY` has an insecure dev-only fallback
  (`"insecure-dev-key-change-me"`) that `prod.py` previously never overrode or asserted —
  meaning a misconfigured deploy with `DJANGO_SECRET_KEY` unset would silently start with a
  well-known secret key. `prod.py` now requires it via `env("DJANGO_SECRET_KEY")` with no
  default (raises `ImproperlyConfigured` at settings-load time if unset), mirroring the
  pre-existing `ALLOWED_HOSTS` pattern.
- No real secret is hardcoded anywhere in the repo (verified by review of every settings file
  and both compose files); `.env`/`.env.*` are gitignored, `.env.example` is the only
  allowlisted exception. *Mostly already correct; the `SECRET_KEY` gap above was the exception.*
- **Fixed this phase**: no `.dockerignore` existed — a `docker build` from the repo root would
  bake `.env` (and therefore every secret in it) directly into an image layer via `COPY . /app`,
  regardless of `docker-compose.yml` also correctly injecting env vars at runtime. Added.

### Error handling
- **Fixed this phase**: `apps.ai.providers.openai.OpenAIProvider` wraps the raw OpenAI SDK
  exception text into `AIProviderError`, and that raw text previously flowed all the way into
  `RoastRun.error_message` — exposed via the roast detail/status API. Now the raw detail stays
  server-side (log line + the admin-only `AIRequest.error` audit field); the client-facing
  `RoastRun.error_message` is always a generic, safe message on final failure
  (`apps/ai/services/roasting.py`).
- **Fixed this phase**: `LogoutView` previously built its error response by hand, bypassing the
  standard `{"success": false, "error": {...}}` envelope every other endpoint uses — now raises
  a proper `ValidationError` like everywhere else (`apps/accounts/views.py`).
- `apps.common.exception_handler.custom_exception_handler`: unhandled exceptions never leak a
  traceback or DB error text to the client (logged server-side only, generic `INTERNAL_ERROR`
  response). *Already correct.*
- **New this phase**: every error response (and every structured log line) now carries a
  `request_id` for correlating a client's bug report with server-side logs
  (`apps.common.middleware.RequestIDMiddleware`, `apps.common.exception_handler`).

### Storage security
- See "File uploads" above — path traversal, opaque keys, content sniffing. *Already correct.*

## 2. Remaining risks (not fixed this phase — deliberately out of scope)

| Risk | Why it's deferred | What it would take |
|---|---|---|
| No email verification at registration | No email-sending infrastructure exists anywhere in the project; this is a new feature, not a hardening fix | An email provider integration, a verification-token flow, and a decision on whether unverified accounts can do anything before confirming |
| No password-reset ("forgot password") flow | Same reason — no email infrastructure | Same as above, plus a reset-token model with expiry |
| Registration reveals whether an email is taken | A near-universal SaaS tradeoff (GitHub, most consumer products do the same); the throttle (10/hour/IP default) already bounds how fast it can be probed | Would require accepting worse registration UX (always return 201, silently email the existing owner instead) — a product decision, not purely technical |
| `apps/sharing`/`apps/feedback` still fully unimplemented | Outside this phase's scope (a hardening/review phase, not a feature-build phase) — confirmed via direct inspection, not assumed | Building them; whoever does must explicitly implement `Submission.visibility` enforcement (see §1, "Public share links") since nothing does today |
| Dependency pins are ~18-20 months old (`requirements/*.txt`) | A full upgrade pass has its own regression risk and wasn't part of this review's scope | Run `pip-audit` (or similar) against current pins, then a scheduled, tested upgrade pass — Django, `djangorestframework-simplejwt`, `psycopg`, and `openai` are the highest-value targets given how central they are |
| Django admin (`/admin/`) has no dedicated throttle or network-level restriction | Requires `is_staff`/superuser credentials already; deferred as a defense-in-depth nicety, not a live gap | Network-level restriction (VPN/IP allowlist) is the usual answer for admin panels, or `django-axes` for login-attempt throttling if network restriction isn't feasible |
| Readiness check treats a dead Celery worker fleet as "not ready" for the **web** service too | This was the explicit fix requested/planned this phase, but note the tradeoff: in an orchestrator that scales web and worker independently, this couples web's readiness to worker health | If that coupling turns out to be too aggressive in practice, split into two probes (a "web is fine" liveness-style check vs. a deeper "workers are healthy" check consumed only by alerting, not by the web pod's own readiness gate) |
| No distributed tracing across the async boundary | The new request-ID correlation (§1) only covers a single HTTP request/response and the logs it directly produces — a Celery task processing a roast doesn't inherit the request ID of whoever created it | Thread the originating request ID through `RoastRun`/`ExtractionTask` (e.g. a column) if full request → task log correlation becomes a real debugging need |
| No automated security regression tests | Per explicit instruction for this phase — everything below was verified manually against the real dev stack instead | Add targeted tests for the quota's concurrency-safety and the account-deletion cascade, the two places a regression would be costliest |

## 3. New feature: weekly roast quota

Every roast-creation *attempt* (not just completed ones) counts against `ROAST_WEEKLY_QUOTA`
(default 3) in a rolling `ROAST_QUOTA_WINDOW_DAYS`-day window (default 7, not calendar-aligned).
Enforced in `apps.roasts.services.create_roast_run` by locking the owner's `User` row
(`select_for_update()`) before counting, so concurrent requests from the same user can't all
observe "under quota" and all proceed — different users never contend with each other.
Exceeding it raises DRF's built-in `Throttled` (429, standard error envelope, `wait` set to
seconds until the oldest in-window roast ages out). `GET /api/v1/roasts/quota/` exposes
`{limit, used, remaining, resets_at}` so a client can show remaining quota ahead of a 429.
`RoastRun.owner` (new denormalized FK + `(owner, created_at)` index) makes the count efficient
without a join through `Submission`.

## 4. New feature: account deletion

`DELETE /api/v1/auth/me/` (password re-confirmation required in the body — the same re-auth
pattern as change-password, so a leaked access token alone can't trigger it) permanently
deletes a user and everything they own. `apps.accounts.services.delete_user_account` purges
every owned asset's storage bytes first (the one thing Django's cascade can't do — it doesn't
know about the storage backend), then deletes the `User` row inside a transaction; Django's
existing `on_delete=CASCADE` chains handle every dependent row (submissions, assets, roast
runs, sections, findings, extraction tasks, AI-request audit rows) with zero extra code.
simplejwt's own `OutstandingToken`/`BlacklistedToken` rows use `SET_NULL` (their default) and
are left behind with a null user — acceptable, they hold no PII beyond an already-meaningless
token.

## 5. Recommended infrastructure

- **Database**: managed Postgres (RDS, Cloud SQL, etc.) over a self-hosted container for
  production — automated backups/point-in-time recovery beat the `pg_dump` script in
  `docs/BACKUP_RECOVERY.md`, which is a fallback/convenience, not a substitute.
- **Redis**: managed (ElastiCache, Memorystore) or a well-monitored self-hosted instance.
  Nothing stored there needs to survive a restart (see `docs/BACKUP_RECOVERY.md`'s "why Redis
  doesn't need backup"), but it does need to be *up* — it's now a hard dependency for both
  Celery task delivery and the throttle cache.
- **Object storage** for `apps.common.storage` (S3-compatible) instead of the local filesystem
  backend, once running more than one web replica — `LocalFileSystemStorage` ties uploaded
  files to whichever container/host wrote them. The storage abstraction already exists
  specifically so this is a new `StorageBackend` implementation + a config change, not a
  rewrite (see `apps/common/storage/base.py`).
- **A TLS-terminating reverse proxy or load balancer** in front of `web` — `prod.py`'s
  `SECURE_PROXY_SSL_HEADER` assumes this topology (gunicorn itself doesn't terminate TLS).
- **A process supervisor / orchestrator** (Kubernetes, ECS, systemd units, etc.) that runs
  `web`, `worker`, and **`beat`** as separate, independently-restartable services — see
  `docker-compose.prod.yml` for the shape, and note `beat` is not optional (§1, "Celery
  retries").
- **Log aggregation** that ingests the JSON lines gunicorn/Celery write to stdout/stderr
  (CloudWatch, Loki, Datadog, etc.) — `request_id` in every line is what makes this useful for
  incident correlation.
- **A secrets manager** (not raw `.env` files) for `DJANGO_SECRET_KEY`, `POSTGRES_PASSWORD`,
  `OPENAI_API_KEY`, etc. in any real deployment — `.env` here is a local-dev/simple-deploy
  convenience.

## 6. Endpoint-by-endpoint permission review

| Endpoint | Auth | Scope/ownership | Throttle |
|---|---|---|---|
| `GET /api/v1/health/` | `AllowAny` | N/A (liveness only) | global default |
| `GET /api/v1/health/ready/` | `AllowAny` | N/A (DB/Redis/Celery checks, no data) | global default |
| `POST /api/v1/auth/register/` | `AllowAny` | N/A | `auth-register` (10/hour) |
| `POST /api/v1/auth/login/` | `AllowAny` | N/A | `auth-login` (10/min) |
| `POST /api/v1/auth/refresh/` | `AllowAny` | N/A | `auth-refresh` (30/min) |
| `POST /api/v1/auth/logout/` | `IsAuthenticated` | blacklists caller's own presented token | `auth-logout` (30/min) |
| `GET/PATCH /api/v1/auth/me/` | `IsAuthenticated` | hardcoded to `request.user` — no ID param, no IDOR surface | global default |
| `DELETE /api/v1/auth/me/` | `IsAuthenticated` | same, + password re-confirmation | global default |
| `POST /api/v1/auth/change-password/` | `IsAuthenticated` | operates on `request.user` only | `auth-password-change` (5/hour) |
| `GET/POST /api/v1/submissions/` | `IsAuthenticated` + `IsSubmissionOwner` | queryset scoped to `owner=request.user` | POST: `submission-create` (20/hour); GET: global default |
| `GET/PATCH/DELETE /api/v1/submissions/{id}/` | `IsAuthenticated` + `IsSubmissionOwner` | queryset-scoped, 404 for non-owned | global default |
| `GET /api/v1/submissions/{id}/status/` | `IsAuthenticated` + `IsSubmissionOwner` | queryset-scoped | global default |
| `GET /api/v1/submissions/{sid}/assets/{aid}/download/` | `IsAuthenticated` | ownership checked in `get_owned_asset_or_404` + submission-id cross-check | global default |
| `GET/POST /api/v1/submissions/{sid}/roasts/` | `IsAuthenticated` | parent submission resolved via owner-scoped 404 | POST: `roast-create` (10/hour) + weekly quota; GET: global default |
| `GET /api/v1/roasts/quota/` | `IsAuthenticated` | always the caller's own quota | global default |
| `GET/DELETE /api/v1/roasts/{id}/` | `IsAuthenticated` + `IsRoastRunOwner` | queryset-scoped, 404 for non-owned | global default |
| `GET /api/v1/roasts/{id}/status/` | `IsAuthenticated` + `IsRoastRunOwner` | queryset-scoped | global default |
| `/admin/` | Django session auth, `is_staff` required | Django's own admin permission model | none (see §2) |
| `/api/v1/schema/`, `/swagger-ui/`, `/redoc/` | `IsAuthenticated` in prod, `AllowAny` in dev only | N/A | global default |
| `apps/sharing`, `apps/feedback` | — | no URLs exist at all | — |

## 7. Required environment variables

See `.env.example` for the complete, commented list (every variable below has a sensible dev
default there). The ones that matter most for a production deploy specifically:

**Must be set explicitly (no safe default in prod):**
- `DJANGO_SECRET_KEY` — `config.settings.prod` refuses to start without it.
- `DJANGO_ALLOWED_HOSTS`
- `POSTGRES_PASSWORD`, `POSTGRES_HOST`, `POSTGRES_DB`, `POSTGRES_USER`
- `OPENAI_API_KEY` (if `AI_PROVIDER=openai`; the `stub` provider needs no key but never
  produces a real roast)
- `CORS_ALLOWED_ORIGINS` — empty by default, which blocks every browser-based frontend origin
  until set

**Worth reviewing before launch (secure but generic defaults):**
- `ROAST_WEEKLY_QUOTA` / `ROAST_QUOTA_WINDOW_DAYS` — the actual product/cost decision this
  phase's quota implements; 3/week is a starting point, not a researched number.
- `THROTTLE_*` rates — tune to expected real traffic.
- `MAX_UPLOAD_SIZE_BYTES` / `MAX_JSON_BODY_SIZE_BYTES`
- `DJANGO_CSRF_TRUSTED_ORIGINS` — only if the Django admin is exposed through a proxy on a
  host not already covered by `DJANGO_ALLOWED_HOSTS`.
- `SECURE_HSTS_SECONDS` (defaults to 7 days) — many guides recommend ramping this up only
  after confirming HTTPS works correctly end-to-end, to avoid locking out a misconfigured
  domain.

**Infrastructure connection strings:**
- `REDIS_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`, `DJANGO_CACHE_URL`
- `STORAGE_BACKEND`, `MEDIA_ROOT` (or the equivalent for whatever `StorageBackend` you add for
  object storage — see §5)

## 8. Deployment checklist

1. Set every "must be set explicitly" env var in §7, from a secrets manager, not a checked-in
   file.
2. Confirm `DJANGO_SETTINGS_MODULE=config.settings.prod`.
3. Run migrations as an explicit deploy step (`python manage.py migrate`), not automatically
   from every service's entrypoint — `docker-compose.prod.yml` already disables
   `DJANGO_AUTO_MIGRATE` for `worker`/`beat` for this reason; do the same for `web` in a
   multi-replica deployment (one migration run, not N racing each other).
4. Deploy `web` (gunicorn), `worker`, and `beat` as separate, independently-monitored
   processes/services — **`beat` is not optional** (§1, "Celery retries").
5. Point TLS termination (load balancer / reverse proxy) at `web`; confirm
   `SECURE_PROXY_SSL_HEADER`'s assumption matches your proxy's actual header behavior before
   enabling `DJANGO_SECURE_SSL_REDIRECT` in front of real traffic.
6. Confirm `GET /api/v1/health/ready/` reports all three checks (`database`, `redis`,
   `celery`) healthy before routing traffic to a new `web` instance.
7. Confirm outbound network access to `api.github.com` (GitHub processing) and your AI
   provider's API host — both are required for two of the three submission types to work at
   all.
8. Set up the backup schedule from `docs/BACKUP_RECOVERY.md` (or confirm your managed
   database's automated backups are enabled) *before* accepting real user data, not after.
9. Wire log aggregation to capture `web`/`worker`/`beat`'s stdout/stderr JSON lines; confirm
   `request_id` shows up and is searchable.
10. Do one restore drill (`docs/BACKUP_RECOVERY.md`'s checklist) before launch, so your first
    real recovery isn't also your first rehearsal.
11. Decide and document your policy on the remaining risks in §2 (particularly registration
    enumeration and the lack of email verification) — these are conscious tradeoffs this phase
    made, not oversights, but they're yours to own going forward.
