FROM python:3.11-slim
WORKDIR /app

RUN apt-get update && apt-get install -y \
    git gcc libc-dev libmariadb-dev pkg-config curl dos2unix \
    && rm -rf /var/lib/apt/lists/*

# Nutzt den Pfad vom Root aus!
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ .

RUN mkdir -p /opt/lyndrix/plugins_backup /data/security /app/plugins

RUN if [ -d "plugins" ] && [ "$(ls -A plugins 2>/dev/null)" ]; then \
        cp -r plugins/. /opt/lyndrix/plugins_backup/; \
    else \
        echo "Keine Plugins zum Sichern gefunden."; \
        mkdir -p /opt/lyndrix/plugins_backup; \
    fi

COPY docker/entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8081

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]