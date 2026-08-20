# Roast Anything — Backend

Production Django/DRF backend for Roast Anything: users submit a resume, website,
or GitHub profile and get an AI-generated roast plus constructive feedback.

## Architecture

```
apps/
  common/       shared base models, storage abstraction, file validation,
                response envelope, pagination, health/readiness checks,
                request-ID middleware + structured logging
  accounts/     custom User model, JWT auth (register/login/refresh/logout/me/
                change-password/account-deletion)
  submissions/  Submission + SubmissionAsset (source material users upload)
  extraction/   async submission-processing pipeline (resume/website/GitHub -> plain
                text + metadata), fully decoupled from the roast engine (see below)
  roasts/       RoastRun/RoastSection/RoastFinding + async processing task +
                weekly per-user roast quota
  ai/           AI provider abstraction, prompt versioning,
                the roast-generation orchestration service (see below)
  sharing/      scaffolded, no models yet — ShareLink, Reactions
  feedback/     scaffolded, no models yet — Feedback
config/         Django project package (settings/urls/celery/wsgi/asgi)
docs/           BACKUP_RECOVERY.md, PRODUCTION_READINESS.md
```

### `apps/extraction` internal layout

```
apps/extraction/
  models.py           ExtractionTask — one row per processing attempt (queued -> processing
                       -> completed/failed), mirrors RoastRun's claim-and-process shape
  exceptions.py         ExtractionError + UnsupportedContentTypeError / CorruptedDocumentError /
                        EmptyDocumentError / InvalidSourceURLError / RemoteFetchError
  processors/
    base.py              SubmissionProcessor ABC: process(self, submission) -> ProcessingResult
                          (text + optional structured metadata) — generic over file-based
                          (resume) and URL-based (website/GitHub) sources alike
    resume.py             ResumeProcessor — the only file-based processor (pypdf, PDF only
                          today; {content_type: parser} dict is the extension point for DOCX)
    website.py             WebsiteProcessor — SSRF-guarded public URL fetch -> visible text
    github.py               GitHubProcessor — GitHub REST API (repo/user metadata + README)
    registry.py            get_processor(submission) factory (mirrors get_ai_provider()/
                          get_storage()), keyed by submission_type — the extension point for
                          new source types later; unregistered types raise
                          UnsupportedContentTypeError with zero call-site changes elsewhere
  http.py                is_safe_public_url() (the SSRF guard) + fetch_url() (timeout- and
                        size-bounded GET) — shared by WebsiteProcessor and GitHubProcessor
  text_utils.py           normalize_text() — whitespace collapsing + length cap shared by
                        WebsiteProcessor/GitHubProcessor's stored output
  tempfiles.py           materialize_asset_to_tempfile() — streams an asset into a private,
                        auto-deleted NamedTemporaryFile so ResumeProcessor never assumes a
                        storage backend hands back a real local path
  services.py            queue_extraction / dispatch_extraction_processing / process_extraction
                        / mark_extraction_failed — the claim/validate/store pipeline
  tasks.py               extract_submission_task Celery task (claim -> process, same
                        idempotent-claim pattern as apps.roasts.tasks.process_roast_run)
  migrations/
```

### `apps/ai` internal layout

```
apps/ai/
  models.py           PromptVersion, AIRequest (audit log — one row per provider call attempt)
  providers/
    base.py            AIProvider ABC + AIGenerationResult — generic (prompt in, raw text+usage out),
                        zero roast-domain knowledge, zero vendor knowledge
    stub.py             NotImplementedAIProvider — default; always raises AIProviderError
    openai.py           OpenAIProvider — real implementation (Chat Completions + JSON mode)
    __init__.py          get_ai_provider() factory, keyed by settings.AI_PROVIDER
  prompts/
    templates.py         base system-prompt template (EN/HI/Hinglish `{language_instruction}`
                          variants) + per-intensity instruction strings
    renderer.py           fills in the two generation-time placeholders left in a stored
                          PromptVersion (submission_type, intensity_instructions)
    schema.py             RoastResponseSchema — strict Pydantic schema the AI's raw JSON
                          must satisfy exactly (extra="forbid", enum-restricted severity)
  services/
    extraction.py         "load submission": a ~5-line internal-consistency guard that just
                          reads Submission.extracted_text — every submission type is fully
                          processed by apps.extraction before a roast can even start, so
                          apps.ai contains no submission-type-specific processing of its own
    roasting.py           the orchestrator: build prompt -> call provider (bounded,
                          exponential retry) -> validate -> persist -> mark completed/failed
  migrations/
    0002_seed_prompt_versions.py   seeds the 3 required active PromptVersion rows
```

All APIs are versioned under `/api/v1/`.

## Requirements

- Python 3.12
- Docker + Docker Compose (for Postgres/Red. is; also runs the app itself if you prefer)
- `libmagic` installed locally if running outside Docker (`brew install libmagic` on macOS) — needed for real file-content sniffing on uploads

## Local development setup

1. Copy the environment template and fill in real values (never commit `.env`):

   ```bash
   cp .env.example .env
   ```

2. Create a virtualenv and install dependencies:

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements/dev.txt -r requirements/test.txt
   ```

3. Start Postgres and Redis (see **Database setup** below), then run migrations and the dev server:

   ```bash
   python manage.py migrate
   python manage.py runserver
   ```

4. API docs: http://localhost:8000/api/v1/schema/swagger-ui/
   Health checks: http://localhost:8000/api/v1/health/ and `/api/v1/health/ready/`

### Running everything in Docker instead

```bash
docker compose up --build
```

This starts `db`, `redis`, `web` (Django dev server), and `worker` (Celery — see the Celery
section below for what's registered). Migrations run automatically on container start via
`docker/entrypoint.sh` (controlled by `DJANGO_AUTO_MIGRATE`, default `true`).

For a production-shaped stack instead (gunicorn, non-root, no dev dependencies, plus a `beat`
service — see `docs/PRODUCTION_READINESS.md`):

```bash
docker compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

## Database setup

`docker-compose.yml` provisions Postgres 16 and Redis 7:

```bash
docker compose up -d db redis
python manage.py migrate
```

If ports `5432`/`6379` are already taken by another local service, override the
host-side mapping without touching container-internal config:

```bash
POSTGRES_HOST_PORT=5433 REDIS_HOST_PORT=6380 docker compose up -d db redis
```

...and point your local (non-Docker) `.env` at the same overridden ports
(`POSTGRES_PORT`, and the port embedded in `REDIS_URL`/`CELERY_BROKER_URL`/`CELERY_RESULT_BACKEND`).

To create a superuser for the Django admin:

```bash
python manage.py createsuperuser
```

## Celery

```bash
celery -A config worker -l info
celery -A config beat -l info    # required for the reconciliation sweeps below
```

In Docker, the `worker` service runs the first command; `docker-compose.prod.yml` (not
`docker-compose.yml`, which is dev-only) adds a `beat` service for the second. Four tasks are
registered:

- `apps.extraction.extract_submission` — dispatched for every submission, of any type, right
  after creation (see the extraction pipeline below).
- `apps.roasts.process_roast_run` — dispatched on roast creation (see the pipeline further
  below).
- `apps.roasts.reconcile_stuck_roast_runs` / `apps.extraction.reconcile_stuck_extraction_tasks`
  — Beat-scheduled sweeps (every 5 minutes by default, `CELERY_BEAT_SCHEDULE`) that fail any
  `RoastRun`/`ExtractionTask` stuck `queued`/`processing` past a generous staleness threshold
  (`ROAST_STUCK_THRESHOLD_MINUTES`/`EXTRACTION_STUCK_THRESHOLD_MINUTES`, default 15 min each).
  This exists because `CELERY_TASK_ACKS_LATE=True` (see below) makes task delivery genuinely
  at-least-once, but the claim-and-process pattern both tasks use is deliberately *not*
  designed to self-recover from a task that dies *after* claiming its row — see the comment
  above `CELERY_TASK_ACKS_LATE` in `config/settings/base.py` for the full reasoning. Without a
  running `beat` process, a crashed worker can leave a row stuck `processing` forever with
  nothing to clean it up — **`beat` is not optional in production**.

Production reliability settings (`config/settings/base.py`): `CELERY_TASK_ACKS_LATE=True` +
`CELERY_TASK_REJECT_ON_WORKER_LOST=True` + `CELERY_WORKER_PREFETCH_MULTIPLIER=1` make message
delivery actually at-least-once (the default isn't — a worker killed mid-task loses the
message entirely without these). Both processing tasks now also have `soft_time_limit`/
`time_limit` (`ROAST_TASK_*_TIME_LIMIT_SECONDS`, `EXTRACTION_TASK_*_TIME_LIMIT_SECONDS`).

## Document extraction pipeline

### Flow

```
POST /api/v1/submissions/ (any submission_type: resume/website/github)
  -> apps.submissions.services.create_submission validates type-specific input (file size/
     content-type for resumes; presence + shape for source_url otherwise), persists the
     Submission (+ SubmissionAsset for resumes), and — in the SAME transaction — queues an
     ExtractionTask(status=queued)
  -> dispatches extract_submission_task.apply_async() after the transaction commits
     (transaction.on_commit); if the broker is unreachable, the task+submission are marked
     failed immediately rather than left stuck `processing` forever

Celery: apps.extraction.tasks.extract_submission_task(extraction_task_id)
  -> atomically claims the task: UPDATE ... WHERE status='queued' -> 'processing'
     (0 rows affected = already claimed/deleted -> safe no-op; same idempotency trick as
     apps.roasts.tasks.process_roast_run, needed because Celery delivers at-least-once)
  -> bounded by EXTRACTION_TASK_SOFT_TIME_LIMIT_SECONDS/EXTRACTION_TASK_TIME_LIMIT_SECONDS —
     a pathological file or slow remote server can't hang a worker indefinitely
  -> delegates to apps.extraction.services.process_extraction(extraction_task):
       1. defense-in-depth re-check of asset.size_bytes against MAX_UPLOAD_SIZE_BYTES for
          resumes (the primary gate already ran at upload time; a no-op for website/GitHub)
       2. resolve the processor: apps.extraction.processors.get_processor(submission) —
          keyed by submission_type (ResumeProcessor/WebsiteProcessor/GitHubProcessor);
          unsupported types/content-types raise UnsupportedContentTypeError
       3. process: the resolved processor returns a ProcessingResult(text, metadata) or
          raises an ExtractionError subclass — CorruptedDocumentError/EmptyDocumentError
          (resume), InvalidSourceURLError/RemoteFetchError/EmptyDocumentError (website/
          GitHub) — see each processor's section below
       4. validate: a uniform non-empty check on whatever the processor returned, ahead of
          storing it — the single choke point every current/future processor's output
          passes through
       5. store: Submission.extracted_text + Submission.metadata + status=ready (+
          ExtractionTask=completed), saved atomically together — or, on any
          ExtractionError, both rows atomically marked failed with Submission.error_message
          set to a clear (never sensitive) message
  -> a SoftTimeLimitExceeded or any truly unexpected exception is caught as a last-resort
     net (mirrors apps.roasts.tasks.process_roast_run) and recorded as a failure the same way

GET /api/v1/submissions/{id}/status/  -- lightweight poll: id/status/error_message/timestamps
GET /api/v1/submissions/{id}/         -- full detail: + extracted_text/metadata/assets
```

Processing runs exactly once per submission, right after creation — not lazily, and never
re-run for subsequent roasts. Every `apps.roasts.services.create_roast_run` call (however
many times a submission is roasted) reads the same cached `Submission.extracted_text`.

### Processor abstraction

```
SubmissionProcessor (apps.extraction.processors.base)
├── ResumeProcessor    file-based: pulls a SubmissionAsset, parses it (PDF only today)
├── WebsiteProcessor   URL-based: SSRF-guarded fetch of submission.source_url -> visible text
└── GitHubProcessor    URL-based: GitHub REST API lookup, no arbitrary URL fetch at all
```

`SubmissionProcessor.process(self, submission) -> ProcessingResult` takes the whole
submission rather than a file object or URL string, so the interface covers file-based and
URL-based sources equally — adding a fourth source type later never requires changing it.
`ProcessingResult` is `(text, metadata)`: `text` becomes `Submission.extracted_text`;
`metadata` (optional, e.g. a GitHub repo's stars/language/topics) becomes
`Submission.metadata`. `apps.extraction.processors.registry.get_processor()` is a
settings-free factory mirroring `apps.common.storage.get_storage()`/
`apps.ai.providers.get_ai_provider()`, keyed by `submission_type`.

**`WebsiteProcessor`** (`apps/extraction/processors/website.py`): validates
`submission.source_url` against `apps.extraction.http.is_safe_public_url()` — scheme
restricted to `http`/`https`, every IP the hostname resolves to checked against
private/loopback/link-local/reserved/multicast ranges (blocks e.g. `http://169.254.169.254/`,
`http://localhost/`) — before ever making a request; this is the SSRF prevention this phase
requires. Fetches through `apps.extraction.http.fetch_url()` (timeout-bounded, capped at
`EXTRACTION_HTTP_MAX_RESPONSE_BYTES`), strips `<script>`/`<style>` and collapses the rest to
visible text, then normalizes/caps it (`apps.extraction.text_utils.normalize_text()`,
`EXTRACTION_MAX_TEXT_CHARS`) before storing. Assumes the fetched resource is HTML/text and
does not execute JavaScript — a JS-rendered page will likely yield little or no text.

**`GitHubProcessor`** (`apps/extraction/processors/github.py`): parses `owner`(`/repo`) out
of `submission.source_url` (must be a `github.com` URL; each path segment is checked against
GitHub's username/repo character set before being interpolated into a request URL — defense
against path/URL injection). For a repository URL, calls the GitHub REST API for repo
metadata (description, language, stars, forks, topics) plus its README (the *only* extra
file ever fetched — no tree walk, no tarball/zip download); for a bare profile URL, calls
the user-profile endpoint (name, bio, company, location, public repo/follower counts).
Requests always target `EXTRACTION_GITHUB_API_BASE_URL` (a fixed, hardcoded host, default
`https://api.github.com`) — never a host derived from `submission.source_url` — so unlike
`WebsiteProcessor`, these calls don't go through `is_safe_public_url()`: there's no way for
user input to redirect them elsewhere, the same trust level already given to
`OpenAIProvider`'s fixed API host. **No GitHub OAuth in this phase**: `GitHubProcessor`
accepts an optional `access_token` (used only for the `Authorization` header); the registry
passes `settings.EXTRACTION_GITHUB_ACCESS_TOKEN` (empty by default = anonymous calls). A
future per-user OAuth flow plugs in at exactly that one constructor argument — no other
interface change.

**`ResumeProcessor`** (`apps/extraction/processors/resume.py`): unchanged from its original
design — a `{content_type: parser_fn}` dict, `application/pdf` the only entry today. Adding
DOCX/image support later is one new parser function + one new dict entry.

**Stubbed** (raise `UnsupportedContentTypeError` — a clean, clearly-labeled failure, not a
crash): DOCX and image resumes.

### Status/error tracking

Two layers, deliberately: `ExtractionTask` (in `apps/extraction`) is the per-attempt audit
row — `status`, `processor_name`, `char_count`, `started_at`/`completed_at`, `error_message`
— an internal record of what was attempted. `Submission.status`/`Submission.error_message`
(in `apps/submissions`) are the aggregate outcome API consumers actually read: `processing`
while extraction runs, `ready` once `extracted_text` is populated, `failed` with a clear
`error_message` otherwise. **No submission type can be roasted until it reaches `ready`**
(`apps.roasts.services._validate_submission_is_roastable`) — a processing failure (corrupt
PDF, SSRF-blocked/unreachable URL, GitHub 404/rate-limited) fails the submission the same way
for every type; there is no "best-effort, roast it anyway" fallback for website/GitHub
anymore.

### Supported source types and limitations

- **Resume**: PDF only. Legacy `.doc` and `.docx` files are accepted at upload time (they
  match the allowed extension/MIME allowlist) but fail extraction with a clear "not yet
  supported" error — no DOCX/legacy-`.doc`/image parser exists yet.
- **Website**: any public `http`/`https` URL that passes the SSRF guard. Content is assumed
  to be HTML/text; JavaScript is not executed, so JS-rendered pages may yield little/no text.
  Non-HTML responses (a PDF, an image) aren't specially handled and will likely produce an
  `EmptyDocumentError`. Fetches are capped at `EXTRACTION_HTTP_MAX_RESPONSE_BYTES` and
  `EXTRACTION_HTTP_TIMEOUT_SECONDS`.
- **GitHub**: public repositories and public user profiles only — no private repos/profiles
  without a future OAuth token. Unauthenticated API calls are subject to GitHub's ~60
  requests/hour/IP rate limit; exceeding it fails the submission clearly (HTTP 403) rather
  than hanging or silently degrading. Only repository metadata + README are fetched — never
  source files, commit history, or a full repo download.

### Requirements checklist

| Requirement | Implementation |
|---|---|
| Maximum file size | `validate_file_size` at upload time (`MAX_UPLOAD_SIZE_BYTES`); re-checked defensively in `process_extraction` before materializing the temp file |
| Supported MIME types | Upload-time allowlist (`ALLOWED_RESUME_CONTENT_TYPES`/`ALLOWED_RESUME_EXTENSIONS`, sniffed via libmagic, not trusted from the client) **and** the processor registry, which only actually parses `application/pdf` resumes today |
| Empty-document detection | `ResumeProcessor`/`WebsiteProcessor`/`GitHubProcessor` each check their own output is non-empty (`EmptyDocumentError`); `process_extraction`'s validate step re-checks uniformly for every processor |
| Corrupted PDF handling | `pypdf` exceptions caught and wrapped as `CorruptedDocumentError` — no raw traceback or file content ever stored/logged |
| Timeout protection | Celery `soft_time_limit`/`time_limit` on `extract_submission_task`; `EXTRACTION_HTTP_TIMEOUT_SECONDS` bounds each individual outbound HTTP call within it |
| Safe temporary file handling | `materialize_asset_to_tempfile` — `tempfile.NamedTemporaryFile` (private 0600 perms), chunked streaming, always cleaned up via context manager even on exception |
| SSRF prevention / protocol restriction / private IP ranges | `apps.extraction.http.is_safe_public_url()` — scheme allowlist (http/https only) + every resolved IP checked against private/loopback/link-local/reserved/multicast; not airtight against DNS rebinding (practical guard, not bulletproof) |
| Response size limit | `apps.extraction.http.fetch_url()` truncates at `EXTRACTION_HTTP_MAX_RESPONSE_BYTES`; stored text further capped at `EXTRACTION_MAX_TEXT_CHARS` |
| No arbitrary server-side requests | `WebsiteProcessor` only ever fetches `submission.source_url` itself (post-SSRF-check); `GitHubProcessor` only ever calls a fixed, hardcoded API host, never a user-influenced one |
| No sensitive content in logs | Every `logger.*` call in `apps.extraction` logs only submission/task IDs, status, and exception class — never `extracted_text`, file/response bytes, URLs, or filenames-with-content |

## AI roasting pipeline

### Flow

```
POST /api/v1/submissions/{submission_id}/roasts/
  -> validates: submission exists & is owned by the caller (404 otherwise),
     submission.status isn't deleted/failed, the submission is specifically `ready`
     — extraction/processing has finished, for every submission type (see the document
     extraction pipeline above) — language/intensity are supported (ChoiceField), the
     owner is within their weekly roast quota (see below — 429 if not), and — via
     a partial unique DB constraint on (submission, language, intensity) covering
     queued/processing rows — returns the existing in-flight run instead of creating
     a duplicate (200 vs 201). Never calls an AI provider from the view.
  -> creates RoastRun(status=queued), dispatches process_roast_run.delay()
     after the DB transaction commits (transaction.on_commit)

Celery: apps.roasts.tasks.process_roast_run(roast_run_id)
  -> atomically claims the run: UPDATE ... WHERE status='queued' -> 'processing'
     (0 rows affected = already claimed/deleted -> safe no-op; this is what
     makes at-least-once task delivery idempotent)
  -> delegates to apps.ai.services.roasting.process_roast(roast_run):
       1. load submission + resolve the active PromptVersion for roast_run.language
          (fails clearly if none configured for that language)
       2. "load submission": apps.ai.services.extraction.ensure_extracted_text() just
          reads the cached Submission.extracted_text — every submission type is fully
          processed by apps.extraction before this run could even be created, so
          apps.ai never processes anything itself (an internal-consistency guard raises
          if extracted_text is somehow still empty, which shouldn't be reachable)
       3. build prompt: render_system_prompt() (language + intensity variables) +
          render_user_prompt() (submission content, capped at AI_MAX_SOURCE_TEXT_CHARS)
       4. AI provider: get_ai_provider().generate_roast(system_prompt, user_prompt)
          — up to AI_MAX_ATTEMPTS attempts, exponential backoff between them
            (AI_RETRY_BACKOFF_BASE_SECONDS * 2**(attempt-1)), retrying on BOTH
            transient provider failures (timeout/connection error) AND
            malformed/invalid structured output — one AIRequest audit row is
            recorded per attempt, success or failure, with token/cost/latency
       5. validate structured output: RoastResponseSchema.model_validate_json()
          (strict — unknown fields rejected, severity enum-restricted, score 0-100)
       6. save sections/findings: only after full validation passes, in one
          transaction alongside marking the run completed — never a partial write
  -> on any unrecoverable failure (no active prompt, extraction error, or every
     retry attempt exhausted): RoastRun.status = failed, error_message set to a
     generic, safe message (never the raw vendor error — see below),
     zero RoastSection/RoastFinding rows exist

GET /api/v1/roasts/{id}/status/   -- lightweight poll: id/status/started_at/completed_at/error_message
GET /api/v1/roasts/{id}/          -- full detail: + summary/final_verdict/score/sections/findings
GET /api/v1/roasts/quota/         -- {limit, used, remaining, resets_at} for the caller (see below)
```

### Weekly roast quota

Every roast-*creation attempt* (not just completed ones — a failed attempt still typically
cost a real AI provider call) counts against `ROAST_WEEKLY_QUOTA` (default 3) in a rolling
`ROAST_QUOTA_WINDOW_DAYS`-day window (default 7, **not** a calendar week — avoids a
burst-at-midnight-Sunday gaming pattern). Enforced in
`apps.roasts.services.create_roast_run` by `select_for_update()`-locking the owner's `User`
row before counting — this serializes concurrent requests from *that one user* (different
users never contend with each other) so N simultaneous requests can't all read "under quota"
and all proceed. Exceeding it raises DRF's built-in `Throttled` (429, with `wait` set to
seconds until the oldest in-window roast ages out) — the same `THROTTLED` error code and
envelope as any other rate limit. `GET /api/v1/roasts/quota/` lets a client check remaining
quota ahead of time rather than only finding out via a 429.

### Email OTP (verification & password reset)

Transactional email goes through Resend exclusively — there is no SMTP/Django-email-backend
configuration anywhere, and `apps.notifications.emails.send_email` is the single place any code
is allowed to call it (see that module's docstring). Registration no longer issues login-ready
accounts: `apps.accounts.services.generate_and_send_otp` emails a 6-digit code
(`OTP_TTL_MINUTES`, default 10) and `User.email_verified` stays `False` until
`POST /api/v1/auth/verify-email/` consumes it — `apps.accounts.serializers.LoginSerializer`
rejects a correct password on an unverified account with a distinct `EMAIL_NOT_VERIFIED` error
code (see `apps.common.exception_handler`'s `api_error_code` extension point) rather than the
generic "no active account" message, so the frontend can route the user to the verification step
instead of showing a wrong-password-looking error. The same `EmailOTP` model and
`apps.accounts.services.verify_otp` power `POST /api/v1/auth/password-reset/request/` +
`/confirm/`. A code is checked against `OTP_MAX_ATTEMPTS` (default 5) and expires on its own; all
four OTP-adjacent endpoints (verify, resend, password-reset request/confirm) are throttled far
tighter than normal auth endpoints, and the resend/request endpoints always respond `200`
regardless of whether the account exists, so neither can be used to enumerate registered emails.
Accounts that existed before this feature shipped were grandfathered in as verified by a
one-time data migration (`apps/accounts/migrations/0004_...`) — only new registrations start
unverified.

### Prompt injection resistance

`extracted_text` (resume/website/GitHub content) and `submission.title` are, structurally,
untrusted user input handed to the model. `apps.ai.prompts.renderer.render_user_prompt` wraps
all of it in `<submitted_content>...</submitted_content>`, and the active `PromptVersion`'s
system prompt (v2, seeded by `apps/ai/migrations/0003_seed_prompt_versions_v2.py`) has an
explicit rule instructing the model to treat that delimited block as data to critique only,
never as instructions — and to roast an embedded manipulation attempt as a finding rather than
obey it. This mitigates, not eliminates, the risk: output is always fully schema-validated
(`RoastResponseSchema`, `extra="forbid"`) regardless, so a successful injection is bounded to
influencing roast content/tone (e.g. an inflated `score`), never to escaping the response
shape, executing anything, or reaching another user's data — there's no tool-use/retrieval
step in this pipeline the model could be tricked into invoking.

### Structured output contract

The AI must return exactly one JSON object (OpenAI's `response_format: json_object` mode
is used as a first line of defense at the API level; `RoastResponseSchema` independently
re-validates the parsed result regardless):

```json
{
  "summary": "string",
  "sections": [{"key": "string", "title": "string", "content": "string"}],
  "findings": [{"category": "string", "severity": "info|low|medium|high|critical",
                "title": "string", "roast_text": "string", "actual_feedback": "string"}],
  "final_verdict": "string",
  "score": 0-100 or null
}
```
At least one section and one finding are required; `position` is assigned server-side
from list order, never trusted from the model.

### Prompt versioning & languages

Three active `PromptVersion` rows are seeded per language (`name="roast_generation"`,
`en`/`hi`/`hinglish`), currently at `version="v2"` (`apps/ai/migrations/0003_seed_prompt_versions_v2.py`
— v1, from `0002_seed_prompt_versions.py`, is deactivated but preserved for history) — a
partial unique DB constraint enforces at most one active version per `(name, language)`.
Editing a live prompt is always a new migration creating a new active `PromptVersion` row
(deactivating the old one atomically), never mutating an existing seed migration — see the
comment in `0002_seed_prompt_versions.py`. **Intensity is a separate runtime variable**, not a
distinct PromptVersion row: `apps.ai.prompts.templates.INTENSITY_INSTRUCTIONS` maps
gentle/sarcastic/brutal/nuclear to tone/profanity instructions substituted into whichever
language's stored template is active. Every prompt's rule #1 restricts the model to roasting
the submitted *content* — resume weaknesses, website/UX choices, GitHub code/commit
quality — and explicitly forbids targeting protected personal characteristics; rule #4 is the
prompt-injection-resistance rule described above.

### Cost/token tracking

Every provider call attempt (success or failure) is recorded as one `AIRequest` row:
`provider`, `model`, `prompt_version`, `input_tokens`, `output_tokens`, `latency_ms`,
`cost` (`Decimal`, computed from `AI_OPENAI_INPUT_PRICE_PER_1K`/`AI_OPENAI_OUTPUT_PRICE_PER_1K`),
`success`, `error`. Never stores prompt text or the raw AI response body — metadata only.
`AIRequest.error` may include the raw per-attempt error detail (e.g. the OpenAI SDK's own
exception text) for debugging — this table is never exposed via any API endpoint (admin-only).
The *client-facing* `RoastRun.error_message`, by contrast, is always a generic, safe message
on failure — see `apps.ai.services.roasting._generate_with_retries`.

### Configuring the AI provider

```bash
AI_PROVIDER=stub   # default — always fails with a clear error; no key needed, safe for dev/CI
AI_PROVIDER=openai # real generation
OPENAI_API_KEY=sk-...
AI_OPENAI_MODEL=gpt-4o-mini
```

See `.env.example` for the full list (temperature, max output tokens, timeout, retry
count/backoff, pricing, source-text cap). Extraction's own HTTP timeout/size caps
(`EXTRACTION_HTTP_TIMEOUT_SECONDS` etc.) are documented in the extraction pipeline section
above.

> **Note on verification**: this environment has no outbound internet access and no
> OpenAI API key configured, so `OpenAIProvider` was verified structurally (instantiates
> correctly via the factory, calls the SDK with the right parameters) but never exercised
> against the live API. The full pipeline — retry-on-malformed-output, retry-on-timeout,
> retry exhaustion -> failed with zero partial rows, successful validation -> persisted
> sections/findings/score, per-attempt token/cost recording, language/intensity actually
> changing the rendered prompt — was verified end-to-end (including through the real
> Celery worker + Postgres, not just in isolation) using fake `AIProvider` implementations
> standing in for the vendor call.

## Running tests

```bash
pytest
```

Tests run against a real Postgres database (not sqlite) — a DB-level `CHECK` constraint
on `Submission` is only enforced by Postgres, so `config.settings.test` intentionally does
not swap the database engine. Make sure `db` (from `docker compose up -d db redis`) is
running before running the suite.

## Linting

```bash
ruff check .
black --check .
```

## Production readiness

Full detail lives in [`docs/PRODUCTION_READINESS.md`](docs/PRODUCTION_READINESS.md) (completed
security checks, remaining/accepted risks, recommended infrastructure, the full required
environment variable list, and a deployment checklist) and
[`docs/BACKUP_RECOVERY.md`](docs/BACKUP_RECOVERY.md) (backup/restore procedure). Summary of
what's new since earlier phases:

- **Throttling**: a generous global default (`UserRateThrottle`/`AnonRateThrottle`) covers
  every endpoint that doesn't set its own throttle; auth endpoints, submission creation, and
  roast creation each have their own tighter scope. See `config/settings/base.py`'s
  `DEFAULT_THROTTLE_RATES`.
- **Health checks**: `GET /api/v1/health/ready/` now checks database, Redis, *and* at least
  one live Celery worker (not just broker reachability) — see the Celery section above.
- **Data deletion**: `DELETE /api/v1/auth/me/` (password re-confirmation required)
  permanently deletes an account and everything it owns — see
  `apps.accounts.services.delete_user_account`.
- **Correlation IDs**: every response carries an `X-Request-ID` header (generated, or echoed
  back if the client supplied one), included in the error envelope and in every structured log
  line for that request — see `apps.common.middleware.RequestIDMiddleware`.
- **Production Docker**: `docker-compose.prod.yml` (gunicorn, non-root, no dev deps, a `beat`
  service) alongside the existing dev-only `docker-compose.yml`; `.dockerignore` keeps `.env`
  out of the built image.
- **Settings hardening**: `config.settings.prod` now requires `DJANGO_SECRET_KEY` (raises if
  unset, rather than silently using the dev fallback), adds `SECURE_PROXY_SSL_HEADER` for a
  TLS-terminating-proxy topology, and the API schema/Swagger/Redoc require authentication by
  default (relaxed back to public in `dev.py` only, for local convenience).

## Assumptions

- Django project package is named `config/`, not `roast_anything/` — avoids awkward
  `roast_anything.settings` imports; not otherwise significant.
- `apps/sharing`, `apps/feedback` are still scaffolded (installed, importable, empty
  `models.py`) — business logic for those lands in a later phase.
- Structured logging uses a small built-in JSON formatter
  (`apps.common.logging_formatters.JSONFormatter`) rather than a third-party logging
  package, to avoid an extra dependency for a straightforward requirement. Per policy,
  no submission file bytes, extracted document text, AI prompts, or AI outputs
  containing private user content may ever be passed to a logger call.
- `/api/v1/health/` never touches the database or Redis (pure liveness); `/api/v1/health/ready/`
  checks both and returns `503` if either is unreachable, so an orchestrator can hold
  traffic without concluding the process itself is dead.
- CORS is enabled via `django-cors-headers` with an explicit `CORS_ALLOWED_ORIGINS`
  allowlist (empty by default in production; defaults to `http://localhost:3000` in dev)
  rather than allowing all origins.
- Submissions in `deleted`/`failed` status cannot be (re-)roasted. Every submission type
  additionally requires `ready` (apps.extraction's async pipeline has actually finished) —
  this is a behavior change from an earlier version of this pipeline, where website/GitHub
  were roastable in `draft`/`processing` because no extraction step existed for them yet.
  Now that one does, a processing failure fails the submission for every type; there is no
  "best-effort, roast it anyway" fallback anymore.
- `RoastFinding.roast_text` (not `roast`) holds the zinger text — named to avoid
  colliding with the `roast` FK to `RoastRun` on the same model.
- Legacy `.doc` and `.docx` resumes are accepted at upload time (matches the allowed
  extensions) but fail extraction with a clear "not yet supported" error — only PDF is
  actually parsed today. Re-adding DOCX support is one new parser function + one new entry
  in `apps.extraction.processors.resume`'s format-parser dict.
- Website fetching and GitHub API calls both require outbound internet access from the
  worker process. `WebsiteProcessor`/`GitHubProcessor` were verified end-to-end (real Celery
  worker + Postgres, real HTTP requests) against `https://en.wikipedia.org/wiki/Python`,
  `https://github.com/octocat/Hello-World`, and `https://github.com/octocat`. If your
  environment lacks outbound access, fall back to structural verification: unit-level calls
  into the processors, plus `is_safe_public_url()` checks against known-bad targets
  (`http://169.254.169.254/`, `http://localhost/`, non-http(s) schemes).
- No GitHub OAuth exists in this phase — `GitHubProcessor` always calls the GitHub API
  anonymously unless `EXTRACTION_GITHUB_ACCESS_TOKEN` is set to one shared token. Per-user
  OAuth (needed for private repos, or to avoid the shared anonymous rate limit) is a future
  phase; the processor's `access_token` constructor argument is the extension point for it.
