#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${MADAR_BACKUP_DIR:-/home/frappe/frappe-bench/sites/hrms.localhost/private/backups}"
MAX_AGE_HOURS="${MADAR_BACKUP_MAX_AGE_HOURS:-24}"

if [[ ! -d "$BACKUP_DIR" ]]; then
  echo "CRITICAL backup_dir_missing path=$BACKUP_DIR"
  exit 2
fi

latest_file="$(
  find "$BACKUP_DIR" -maxdepth 1 -type f \
    \( -name '*.sql.gz' -o -name '*database*.gz' -o -name '*files.tar' -o -name '*private-files.tar' \) \
    -printf '%T@ %p\n' 2>/dev/null | sort -nr | head -n 1 | cut -d' ' -f2-
)"

if [[ -z "$latest_file" ]]; then
  echo "CRITICAL backup_missing path=$BACKUP_DIR"
  exit 2
fi

now_epoch="$(date +%s)"
latest_epoch="$(stat -c %Y "$latest_file" 2>/dev/null || stat -f %m "$latest_file")"
age_seconds=$((now_epoch - latest_epoch))
max_age_seconds=$((MAX_AGE_HOURS * 3600))
age_hours=$((age_seconds / 3600))
size_bytes="$(wc -c < "$latest_file" | tr -d ' ')"
file_name="$(basename "$latest_file")"

if (( age_seconds > max_age_seconds )); then
  echo "CRITICAL backup_stale latest=$file_name age_hours=$age_hours max_age_hours=$MAX_AGE_HOURS size_bytes=$size_bytes"
  exit 2
fi

echo "OK backup_fresh latest=$file_name age_hours=$age_hours max_age_hours=$MAX_AGE_HOURS size_bytes=$size_bytes"
