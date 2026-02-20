FROM python:3.11-slim

WORKDIR /app

# System-Tools installieren
RUN apt-get update && apt-get install -y git gcc libmariadb-dev pkg-config curl && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Plugin-Volume definieren
VOLUME /app/plugins

# Angepasst auf deinen neuen Port
EXPOSE 8081

CMD ["python", "main.py"]