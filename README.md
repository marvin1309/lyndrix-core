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

- Python 3.9+
- Running HashiCorp Vault / OpenBao server (for secrets management)
- GitLab (for SSOT repositories)

### 1. Clone repository & prepare environment

```bash
git clone https://<your-git-url>/lyndrix-core.git
cd lyndrix-core
python -m venv .venv

# Windows:
.venv\Scripts\activate
# Linux/macOS:
source .venv/bin/activate

```

### 2. Install dependencies

```bash
pip install -r requirements.txt

```

_(Note: Required packages include: `nicegui`, `fastapi`, `sqlalchemy`, `GitPython`, `requests`, `pyyaml`, `psutil`, `hvac`)_

### 3. Start the server

```bash
python main.py

```

The web interface will then be accessible at `http://localhost:8081` (or the port configured in your `main.py`).

---

## Configuration (Day-2 Operations)

Plugin configuration is **no longer** done in the code, but directly through the web interface:

1. Navigate to **System -> Einstellungen (Settings)** in Lyndrix.
2. Expand the **Secrets Manager**, enter your Vault URL (`http://127.0.0.1:8200`) and credentials, and click "Save".
3. Expand the **SSOT App Manager**, enter the GitLab URL, and provide your Personal Access Token (this will be securely encrypted and stored in the Vault!).
4. The **Discord Notifier** webhook can also be securely stored in the Vault from here.

---

_Developed for scalable Homelabs and Enterprise Environments._
