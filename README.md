# Lyndrix Core

**A secure, extensible, and cloud-native application framework for modern enterprises.**

Lyndrix Core is the foundation for building modular, enterprise-grade applications. Built on a powerful combination of **FastAPI** and **NiceGUI**, it provides seamless integration of backend services and dynamic web interfaces. Deep integration with **HashiCorp Vault** and a flexible GitHub-based plugin system enable maximum security with unlimited scalability.

---

## ✨ Enterprise-Grade Features

### 🛡️ Integrated Security & Secrets Management

Security is not an afterthought—it's at the core. Lyndrix features native HashiCorp Vault integration:

- **Automated Initialization & Auto-Unseal**: Encrypted key stores (`vault_keys.enc`) enable zero-touch restarts with automatic unseal via `LYNDRIX_MASTER_KEY`
- **Isolated Secret Engines**: Automatic provisioning of dedicated KV v2 secret storage (`lyndrix/`)
- **State-of-the-Art Cryptography**: Password hashing with Argon2 and in-transit encryption with PyCryptodome

### 🧩 Dynamic Plugin Ecosystem

Extend functionality at runtime without system downtime:

- **GitHub Integration**: Install plugins directly from GitHub repositories as `.zip` archives
- **Dependency Management**: Isolated, runtime dependency installation prevents dependency hell
- **Hot-Loading**: The internal `ModuleManager` seamlessly integrates new components
- **UI Integration Hooks**: 
  - `render_settings_ui()` for configuration modals
  - `render_dashboard_widget()` for dashboard status cards
- **Module Sandbox**: Each plugin receives an isolated `ModuleContext` for secure access to events and vault secrets

### ⚡ High-Performance Architecture

- **Event-Driven Design**: Global, asynchronous event bus (`bus.subscribe` / `bus.emit`) decouples modules for maximum stability
- **Boot Sequence Protection**: HTTP middleware blocks requests until core systems (database, vault, auth) are fully initialized
- **Async I/O**: FastAPI and NiceGUI for responsive, real-time user interfaces

---

## 📋 Quick Start: 5-Minute Setup

### Prerequisites

- Docker v24.0+
- Docker Compose v2.20+
- 2GB+ RAM

### Development Setup

```bash
# 1. Clone repository
git clone https://github.com/marvin1309/lyndrix-core.git
cd lyndrix-core

# 2. Initialize environment
cp docker/.env.dev docker/.env

# 3. Start containers (includes hot-reload)
docker compose -f docker/docker-compose.dev.yml up -d --build

# 4. Access at http://localhost:8081
# Default credentials: admin / lyndrix
```

The `.dev` directory automatically stores persistent state:
- Database (MariaDB)
- Vault encryption keys
- User data and sessions
- Plugin configurations

Your Git repository remains clean—all state is in `.dev/` which is in `.gitignore`.

### Production Deployment

See [Installation & Deployment](docs/deployment.md) for comprehensive production setup guides including Docker, Kubernetes, reverse proxy configuration, and security hardening.

### Release And Image Tags

Lyndrix uses the common maintainer pattern of one rolling development tag and one rolling stable tag:

- `ghcr.io/<owner>/lyndrix-core:edge` tracks the latest successful build from `main`
- `ghcr.io/<owner>/lyndrix-core:latest` tracks the newest stable release tag
- `ghcr.io/<owner>/lyndrix-core:<major>.<minor>.<patch>` is immutable for each release
- `ghcr.io/<owner>/lyndrix-core:<major>.<minor>` is a rolling convenience tag for the current patch line
- `ghcr.io/<owner>/lyndrix-core:sha-<commit>` gives you an exact build reference

Recommended release flow:

```bash
# 1. Finish work and merge to main
git checkout main
git pull --ff-only

# 2. Create a stable release tag
git tag -a v0.3.0 -m "Lyndrix Core v0.3.0"
git push origin main
git push origin v0.3.0
```

What the workflow does after that:

- every push to `main` updates `edge`
- every stable tag like `v0.3.0` publishes `0.3.0`, `0.3`, `sha-...`, and updates `latest`
- prerelease tags like `v0.4.0-rc.1` publish prerelease image tags but do not move `latest`

Practical rules:

- use `main` as the integration branch
- cut stable releases only with `vX.Y.Z`
- use `vX.Y.Z-rc.1`, `vX.Y.Z-beta.1`, or similar for prereleases
- never move `latest` by hand; let the release tag do it

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────┐
│    Application Layer (FastAPI + NiceGUI)    │
│    Dashboard • Settings • Auth • Plugins    │
├─────────────────────────────────────────────┤
│         Core Services Layer                 │
│  Event Bus • Plugin Manager • Monitoring    │
├─────────────────────────────────────────────┤
│    Persistence & Security Layer             │
│      MariaDB • HashiCorp Vault              │
└─────────────────────────────────────────────┘
```

### Core Components

| Module | Purpose |
|--------|---------|
| `auth/` | User authentication, session management, password hashing (Argon2) |
| `boot/` | Boot sequence orchestration and system lock |
| `dashboard/` | Main entry point for authenticated users |
| `database/` | SQLAlchemy ORM and database connection management |
| `plugins/` | Plugin discovery, installation, and lifecycle management |
| `vault/` | Vault integration, encryption, key management |
| `system/` | Monitoring, logging, and health checks |

---

## 📦 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| **Runtime** | Python | 3.10+ |
| **Framework** | FastAPI | 0.129.0 |
| **UI** | NiceGUI | 3.9.0 |
| **Server** | Uvicorn | 0.41.0 |
| **Database** | MariaDB (SQLAlchemy 2.0) | 2.0.46 |
| **Secrets** | HashiCorp Vault | 2.1.0+ |
| **Auth** | Argon2 + LDAP | 23.1.0 / 2.9.1 |
| **Container** | Docker | 24.0+ |

---

## 🔌 Plugin Integration

Plugins are first-class citizens in Lyndrix Core. Here's what they can do:

### Dashboard Widgets

Display status cards or metrics on the main dashboard:

```python
def render_dashboard_widget(ctx):
    """Renders a widget on the system dashboard."""
    from ui.theme import UIStyles
    
    with ui.card().classes(f'{UIStyles.CARD_GLASS} p-4'):
        ui.label('My Plugin Status').classes('font-bold')
        ui.label('Everything operational').classes('text-green-500')
```

### Settings Configuration

Plugins can expose configuration UI:

```python
def render_settings_ui(ctx):
    """Renders plugin settings modal."""
    with ui.column().classes('gap-4'):
        enable = ui.checkbox('Enable Feature')
        ui.button('Save', on_click=lambda: ui.notify('Saved'))
```

### Event Subscriptions

React to system events:

```python
@ctx.subscribe('vault:ready_for_data')
async def on_vault_ready(payload):
    ctx.log.info("Vault ready, loading plugin data")
```

### Secure Storage

Access plugin-specific Vault secrets:

```python
# Write secrets
ctx.vault.kv_v2_write(
    path="my_plugin/api_keys",
    data={"key": "value"}
)

# Read secrets
secret = ctx.vault.kv_v2_read(path="my_plugin/api_keys")
```

For complete plugin development, see [Plugin Development Guide](docs/plugins.md).

---

## 🚀 Available Plugins

The following plugins are included in the core distribution:

- **IaC Orchestrator**: GitOps controller for Terraform and Ansible pipelines
- **Discord Notifier**: Send notifications to Discord channels
- **Git Manager**: Repository cloning and management
- **Meeting Bingo**: Team collaboration tool with real-time updates
- **AAC SSOT Manager**: Application architecture and single source of truth

Install additional plugins via the plugin marketplace in the web UI.

---

## 🛡️ Security Best Practices

### Vault Key Management

The `vault_keys.enc` file (stored in persistent volumes) is **critical**:
- Contains encrypted Vault master keys
- Without this file or `LYNDRIX_MASTER_KEY`, data cannot be recovered after restart
- Implement **regular, offsite backups** of this file
- Use hardware security modules (HSM) for production

### Secrets Management

- Never store secrets in environment variables (except `LYNDRIX_MASTER_KEY`)
- All sensitive data goes to HashiCorp Vault
- Each plugin gets isolated Vault namespaces
- Implement audit logging for sensitive operations

### Network Security

- Use HTTPS/TLS in production (see reverse proxy configuration in deployment guide)
- Restrict Vault UI access to administrative networks
- Implement network policies and firewall rules
- Use VPN for remote access to admin interfaces

---

## 📚 Documentation

- **[Installation & Deployment](docs/deployment.md)** — Setup for dev and production
- **[Plugin Development Guide](docs/plugins.md)** — Building custom plugins
- **[Security & Vault](docs/security.md)** — Security architecture and best practices
- **[System Architecture](docs/architecture.md)** — Event bus, plugin system, core design

---

## 🔧 Common Development Tasks

### Hot Reload

Code changes in `app/` are automatically reflected in development:

```bash
# Edit a file
nano app/main.py

# Save and refresh browser—changes appear within 1 second
```

### View Logs

```bash
docker compose -f docker/docker-compose.dev.yml logs -f app
```

### Reset Development State

```bash
docker compose -f docker/docker-compose.dev.yml down
rm -rf .dev/
docker compose -f docker/docker-compose.dev.yml up -d --build
```

### Create a Plugin

```bash
mkdir -p app/plugins/my_plugin
touch app/plugins/my_plugin/entrypoint.py
```

See the [Plugin Development Guide](docs/plugins.md) for structure and examples.

---

## 🐛 Troubleshooting

**Port 8081 already in use**
```bash
# Change port in docker-compose.dev.yml or use:
docker compose -f docker/docker-compose.dev.yml down
```

**Vault sealed after restart**
```bash
# Unseal using LYNDRIX_MASTER_KEY from docker/.env
# Or navigate to http://localhost:8081/unseal
```

**Database won't initialize**
```bash
# MariaDB needs ~30 seconds to start
docker compose logs lyndrix-db-dev
# Wait and retry
```

**Plugin not loading**
```bash
# Check logs for detailed error
docker compose logs app | grep -A 5 "plugin"

# Verify plugin structure and manifest
ls app/plugins/your_plugin/entrypoint.py
```

---

## ⚙️ Configuration

Key environment variables (see `docker/.env.dev` and `docker/.env.prod`):

```env
# System
ENV_TYPE=dev|prod
LOG_LEVEL=DEBUG|INFO|WARNING|ERROR

# Database
DB_HOST=localhost
DB_NAME=lyndrix_db
DB_USER=admin
DB_PASSWORD=secret

# Vault
VAULT_URL=http://vault:8200
LYNDRIX_MASTER_KEY=your_master_key_here (dev only)

# Storage
STORAGE_SECRET=secure_random_string_here
```

---

## 📈 Performance & Scaling

### Database Optimization

- Connection pooling enabled by default
- Automatic index creation for common queries
- Query caching configured in MariaDB

### Container Scaling

For production, scale horizontally:

```bash
# Run multiple instances behind a load balancer
for i in {1..3}; do
    docker run -d \
      --name lyndrix-core-$i \
      -p 808$i:8081 \
      lyndrix-core:latest
done
```

### Resource Management

Recommended resource limits:

```yaml
resources:
  requests:
    memory: "256Mi"
    cpu: "250m"
  limits:
    memory: "2Gi"
    cpu: "1000m"
```

---

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License—see [LICENSE](LICENSE) for details.

---

## 🙋 Support & Community

- **Documentation**: [Full docs](docs/index.md)
- **Issues**: GitHub Issues for bug reports and feature requests
- **Discussions**: GitHub Discussions for general questions

---

**Built with integrity, security, and scalability in mind.**
