#!/usr/bin/env bash
set -euo pipefail

# CodeSentinel SQLite Database Backup & Restore Tool
# Uses SQLite Online Backup API (safe with WAL mode)

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DB_SOURCE="${DATABASE_PATH:-$HOME/codesentinel-ai/codesentinel.db}"
BACKUP_DIR="${PROJECT_ROOT}/backups"

do_backup_api() {
    local src="$1"
    local dst="$2"

    if command -v sqlite3 >/dev/null 2>&1; then
        sqlite3 "$src" ".backup '$dst'"
    else
        python3 -c "
import sqlite3, sys
src_path = sys.argv[1]
dst_path = sys.argv[2]
src_conn = sqlite3.connect(src_path)
dst_conn = sqlite3.connect(dst_path)
src_conn.backup(dst_conn)
dst_conn.close()
src_conn.close()
" "$src" "$dst"
    fi
}

check_integrity() {
    local target="$1"
    local res
    if command -v sqlite3 >/dev/null 2>&1; then
        res=$(sqlite3 "$target" "PRAGMA integrity_check;")
    else
        res=$(python3 -c "
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()
result = cur.execute('PRAGMA integrity_check;').fetchone()[0]
conn.close()
print(result)
" "$target")
    fi

    if [ "$res" != "ok" ]; then
        echo "Integrity check failed for $target: $res"
        return 1
    fi
    return 0
}

count_rows() {
    local target="$1"
    python3 -c "
import sqlite3, sys
conn = sqlite3.connect(sys.argv[1])
cur = conn.cursor()
tables = [row[0] for row in cur.execute(\"SELECT name FROM sqlite_master WHERE type='table';\").fetchall()]
total = 0
for t in tables:
    count = cur.execute(f'SELECT count(*) FROM {t}').fetchone()[0]
    total += count
conn.close()
print(total)
" "$target"
}

case "${1:-backup}" in
    backup)
        if [ ! -f "$DB_SOURCE" ]; then
            echo "Error: Source database not found at $DB_SOURCE" >&2
            exit 1
        fi
        mkdir -p "$BACKUP_DIR"
        TIMESTAMP=$(date +%Y%m%d_%H%M%S)
        TARGET_FILE="$BACKUP_DIR/codesentinel_${TIMESTAMP}.db"
        LATEST_FILE="$BACKUP_DIR/codesentinel_latest.db"

        echo "==> Backing up database using SQLite .backup API..."
        echo "    Source: $DB_SOURCE"
        echo "    Target: $TARGET_FILE"
        do_backup_api "$DB_SOURCE" "$TARGET_FILE"

        echo "==> Verifying backup integrity..."
        check_integrity "$TARGET_FILE"
        cp -f "$TARGET_FILE" "$LATEST_FILE"
        echo "==> Backup successful and verified: $TARGET_FILE"
        ;;

    restore)
        BACKUP_SRC="${2:-$BACKUP_DIR/codesentinel_latest.db}"
        TARGET_DEST="${3:-$DB_SOURCE}"

        if [ ! -f "$BACKUP_SRC" ]; then
            echo "Error: Backup file not found at $BACKUP_SRC" >&2
            exit 1
        fi

        echo "==> Restoring database from backup..."
        echo "    Backup: $BACKUP_SRC"
        echo "    Target: $TARGET_DEST"

        check_integrity "$BACKUP_SRC"
        do_backup_api "$BACKUP_SRC" "$TARGET_DEST"
        check_integrity "$TARGET_DEST"
        echo "==> Restore completed successfully and verified: $TARGET_DEST"
        ;;

    --test-restore|test-restore)
        echo "==> Running end-to-end backup and test restore verification..."
        if [ ! -f "$DB_SOURCE" ]; then
            echo "Initializing database for test..."
            python3 -c "from codesentinel.api.database import init_db; init_db()"
        fi

        TEMP_BACKUP=$(mktemp /tmp/cs_backup_test_XXXXXX.db)
        TEMP_RESTORE=$(mktemp /tmp/cs_restore_test_XXXXXX.db)
        trap "rm -f $TEMP_BACKUP $TEMP_RESTORE" EXIT

        echo "1. Performing online .backup to $TEMP_BACKUP..."
        do_backup_api "$DB_SOURCE" "$TEMP_BACKUP"

        echo "2. Validating backup file integrity..."
        check_integrity "$TEMP_BACKUP"

        echo "3. Performing test restore to $TEMP_RESTORE..."
        do_backup_api "$TEMP_BACKUP" "$TEMP_RESTORE"

        echo "4. Validating restored database integrity..."
        check_integrity "$TEMP_RESTORE"

        SRC_ROWS=$(count_rows "$DB_SOURCE")
        RESTORED_ROWS=$(count_rows "$TEMP_RESTORE")
        echo "5. Comparing row counts across tables: Source=$SRC_ROWS, Restored=$RESTORED_ROWS"

        if [ "$SRC_ROWS" -ne "$RESTORED_ROWS" ]; then
            echo "Error: Row count mismatch between source and restored database!" >&2
            exit 1
        fi

        echo "==> Test restore verification PASSED! WAL mode safe backup confirmed."
        ;;

    *)
        echo "Usage: $0 [backup | restore <file> [<dest>] | --test-restore]"
        exit 1
        ;;
esac
