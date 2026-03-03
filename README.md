# Lyndrix Core

**Lyndrix Core** is a highly modular, event-driven Internal Developer Platform (IDP) and Configuration Management Database (CMDB). It acts as a central control plane for GitOps-based infrastructure and application deployments.

Developed with **Python**, **FastAPI**, and **NiceGUI**, Lyndrix provides a modern, reactive web interface for managing complex YAML structures, server landscapes, and zero-trust secrets.

**Documentation:** [https://marvin1309.github.io/lyndrix-core/](https://marvin1309.github.io/lyndrix-core/)

---

## Core Features

- **Modular Plugin Architecture:** The system is completely divided into independent plugins that communicate with each other via a central Event Bus.
- **GitOps SSOT Synchronization:** Automatic import, parsing, and write-back (commit & push) of `service.yml` definitions from GitLab repositories.
- **Zero-Trust Security (HashiCorp Vault):** Sensitive data (GitLab PATs, Webhooks) are never stored locally in the database. Instead, they are dynamically retrieved from a HashiCorp Vault / OpenBao instance.
- **Change Management:** Integrated approval workflow. Changes to the infrastructure or applications first generate a "Change Request" before they are provisioned (or pushed to Git).
- **Hybrid Editor:** The UI offers both user-friendly forms for standard settings and a dynamic JSON/YAML tree editor for complex configurations.
- **Event-Driven Notifications:** Automatic alerts (e.g., via Discord Webhooks) for new change requests or system events.

---

## System Architecture & Plugins

The system currently consists of the following core modules:

- `lyndrix_core_ui`: Dashboard, Darkmode engine, and global system settings.
- `application_manager`: The CMDB view for linking applications with servers and firewalls.
- `server_manager`: Management of hardware, VM, and LXC nodes.
- `change_manager`: Central approval instance for all system changes.
- `secrets_manager`: The direct integration to HashiCorp Vault (Service Locator Pattern).
- `ssot_app_importer`: Connects Lyndrix with the GitLab Application-Definitions group.
- `ssot_infra_importer`: Dynamically pulls server nodes from the IaC Controller (Ansible/Terraform).
- `discord_notifier`: Sends approval requests as embeds to Discord.

---

## Installation & Setup

### Prerequisites

- Docker & Docker Compose
- GitLab (for SSOT repositories)

### 1. Development Environment (Local)

Since Lyndrix Core relies on a MariaDB database and a HashiCorp Vault instance, the recommended way to run it locally is via the provided Docker Compose setup. This ensures all dependencies are correctly configured.

```bash
# 1. Clone repository
git clone https://github.com/marvin1309/lyndrix-core.git
cd lyndrix-core

# 2. Start the Development Stack
# This starts Lyndrix (Hot-Reload), MariaDB, and Vault
docker compose -f docker/docker-compose.dev.yml up -d --build
```

The web interface will then be accessible at `http://localhost:8081`.

- **Vault UI:** `http://localhost:8200`

### 2. Production Deployment

For production environments, use the pre-built Docker image. Below is a reference `docker-compose.yml` (including Traefik labels) for a secure deployment.

```yaml
version: "3.8"

services:
  lyndrix:
    image: ghcr.io/marvin1309/lyndrix-core:latest
    container_name: lyndrix-core
    restart: unless-stopped
    ports:
      - "8081:8081"
    environment:
      - DB_USER=admin
      - DB_PASSWORD=secret
      - DB_HOST=lyndrix-db
      - DB_NAME=lyndrix_db
      - VAULT_URL=http://lyndrix-vault:8200
      - LYNDRIX_MASTER_KEY=your_secure_master_key_here
      - ENV_TYPE=prod
    volumes:
      - ./plugins:/app/plugins
      - ./secure_data:/data/security
    depends_on:
      db:
        condition: service_healthy
      vault:
        condition: service_started
    networks:
      - secured
      - stack_internal
    # Optional: Traefik Labels
    labels:
      traefik.enable: "true"
      traefik.http.routers.lyndrix.rule: "Host(`lyndrix.your-domain.com`)"
      traefik.http.routers.lyndrix.entrypoints: "websecure"
      traefik.http.routers.lyndrix.tls: "true"

  db:
    image: mariadb:10.11
    container_name: lyndrix-db
    restart: unless-stopped
    networks:
      - stack_internal
    environment:
      MARIADB_ROOT_PASSWORD: secret
      MARIADB_DATABASE: lyndrix_db
      MARIADB_USER: admin
      MARIADB_PASSWORD: secret
    volumes:
      - ./db_data:/var/lib/mysql
    healthcheck:
      test:
        [
          "CMD",
          "mariadb-admin",
          "ping",
          "-h",
          "localhost",
          "-uadmin",
          "-psecret",
        ]
      interval: 10s
      timeout: 5s
      retries: 5

  vault:
    image: hashicorp/vault:latest
    container_name: lyndrix-vault
    restart: unless-stopped
    cap_add:
      - IPC_LOCK
    environment:
      VAULT_LOCAL_CONFIG: '{"storage": {"file": {"path": "/vault/file"}}, "listener": {"tcp": {"address": "0.0.0.0:8200", "tls_disable": 1}}, "ui": true}'
      VAULT_API_ADDR: "http://lyndrix-vault:8200"
    networks:
      - secured
      - stack_internal
    volumes:
      - ./vault_data:/vault/file
    command: server

networks:
  secured:
    external: true
    name: "services-secured"
  stack_internal:
    driver: "bridge"
```

---

## Configuration (Day-2 Operations)

Plugin configuration is **no longer** done in the code, but directly through the web interface:

1. Navigate to **System -> Einstellungen (Settings)** in Lyndrix.
2. Expand the **Secrets Manager**, enter your Vault URL (`http://127.0.0.1:8200`) and credentials, and click "Save".
3. Expand the **SSOT App Manager**, enter the GitLab URL, and provide your Personal Access Token (this will be securely encrypted and stored in the Vault!).
4. The **Discord Notifier** webhook can also be securely stored in the Vault from here.

---

_Developed for scalable Homelabs and Enterprise Environments._
