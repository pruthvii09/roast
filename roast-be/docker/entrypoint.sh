#!/usr/bin/env bash
set -e

if [ "${DJANGO_AUTO_MIGRATE:-true}" = "true" ]; then
  python manage.py migrate --noinput
fi

exec "$@"
