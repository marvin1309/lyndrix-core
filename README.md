# 🚀 Lyndrix Core

**Ein hochsicheres, erweiterbares und Cloud-natives Application Framework.**

Lyndrix Core ist das Fundament für moderne, modulare Unternehmensanwendungen. Basierend auf einer leistungsstarken Kombination aus **FastAPI** und **NiceGUI** bietet es eine nahtlose Integration von Backend-Services und Benutzeroberflächen. Durch die tiefe Verankerung von **HashiCorp Vault** und einem dynamischen, GitHub-basierten **Plugin-System** ist Lyndrix Core darauf ausgelegt, maximale Sicherheit mit grenzenloser Skalierbarkeit zu vereinen.

---

## ✨ Enterprise-Grade Features

### 🛡️ Integrierte Sicherheit & Secrets Management (HashiCorp Vault)

Sicherheit ist nicht nur ein Add-on, sondern Kernbestandteil. Lyndrix Core verfügt über einative **HashiCorp Vault**-Integration:

- **Automatisches Setup & Unseal:** Verschlüsselte Key-Stores (`vault_keys.enc`) ermöglichen Zero-Touch-Restarts mit Auto-Unseal über den `LYNDRIX_MASTER_KEY`.
- **Isolierte Secret Engines:** Automatische Provisionierung eines eigenen KV v2 Secret-Stores (`lyndrix/`).
- **State-of-the-Art Crypto:** Passwort-Hashing via Argon2 (`argon2-cffi`) und In-Transit-Verschlüsselung mit PyCryptodome.

### 🧩 Dynamisches Plugin-Ökosystem

Erweitere die Funktionalität im laufenden Betrieb ohne Systemausfälle:

- **Marketplace & GitHub Integration:** Lade und installiere Plugins direkt aus GitHub-Repositories als `.zip`-Archive.
- **Automatisches Dependency Management:** Isolierte Installation von Plugin-Abhängigkeiten (`pip install -r requirements.txt`) während der Laufzeit.
- **Hot-Loading:** Der interne `ModuleManager` integriert neue Komponenten nahtlos in das bestehende System.

### ⚡ Hochleistungs-Architektur

- **Event-Driven Design:** Ein globaler, asynchroner Event-Bus (`bus.subscribe` / `bus.emit`) sorgt für extrem lose Kopplung der Module (z.B. Vault-Status an Plugin-Lader).
- **Boot-Sequence & Middleware:** Ein "Türsteher" (HTTP-Middleware) blockiert API- und UI-Zugriffe sicher, bis Systemkomponenten (wie Datenbank und Vault) vollständig geladen und authentifiziert sind.
- **FastAPI & NiceGUI:** Asynchrone API-Endpunkte gepaart mit reaktiven, Python-gesteuerten Web-UIs.

---

## 🏗️ Systemarchitektur & Tech-Stack

- **Core Framework:** Python 3.10+, FastAPI, Uvicorn, NiceGUI
- **Datenbank:** MariaDB / MySQL (via SQLAlchemy 2.0 & PyMySQL)
- **Sicherheit:** HashiCorp Vault (hvac), Argon2
- **Infrastruktur:** Docker & Docker Compose (Production-Ready)

---

## 🚀 Quickstart (Production via Docker)

Das System ist vollständig containerisiert und für den sofortigen Einsatz via Docker Compose vorbereitet.

### 1. Repository klonen

```bash
git clone https://github.com/dein-user/lyndrix-core.git
cd lyndrix-core

```

### 2. Umgebungsvariablen konfigurieren

Erstelle eine `.env.prod` Datei im Root-Verzeichnis (siehe `docker-compose.prod.yml`). Diese Variablen steuern auch das Setup von MariaDB:

```env
# App Config
APP_NAME=Lyndrix Core
APP_TITLE=LYNDRIX - PRODUCTION
ENV_TYPE=prod
LOG_LEVEL=INFO
STORAGE_SECRET=dein_sehr_sicheres_cookie_secret

# Database
DB_HOST=db
DB_NAME=lyndrix_db
DB_USER=admin
DB_PASSWORD=super_secret_db_pass
DB_ROOT_PASSWORD=super_secret_root_pass

# Security & Vault
LYNDRIX_MASTER_KEY=optionaler_auto_unseal_key
VAULT_URL=http://vault:8200

```

### 3. Container starten

Das System wird gebaut und mitsamt MariaDB und HashiCorp Vault hochgefahren:

```bash
docker-compose -f docker/docker-compose.prod.yml up -d --build

```

### 4. UI aufrufen

Sobald die Container laufen, ist die Oberfläche standardmäßig unter `http://localhost:80` (bzw. auf Port 8081 im Dev-Setup) erreichbar.
Beim allerersten Start leitet dich das System automatisch durch das **Vault Setup** (`/setup`), generiert die Master-Keys und bootet anschließend in das Dashboard.

---

## ⚙️ Modul-Übersicht

Die Architektur folgt einem strengen Domain-Driven Design innerhalb des `app/core/components/` Verzeichnisses:

- `auth/`: Authentifizierung, User-Sessions, Session-Storage und Hashing.
- `boot/`: Steuerung der Boot-Sequenz und Sperrung der Applikation während Ladevorgängen.
- `dashboard/`: Zentrale Einstiegsseite nach erfolgreichem Login.
- `database/`: SQLAlchemy-Verbindungsmanagement und ORM-Logik.
- `plugins/`: Verwaltung, Installation und Laden externer Funktionsbausteine über die GitHub-API.
- `system/`: Monitoring und Logs.
- `vault/`: Kryptographie, Unseal-Routinen und Initialisierung der Vault-Instanz.

---

## 🛡️ Wartung & Sicherheitshinweise

- **Vault Keys:** Das File `vault_keys.enc` (im Docker-Volume `lyndrix_secure_data`) ist lebenswichtig. Ohne dieses File oder den `LYNDRIX_MASTER_KEY` können die verschlüsselten Daten nach einem Neustart **nicht** wiederhergestellt werden. Bitte richte regelmäßige Backups für das Volume ein.
- **Maintenance Mode:** Ein integrierter Wartungsmodus kann jederzeit getriggert werden, um Usern einen Overlay anzuzeigen (`ui.maintenance`), während Background-Prozesse ablaufen.

---

_Entwickelt für Stabilität, Erweiterbarkeit und kompromisslose Sicherheit._
