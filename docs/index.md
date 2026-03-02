# Lyndrix Core Dokumentation

Willkommen zur offiziellen Dokumentation von **Lyndrix Core** – einer modernen, sicheren und hochgradig modularen Internal Developer Platform (IDP).

Lyndrix ist darauf ausgelegt, Entwicklern und Administratoren ein zentrales Hub für Infrastruktur-Management, Automatisierung und Team-Werkzeuge zu bieten.

---

## Kern-Features

- **Modulare Architektur:** Das System wächst mit deinen Anforderungen. Füge eigene Plugins (wie den _Docker Manager_ oder _Meeting Bingo_) nahtlos hinzu.
- **Secure by Default:** Tiefe Integration von **HashiCorp Vault**. Alle Passwörter, API-Keys und sensiblen Plugin-Daten werden stark verschlüsselt gespeichert.
- **Echtzeit UI:** Dank NiceGUI und FastAPI synchronisieren sich Dashboards in Echtzeit via WebSockets, ganz ohne Page-Reloads.
- **Event-Driven:** Ein globaler, asynchroner Event-Bus entkoppelt Kernsysteme und Plugins für maximale Stabilität.

---

## Quick Start (Entwicklungsumgebung)

Möchtest du Lyndrix Core lokal testen oder eigene Plugins entwickeln? Das geht in wenigen Sekunden dank unseres vorbereiteten Docker-Setups.

### 1. Repository klonen

```bash
git clone https://github.com/marvin1309/lyndrix-core.git
cd lyndrix-core
```

**2. Docker Compose starten:**
Wir haben eine sichere `.env.dev` vorbereitet, damit du sofort loslegen kannst.

```bash
docker compose -f docker/docker-compose.dev.yml up -d --build
```

**3. UI aufrufen:**
Sobald die Initialisierung (Datenbank, Vault, Auth-Service) abgeschlossen ist, erreichst du das System unter:
👉 **[http://localhost:8081](https://www.google.com/search?q=http://localhost:8081)**

---

## 📚 Inhaltsverzeichnis

Hier findest du in Zukunft alle weiterführenden Anleitungen (Work in Progress):

- **Installation & Deployment** (Produktion, Docker Swarm, Reverse Proxies)
- **Plugin Development Guide** (Wie baue ich ein eigenes Lyndrix-Plugin?)
- **Security & Vault** (Wie Lyndrix deine Daten schützt)
- **Architektur & API** (Deep-Dive in den Event-Bus und den Core)

---

_Gebaut mit ❤️ und Python._
