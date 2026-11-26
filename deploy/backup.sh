#!/usr/bin/env bash
# Backup harian database laporan; simpan 30 file terakhir.
set -euo pipefail
DB=${DB_PATH:-/var/lib/laporan/laporan.db}
DIR=${BACKUP_DIR:-/var/backups/laporan}
mkdir -p "$DIR"
sqlite3 "$DB" ".backup '$DIR/laporan-$(date +%F).db'"
ls -1t "$DIR"/laporan-*.db | tail -n +31 | xargs -r rm --
