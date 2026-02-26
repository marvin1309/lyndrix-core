# 🚀 Lyndrix Core Dokumentation

Willkommen zur offiziellen Dokumentation von **Lyndrix Core** – einer modernen, sicheren und hochgradig modularen Internal Developer Platform (IDP).

Lyndrix ist darauf ausgelegt, Entwicklern und Administratoren ein zentrales Hub für Infrastruktur-Management, Automatisierung und Team-Werkzeuge zu bieten.

---

## ✨ Kern-Features

- 🧩 **Modulare Architektur:** Das System wächst mit deinen Anforderungen. Füge eigene Plugins (wie den _Docker Manager_ oder _Meeting Bingo_) nahtlos hinzu.
- 🔐 **Secure by Default:** Tiefe Integration von **HashiCorp Vault**. Alle Passwörter, API-Keys und sensiblen Plugin-Daten werden stark verschlüsselt gespeichert.
- ⚡ **Echtzeit UI:** Dank [NiceGUI](https://nicegui.io/) und FastAPI synchronisieren sich Dashboards und Dashboards in Echtzeit via WebSockets, ganz ohne lästige Page-Reloads.
- 📡 **Event-Driven:** Ein globaler, asynchroner Event-Bus entkoppelt Kernsysteme und Plugins für maximale Stabilität.

---

## 🚀 Quick Start (Entwicklungsumgebung)

Möchtest du Lyndrix Core lokal testen oder eigene Plugins entwickeln? Das geht in wenigen Sekunden dank unseres vorbereiteten Docker-Setups.

**1. Repository klonen:**

```bash
git clone [https://github.com/DEIN_USERNAME/lyndrix-core.git](https://github.com/DEIN_USERNAME/lyndrix-core.git)
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

- 🛠️ **[Installation & Deployment](https://www.google.com/search?q=./deployment.md)** (Produktion, Docker Swarm, Reverse Proxies)
- 👨‍💻 **[Plugin Development Guide](https://www.google.com/search?q=./plugins.md)** (Wie baue ich ein eigenes Lyndrix-Plugin?)
- 🔐 **[Security & Vault](https://www.google.com/search?q=./security.md)** (Wie Lyndrix deine Daten schützt)
- ⚙️ **[Architektur & API](https://www.google.com/search?q=./architecture.md)** (Deep-Dive in den Event-Bus und den Core)

---

_Gebaut mit ❤️ und Python._

```

### Was passiert, wenn du das pushst?
1. GitHub Pages (Jekyll) erkennt die `docs/index.md`.
2. Es wandelt das Markdown automatisch in eine saubere HTML-Seite um (mit dem Standard GitHub-Theme).
3. Dein Build-Fehler verschwindet und du erreichst unter deiner `.github.io` URL deine neue Startseite!

Sollen wir danach mit der **`config.py`** weitermachen, um den Code genauso sauber zu kriegen wie diese Doku?


```
