# Lyndrix Core Documentation

Welcome to the official documentation for **Lyndrix Core** – a modern, secure, and highly modular Internal Developer Platform (IDP).

Lyndrix Core is designed to provide developers and administrators with a centralized hub for infrastructure management, automation, and team collaboration tools.

---

## Core Features

- **Modular Architecture**: The system grows with your needs. Seamlessly integrate custom plugins such as the IaC Orchestrator or Meeting Bingo tool.
- **Secure by Default**: Deep integration with **HashiCorp Vault**. All passwords, API keys, and sensitive plugin data are encrypted and stored securely.
- **Real-Time UI**: Powered by NiceGUI and FastAPI, dashboards synchronize in real-time via WebSockets without page reloads.
- **Event-Driven Design**: A global, asynchronous event bus decouples core systems and plugins for maximum stability and maintainability.
- **Developer Experience**: Native support for active hot-reloading and isolated local state management.

---

## Getting Started

### Quick Start: Development Setup

Set up a local development environment in seconds with our Docker-based setup.

#### Prerequisites

- Docker Engine (v24.0+)
- Docker Compose (v2.20+)
- 2GB+ RAM available

#### Step 1: Clone the Repository

```bash
git clone https://github.com/marvin1309/lyndrix-core.git
cd lyndrix-core
```

#### Step 2: Initialize Development Environment

The development setup uses an isolated `.dev` directory to keep your repository clean while maintaining persistent state:

```bash
cp docker/.env.dev docker/.env
docker compose -f docker/docker-compose.dev.yml up -d --build
```

The `.dev` folder automatically stores:
- Database files (MariaDB)
- Vault encryption keys
- Plugin state and configurations
- User session data

This approach ensures your Git repository remains clean while preserving system state between `docker compose down` and `docker compose up` operations.

#### Step 3: Access the Application

Once initialization completes (typically 30-60 seconds), open your browser and navigate to:

```
http://localhost:8081
```

You will be guided through the initial setup:
1. Vault Master Key generation
2. Database initialization
3. User authentication setup

---

## Documentation Guide

This documentation is organized into the following sections:

- **[Installation & Deployment](deployment.md)** – Setup for development and production environments
- **[Plugin Development Guide](plugins.md)** – Building and integrating custom plugins
- **[Security & Vault](security.md)** – Encryption, secrets management, and security best practices
- **[System Architecture](architecture.md)** – Event bus, plugin system, and core components

---

## Architecture Overview

```
┌─────────────────────────────────────────────────┐
│        Lyndrix Core Application Layer            │
│  (FastAPI + NiceGUI)                            │
├─────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐             │
│  │   Dashboard  │  │   Auth       │             │
│  └──────────────┘  └──────────────┘             │
│  ┌──────────────┐  ┌──────────────┐             │
│  │   Settings   │  │   Vault UI   │             │
│  └──────────────┘  └──────────────┘             │
├─────────────────────────────────────────────────┤
│        Core Services Layer                       │
│  ┌──────────────────────────────────────────┐   │
│  │     Event Bus (Pub/Sub)                  │   │
│  └──────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────┐   │
│  │  Plugin Manager | Boot Service | Monitor│   │
│  └──────────────────────────────────────────┘   │
├─────────────────────────────────────────────────┤
│        Persistence & Security Layer              │
│  ┌──────────────┐  ┌──────────────┐             │
│  │  MariaDB     │  │ HashiCorp    │             │
│  │  (SQLAlchemy)│  │ Vault        │             │
│  └──────────────┘  └──────────────┘             │
└─────────────────────────────────────────────────┘
```

---

## System Requirements

### Minimum

- Python 3.10+
- Docker Engine 24.0+
- Docker Compose 2.20+
- 2GB RAM
- 10GB disk space

### Recommended for Production

- Python 3.11+
- Docker Engine 24.0+
- Docker Compose 2.20+
- 8GB+ RAM
- 50GB+ disk space (for plugins and data)
- Dedicated storage (NFS/EFS) for persistent volumes

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | FastAPI + NiceGUI | 3.8.0 / 0.129.0 |
| Database | MariaDB (SQLAlchemy) | 2.0.46 |
| Secrets Management | HashiCorp Vault | 2.1.0+ |
| Authentication | Argon2 + LDAP3 | 23.1.0 / 2.9.1 |
| Containerization | Docker | 24.0+ |
| Async Runtime | Uvicorn | 0.41.0 |

---

## Next Steps

- **New User?** Start with the [Getting Started](#getting-started) guide above
- **Deploy to Production?** See [Installation & Deployment](deployment.md)
- **Build Plugins?** Read the [Plugin Development Guide](plugins.md)
- **Questions about Security?** Check [Security & Vault](security.md)
