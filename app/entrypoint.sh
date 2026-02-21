#!/bin/bash
set -e

# 1. Plugins wiederherstellen, falls der Mount leer ist
if [ ! "$(ls -A /app/plugins 2>/dev/null)" ]; then
    echo "[Boot] /app/plugins ist leer. Kopiere Default-Plugins aus Backup..."
    cp -r /opt/lyndrix/plugins_backup/. /app/plugins/
fi

# 2. Berechtigungen sicherstellen
mkdir -p /data/security
chmod -R 777 /app/plugins /data/security 2>/dev/null || true

echo "[Boot] Starte Lyndrix Core..."
exec "$@"