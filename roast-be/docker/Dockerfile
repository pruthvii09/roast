FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libmagic1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 appuser
WORKDIR /app

COPY requirements/ /app/requirements/

FROM base AS dev
RUN pip install --no-cache-dir -r requirements/dev.txt -r requirements/test.txt
COPY . /app
RUN chown -R appuser:appuser /app
USER appuser
ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

FROM base AS prod
RUN pip install --no-cache-dir -r requirements/base.txt
COPY . /app
RUN chown -R appuser:appuser /app
USER appuser
ENTRYPOINT ["docker/entrypoint.sh"]
# --workers: a starting point, not a universal answer — tune to actual
#   CPU count in real deployments (docker-compose.prod.yml/orchestrator
#   command override), the usual guidance is ~(2 x cores) + 1.
# --timeout: kill and restart a worker stuck handling one request this
#   long — bounds a hung request instead of it blocking that worker slot
#   forever (this app's own I/O — DB, storage, dispatching Celery tasks —
#   is already independently timeout-bounded; this is the outer backstop).
# --max-requests(-jitter): recycle each worker after roughly this many
#   requests (jittered, so all workers don't recycle simultaneously) —
#   bounds any slow memory growth over a long-running process.
# --access-logfile/--error-logfile -: log to stdout/stderr so container
#   log collection (docker/k8s) captures them, rather than into the
#   container's filesystem where they'd be lost on restart.
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", \
     "--workers", "3", "--timeout", "60", \
     "--max-requests", "1000", "--max-requests-jitter", "100", \
     "--access-logfile", "-", "--error-logfile", "-"]
