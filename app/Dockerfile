FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y git gcc libc-dev libmariadb-dev pkg-config curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Backup für Plugins (falls der Mount beim ersten Mal leer ist)
RUN mkdir -p /opt/lyndrix/plugins_backup /data/security
RUN cp -r /app/plugins/. /opt/lyndrix/plugins_backup/ || echo "Keine Plugins zum Sichern"

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8081
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "main.py"]