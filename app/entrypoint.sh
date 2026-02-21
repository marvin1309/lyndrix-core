#!/bin/bash
set -e

# Plugins wiederherstellen, falls Mount leer
if [ ! "$(ls -A /app/plugins 2>/dev/null)" ]; then
    echo "[Boot] /app/plugins ist leer. Kopiere Standard-Plugins..."
    cp -r /opt/lyndrix/plugins_backup/. /app/plugins/
fi

mkdir -p /data/security
chmod -R 777 /app/plugins /data/security 2>/dev/null || true

exec "$@"