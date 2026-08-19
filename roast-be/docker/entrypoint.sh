#!/usr/bin/env bash
set -e

# Runs as root so it can fix ownership of mounted volumes (e.g. a fresh
# named volume for MEDIA_ROOT, which Docker creates as root-owned — the
# app itself runs as appuser and would otherwise fail to write to it,
# see apps/common/storage/local.py's mkdir). Drops to appuser for
# everything else below.
mkdir -p /app/media
chown -R appuser:appuser /app/media

if [ "${DJANGO_AUTO_MIGRATE:-true}" = "true" ]; then
  gosu appuser python manage.py migrate --noinput
fi

exec gosu appuser "$@"
