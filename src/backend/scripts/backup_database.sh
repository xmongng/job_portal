#!/bin/sh
# Chạy trong backend: sh scripts/backup_database.sh /absolute/private/path/jobportal.dump
# pg_dump hỏi password hoặc đọc ~/.pgpass; không đưa mật khẩu vào command/log.
set -eu
if [ "$#" -ne 1 ]; then
    echo 'Usage: sh scripts/backup_database.sh /private/path/backup.dump' >&2
    exit 2
fi
umask 077
if [ -e "$1" ]; then
    echo 'Refusing to overwrite existing backup' >&2
    exit 1
fi
pg_dump --format=custom --no-owner --no-acl --file="$1" \
    --host="${PGHOST:-localhost}" --port="${PGPORT:-5432}" \
    --username="${PGUSER:-jobportal}" --dbname="${PGDATABASE:-jobportal}"
echo 'Backup complete. Test restore into a separate empty database before relying on it.'
