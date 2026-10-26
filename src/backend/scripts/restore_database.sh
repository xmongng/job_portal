#!/bin/sh
# Chỉ restore vào database đích rỗng có hậu tố _restore để tránh ghi đè dữ liệu chính.
set -eu
if [ "$#" -ne 2 ]; then
    echo 'Usage: sh scripts/restore_database.sh backup.dump jobportal_restore' >&2
    exit 2
fi
case "$2" in
    *_restore) ;;
    *) echo 'Target database name must end with _restore' >&2; exit 1 ;;
esac
# Tạo database riêng; createdb thất bại nếu tên đã tồn tại, không xóa database cũ.
createdb --host="${PGHOST:-localhost}" --port="${PGPORT:-5432}" \
    --username="${PGUSER:-jobportal}" "$2"
pg_restore --exit-on-error --single-transaction --no-owner --no-acl \
    --host="${PGHOST:-localhost}" --port="${PGPORT:-5432}" \
    --username="${PGUSER:-jobportal}" --dbname="$2" "$1"
echo 'Restore complete into separate database.'
