FROM python:3.11-slim
WORKDIR /app

# System-Abhängigkeiten (MariaDB & Git für Plugin-Support)
RUN apt-get update && apt-get install -y \
    git gcc libc-dev libmariadb-dev pkg-config curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Sicherstellen, dass die Pfade existieren (relativ zum WORKDIR /app)
RUN mkdir -p /opt/lyndrix/plugins_backup /data/security
# Kopiert alles aus dem lokalen /app/plugins in das Backup-Verzeichnis
RUN cp -r plugins/. /opt/lyndrix/plugins_backup/ || echo "Keine Plugins zum Sichern"

# entrypoint muss aus dem app ordner eine ebene höher oder wir kopieren ihn mit
RUN chmod +x entrypoint.sh
ENTRYPOINT ["./entrypoint.sh"]