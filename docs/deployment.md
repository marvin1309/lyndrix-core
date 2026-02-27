# 🛠️ Installation & Deployment

Lyndrix Core ist für den Betrieb in Docker-Umgebungen optimiert. Wir unterscheiden strikt zwischen lokalen Entwicklungs-Umgebungen und produktiven Server-Deployments.

## Systemvoraussetzungen

- Docker Engine (v24.0+)
- Docker Compose (v2.20+)
- Mindestens 2GB RAM (für MariaDB & HashiCorp Vault)

---

## 💻 Lokale Entwicklung (Dev-Setup)

Für die Entwicklung von Plugins oder das Testen des Systems nutzt du unser Dev-Setup. Hierbei wird dein lokaler Code direkt in den Container gemountet (Hot-Reload).

1. Kopiere die Dummy-Umgebungsvariablen:

```bash
   cp docker/.env.dev docker/.env
```

2. Starte das System mit der Dev-Compose-Datei:

```bash
docker compose -f docker/docker-compose.dev.yml up -d --build
```

3. Das System ist nun unter `http://localhost:8081` erreichbar.

---

## 🚀 Produktion (Server-Deployment)

In der Produktion sind Sicherheit und Persistenz das Wichtigste. Hier wird der Code fest in das Image gebacken und Vault benötigt eine korrekte Initialisierung.

1. Erstelle eine sichere `.env` Datei aus dem Template:

```bash
cp docker/.env.prod.example docker/.env
```

2. **WICHTIG:** Bearbeite die `docker/.env` und trage sichere Passwörter sowie den `STORAGE_SECRET` ein!
3. Starte die Produktions-Container:

```bash
docker compose -f docker/docker-compose.prod.yml up -d
```

4. Beim allerersten Start musst du Lyndrix über die Web-UI aufrufen und den **Vault Master-Key** generieren. Speichere diesen Key extrem sicher ab!
