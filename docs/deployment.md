# Installation & Deployment Guide

Lyndrix Core is optimized for containerized deployment. This guide covers setup for both local development and production environments.

---

## System Requirements

### Development Environment

- Docker Engine v24.0+
- Docker Compose v2.20+
- Minimum 2GB RAM
- 10GB disk space
- Active internet connection

### Production Environment

- Docker Engine v24.0+ (or Kubernetes 1.24+)
- Docker Compose v2.20+
- Minimum 8GB RAM
- 50GB+ disk space
- Dedicated storage backend (NFS/EFS/S3)
- SSL/TLS certificates
- Network access controls and firewall rules

---

## Local Development Setup

The development environment prioritizes developer experience with hot-reloading, live code mounts, and persistent isolated state.

### Architecture Overview

```
┌─────────────────────────────────────────┐
│     Your Local Machine                  │
│  ┌────────────────────────────────────┐ │
│  │ lyndrix-core/                      │ │
│  │ ├── app/          (mounted)        │ │
│  │ ├── plugins/      (mounted)        │ │
│  │ ├── docker/                        │ │
│  │ ├── docs/                          │ │
│  │ └── .dev/         (persistent)     │ │
│  │     ├── storage/  (database)       │ │
│  │     ├── vault/    (encryption)     │ │
│  │     └── logs/     (output)         │ │
│  └────────────────────────────────────┘ │
│           ▼ Docker Volumes              │
├─────────────────────────────────────────┤
│     Docker Container (Lyndrix Core)     │
│  • FastAPI + NiceGUI                    │
│  • Hot-reload on file changes           │
│  • Code mounts from host                │
├─────────────────────────────────────────┤
│     Supporting Containers                │
│  • MariaDB (Development)                │
│  • HashiCorp Vault                      │
└─────────────────────────────────────────┘
```

### The `.dev` Directory

The `.dev` folder maintains persistent state for your local environment:

- **`.dev/storage/`**: Database files, uploaded assets, and Git repositories
- **`.dev/vault/`**: Encrypted vault configuration and keys
- **`.dev/logs/`**: Application and container logs

**Advantages**:
- Git repository remains clean; `.dev/` is in `.gitignore`
- System state persists across `docker compose down` and `docker compose up`
- Prevents pollution of your project directory with temporary files
- Easy reset: simply delete `.dev/` to start fresh

### Step-by-Step Installation

#### 1. Clone Repository

```bash
git clone https://github.com/marvin1309/lyndrix-core.git
cd lyndrix-core
```

#### 2. Create Environment Configuration

Copy the development environment template:

```bash
cp docker/.env.dev docker/.env
```

Review the generated `.env` file:

```env
# System Configuration
ENV_TYPE=dev
LOG_LEVEL=DEBUG
STORAGE_SECRET=lyndrix_local_dev_secret_12345

# Storage Paths
HOST_GIT_REPOS_DIR=/home/marvin/gitlab/lyndrix-dev/lyndrix-core/.dev/storage/git_repos
HOST_SECURITY_DIR=/home/marvin/gitlab/lyndrix-dev/lyndrix-core/.dev/secure_data

# Database Configuration
DB_HOST=lyndrix-db-dev
DB_NAME=lyndrix_db
DB_USER=admin
DB_PASSWORD=secret
DB_ROOT_PASSWORD=root_secret

# Vault Configuration
VAULT_URL=http://vault:8200
VAULT_SKIP_VERIFY=true
LYNDRIX_MASTER_KEY=C2RNVbITSzb60iA1LDowLwBuIXehvDPRzfV6FCfH
```

**Security Note**: The development master key shown above is for development only. Change it in production environments.

#### 3. Start Development Environment

```bash
docker compose -f docker/docker-compose.dev.yml up -d --build
```

This command:
- Builds the Lyndrix Core image from the Dockerfile
- Starts MariaDB, Vault, and Lyndrix Core containers
- Mounts your local code for hot-reloading
- Creates persistent volumes in `.dev/`

#### 4. Monitor Startup

```bash
# Follow container logs
docker compose -f docker/docker-compose.dev.yml logs -f app

# Or individual container
docker logs -f app
```

Expected startup sequence (2-3 minutes):
1. Database initialization (MariaDB)
2. Vault unsealing
3. Core component loading
4. Plugin discovery and loading
5. Web server ready

#### 5. Access the Application

Once startup completes, open your browser:

```
http://localhost:8081
```

Initial setup walkthrough:
1. **Vault Setup**: Generate or enter Master Key
2. **User Registration**: Create admin account
3. **Database Initialization**: Automatic
4. **Dashboard**: System is ready for use

### Hot Reloading in Development

Code changes are automatically reflected without container restarts:

```bash
# Edit a file
nano app/main.py

# Save - the app automatically reloads in ~1 second
# Refresh your browser to see changes
```

### Stopping Development Environment

```bash
# Stop all containers (preserves .dev/ state)
docker compose -f docker/docker-compose.dev.yml down

# Stop and remove state (clean reset)
docker compose -f docker/docker-compose.dev.yml down
rm -rf .dev/
```

### Troubleshooting Development Setup

**Issue**: "Vault is sealed" error
```bash
# Unseal using master key from LYNDRIX_MASTER_KEY in .env
# Or enter it via the web UI at http://localhost:8081/unseal
```

**Issue**: Database connection refused
```bash
# Wait 30 seconds for MariaDB to initialize, then reload
# Check: docker compose logs lyndrix-db-dev
```

**Issue**: Port 8081 already in use
```bash
# Change port in docker-compose.dev.yml:
# services:
#   app:
#     ports:
#       - "8080:8081"  # Changed from 8081:8081
```

**Issue**: Hot reload not working
```bash
# Verify code mounts in docker-compose.dev.yml
# Check: docker inspect app | grep Mounts
```

---

## Production Deployment

Production deployments prioritize security, reliability, and performance. Code is immutable, hot-reload is disabled, and volumes are externally managed.

### Pre-Deployment Checklist

- [ ] SSL/TLS certificates obtained (Let's Encrypt recommended)
- [ ] Database backup strategy defined
- [ ] Vault backup and recovery tested
- [ ] Monitoring and alerting configured
- [ ] Load balancer or reverse proxy configured
- [ ] Network policies and firewall rules established
- [ ] Secrets management strategy in place (HashiCorp Vault, AWS Secrets Manager, etc.)
- [ ] Regular backup schedule created

### Docker Deployment

#### 1. Prepare Production Environment

```bash
git clone https://github.com/marvin1309/lyndrix-core.git
cd lyndrix-core
```

#### 2. Create Secure Configuration

Copy the production template:

```bash
cp docker/.env.prod docker/.env
```

Edit `.env` with production values:

```env
# System Configuration
ENV_TYPE=prod
LOG_LEVEL=INFO
STORAGE_SECRET=generate_a_very_long_random_string_here

# CRITICAL: Change these for production
DB_HOST=mariadb
DB_NAME=lyndrix_prod
DB_USER=prod_admin
DB_PASSWORD=generate_strong_password_here
DB_ROOT_PASSWORD=generate_strong_password_here

# Vault Configuration
VAULT_URL=http://vault:8200
VAULT_SKIP_VERIFY=false
# Do NOT set LYNDRIX_MASTER_KEY in production
# Unseal manually for security
```

Generate secure passwords:

```bash
# Generate 32-character random string
openssl rand -base64 32
```

#### 3. Configure Docker Compose

Review and customize `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    image: lyndrix/lyndrix-core:latest
    container_name: lyndrix-app-prod
    restart: always
    environment:
      - ENV_TYPE=prod
      - DB_HOST=mariadb
      # ... other variables from .env
    volumes:
      - /etc/letsencrypt/live/example.com:/app/certs:ro
      - vault_keys:/data/vault
      - app_logs:/app/logs
    ports:
      - "8081:8081"
    depends_on:
      - mariadb
      - vault
    networks:
      - lyndrix-network

  mariadb:
    image: mariadb:11.4-alpine
    container_name: lyndrix-mariadb-prod
    restart: always
    environment:
      MARIADB_DATABASE: ${DB_NAME}
      MARIADB_USER: ${DB_USER}
      MARIADB_PASSWORD: ${DB_PASSWORD}
      MARIADB_ROOT_PASSWORD: ${DB_ROOT_PASSWORD}
    volumes:
      - mariadb_data:/var/lib/mysql
    networks:
      - lyndrix-network

  vault:
    image: vault:latest
    container_name: lyndrix-vault-prod
    restart: always
    environment:
      - VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200
    volumes:
      - vault_data:/vault/file
    ports:
      - "8200:8200"
    networks:
      - lyndrix-network

volumes:
  mariadb_data:
    driver: local
  vault_data:
    driver: local
  vault_keys:
    driver: local
  app_logs:
    driver: local

networks:
  lyndrix-network:
    driver: bridge
```

#### 4. Deploy Containers

```bash
docker compose -f docker-compose.prod.yml up -d --build
```

#### 5. Post-Deployment Setup

After containers are running:

1. **Initialize Vault**:
   - Navigate to `http://your-server:8200/ui/`
   - Generate unseal keys (store securely, offline preferred)
   - Save root token in secure vault (1Password, AWS Secrets Manager, etc.)

2. **Create Admin User**:
   ```bash
   docker exec lyndrix-app-prod python -c "
   from core.components.auth.logic.models import User
   from core.components.database.logic.db_service import db_instance
   
   admin = User(username='admin', password='secure_password')
   db_instance.add(admin)
   db_instance.commit()
   "
   ```

3. **Test Configuration**:
   ```bash
   curl -s http://localhost:8081/api/health | jq .
   ```

### Kubernetes Deployment

For enterprise environments, use Kubernetes:

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: lyndrix-core
spec:
  replicas: 3
  selector:
    matchLabels:
      app: lyndrix-core
  template:
    metadata:
      labels:
        app: lyndrix-core
    spec:
      containers:
      - name: lyndrix-core
        image: lyndrix/lyndrix-core:v1.0.0
        ports:
        - containerPort: 8081
        env:
        - name: DB_HOST
          valueFrom:
            configMapKeyRef:
              name: lyndrix-config
              key: db_host
        - name: DB_PASSWORD
          valueFrom:
            secretKeyRef:
              name: lyndrix-secrets
              key: db_password
        livenessProbe:
          httpGet:
            path: /health
            port: 8081
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8081
          initialDelaySeconds: 10
          periodSeconds: 5
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        volumeMounts:
        - name: vault-keys
          mountPath: /data/vault
        - name: app-logs
          mountPath: /app/logs
      volumes:
      - name: vault-keys
        secret:
          secretName: vault-keys
      - name: app-logs
        emptyDir: {}
```

### Docker Registry Setup

Build and push to your registry:

```bash
# Build image
docker build -f docker/Dockerfile -t myregistry.azurecr.io/lyndrix-core:v1.0.0 .

# Push to registry
docker push myregistry.azurecr.io/lyndrix-core:v1.0.0

# Pull and run
docker pull myregistry.azurecr.io/lyndrix-core:v1.0.0
docker run -d myregistry.azurecr.io/lyndrix-core:v1.0.0
```

---

## Reverse Proxy Configuration

### Nginx

```nginx
upstream lyndrix_backend {
    server localhost:8081;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    
    location / {
        proxy_pass http://lyndrix_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### Apache

```apache
<VirtualHost *:443>
    ServerName your-domain.com
    
    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/your-domain.com/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/your-domain.com/privkey.pem
    
    ProxyPreserveHost On
    ProxyPass / http://localhost:8081/
    ProxyPassReverse / http://localhost:8081/
    
    # WebSocket support
    RewriteEngine On
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://localhost:8081/$1" [P,L]
</VirtualHost>

<VirtualHost *:80>
    ServerName your-domain.com
    Redirect / https://your-domain.com/
</VirtualHost>
```

---

## Backup & Recovery

### Database Backup

```bash
# Backup MariaDB
docker exec lyndrix-mariadb-prod mysqldump -u root -p${DB_ROOT_PASSWORD} \
    --all-databases > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i lyndrix-mariadb-prod mysql -u root -p${DB_ROOT_PASSWORD} < backup.sql
```

### Vault Backup

```bash
# Backup Vault configuration
docker exec lyndrix-vault-prod vault operator raft snapshot save /tmp/raft.snap
docker cp lyndrix-vault-prod:/tmp/raft.snap ./raft.snap

# Store offline
gpg --symmetric raft.snap
```

---

## Monitoring & Logging

### Container Monitoring

```bash
# View logs
docker logs -f lyndrix-app-prod

# Monitor resource usage
docker stats lyndrix-app-prod

# Health check
curl -s http://localhost:8081/health | jq .
```

### Application Metrics

Access system metrics at:
```
http://your-domain/dashboard
```

---

## Security Hardening

### Network Security

```bash
# Restrict container network
docker network create \
  --driver bridge \
  --opt com.docker.network.driver.mtu=1450 \
  --subnet=172.20.0.0/16 \
  lyndrix-isolated
```

### Secrets Management

Never commit `.env` files to Git:

```bash
# Add to .gitignore
echo "docker/.env" >> .gitignore
echo "docker/.env.prod" >> .gitignore
```

Use external secrets management:

```bash
# AWS Secrets Manager
aws secretsmanager get-secret-value --secret-id lyndrix/db-password

# HashiCorp Vault (integrated)
vault kv get lyndrix/database/credentials
```

---

## Performance Tuning

### Database Optimization

```sql
-- Create indexes
CREATE INDEX idx_user_email ON users(email);
CREATE INDEX idx_plugin_status ON plugins(status);

-- Enable query cache
SET GLOBAL query_cache_size = 268435456;
```

### Application Tuning

Edit `docker-compose.prod.yml`:

```yaml
app:
  environment:
    - WORKERS=8  # Adjust based on CPU cores
    - TIMEOUT=120
    - MAX_CONNECTIONS=100
```

---

## Troubleshooting Production

### Container Won't Start

```bash
# Check logs
docker compose logs app

# Verify environment variables
docker inspect app | grep "ENV_TYPE"

# Check port availability
lsof -i :8081
```

### Database Connection Issues

```bash
# Test connection
docker exec app mysql -h mariadb -u admin -psecret -e "SELECT 1"

# Check network
docker network inspect lyndrix_network
```

### High Memory Usage

```bash
# Monitor memory
docker stats --no-stream app

# Adjust resource limits in compose file
resources:
  limits:
    memory: 2G
```

---

## Upgrading Lyndrix Core

```bash
# Pull latest version
git pull origin main

# Rebuild image
docker compose -f docker-compose.prod.yml build --no-cache

# Restart with new image
docker compose -f docker-compose.prod.yml up -d
```

Always backup before upgrading production environments.
