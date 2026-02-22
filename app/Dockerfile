FROM python:3.11-slim
WORKDIR /app

# System-Abhängigkeiten inkl. dos2unix gegen Windows-Format-Fehler
RUN apt-get update && apt-get install -y \
    git gcc libc-dev libmariadb-dev pkg-config curl dos2unix \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Kopiere den gesamten Inhalt des aktuellen Contexts (app Ordner)
COPY . .

# Sicherstellen, dass Verzeichnisse existieren
RUN mkdir -p /opt/lyndrix/plugins_backup /data/security /app/plugins

# Plugins sichern, falls der Ordner existiert und nicht leer ist
RUN if [ -d "plugins" ] && [ "$(ls -A plugins 2>/dev/null)" ]; then \
        cp -r plugins/. /opt/lyndrix/plugins_backup/; \
    else \
        echo "Keine Plugins zum Sichern gefunden - erstelle leeres Backup."; \
        mkdir -p /opt/lyndrix/plugins_backup; \
    fi

# Entrypoint fixen (Zeilenenden & Rechte)
RUN dos2unix entrypoint.sh && chmod +x entrypoint.sh

EXPOSE 8081

# Fail-safe Entrypoint Aufruf
ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]