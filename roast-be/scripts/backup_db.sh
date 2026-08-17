#!/usr/bin/env bash
# Plain pg_dump wrapper — a convenience for manual/cron-triggered backups,
# not a scheduler itself (that's infrastructure-specific; see
# docs/BACKUP_RECOVERY.md). Reads standard POSTGRES_* env vars (the same
# ones config/settings/base.py reads), so it works against the same
# database a running app instance is configured for without extra setup.
#
# Usage:
#   ./scripts/backup_db.sh [output_directory]
#
# Requires: pg_dump (matching or newer major version than the target
# Postgres server) and, for authentication, either PGPASSWORD in the
# environment or a ~/.pgpass entry — POSTGRES_PASSWORD is intentionally
# NOT read directly into a command-line argument, which would leak it via
# `ps`/shell history.
set -euo pipefail

OUTPUT_DIR="${1:-./backups}"
mkdir -p "$OUTPUT_DIR"

TIMESTAMP="$(date -u +%Y%m%dT%H%M%SZ)"
OUTPUT_FILE="${OUTPUT_DIR}/roast_anything_${TIMESTAMP}.dump"

export PGPASSWORD="${POSTGRES_PASSWORD:-}"

pg_dump \
  --host="${POSTGRES_HOST:-localhost}" \
  --port="${POSTGRES_PORT:-5432}" \
  --username="${POSTGRES_USER:-roast}" \
  --dbname="${POSTGRES_DB:-roast_anything}" \
  --format=custom \
  --file="$OUTPUT_FILE"

echo "Backup written to ${OUTPUT_FILE}"
echo "Restore with: pg_restore --host=<host> --port=<port> --username=<user> --dbname=<db> --clean --if-exists ${OUTPUT_FILE}"
