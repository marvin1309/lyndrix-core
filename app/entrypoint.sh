#!/bin/bash
set -e

echo "[Boot] Lyndrix Entrypoint wird ausgeführt..."

# 1. Plugins wiederherstellen, falls das gemountete Volume leer ist
if [ ! "$(ls -A /app/plugins 2>/dev/null)" ]; then
    if [ -d "/opt/lyndrix/plugins_backup" ] && [ "$(ls -A /opt/lyndrix/plugins_backup)" ]; then
        echo "[Boot] /app/plugins ist leer. Kopiere Standard-Komponenten..."
        cp -r /opt/lyndrix/plugins_backup/. /app/plugins/
    fi
fi

# 2. Daten-Verzeichnisse vorbereiten
mkdir -p /data/security
chmod -R 777 /app/plugins /data/security 2>/dev/null || true

echo "[Boot] Starte Anwendung: $@"
exec "$@"