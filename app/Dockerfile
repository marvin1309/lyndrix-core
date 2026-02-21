FROM python:3.11-slim
WORKDIR /app

# System-Abhängigkeiten (MariaDB & Git für Plugin-Support)
RUN apt-get update && apt-get install -y \
    git gcc libc-dev libmariadb-dev pkg-config curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Verzeichnisse für Daten persistenz vorbereiten
RUN mkdir -p /opt/lyndrix/plugins_backup /data/security /app/plugins /app/core/components

# Plugins sichern (falls der User später ein leeres Volume mountet)
RUN cp -r /app/plugins/. /opt/lyndrix/plugins_backup/ || echo "Keine Plugins zum Sichern"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8081
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]