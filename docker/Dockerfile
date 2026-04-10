FROM python:3.11-slim
WORKDIR /app

# 1. Install System Dependencies
# Added 'libffi-dev' and 'ssl-dev' which are often needed for crypto/hvac
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    gcc \
    libc-dev \
    libmariadb-dev \
    libffi-dev \
    libssl-dev \
    pkg-config \
    curl \
    dos2unix \
    docker.io \
    && rm -rf /var/lib/apt/lists/*
# Download and install only the standalone Docker CLI
ENV DOCKER_VERSION=24.0.7
RUN curl -fsSLO https://download.docker.com/linux/static/stable/x86_64/docker-${DOCKER_VERSION}.tgz && \
    tar xzvf docker-${DOCKER_VERSION}.tgz --strip 1 -C /usr/local/bin docker/docker && \
    rm docker-${DOCKER_VERSION}.tgz



# 2. Layered Python Requirements (Best practice for build caching)
COPY app/requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 3. App Source Code
COPY app/ .

# 4. Directory Prep
# Ensure the mount points for your Git Repos and Plugins exist
RUN mkdir -p /opt/lyndrix/plugins_backup \
             /data/security \
             /app/plugins \
             /data/storage/git_repos

# 5. Plugin Backup Logic
RUN if [ -d "plugins" ] && [ "$(ls -A plugins 2>/dev/null)" ]; then \
        cp -r plugins/. /opt/lyndrix/plugins_backup/; \
    else \
        echo "No plugins found for backup. Creating empty backup dir."; \
        mkdir -p /opt/lyndrix/plugins_backup; \
    fi

# 6. Entrypoint Prep
COPY docker/entrypoint.sh /app/entrypoint.sh
RUN dos2unix /app/entrypoint.sh && chmod +x /app/entrypoint.sh

EXPOSE 8081

ENTRYPOINT ["/bin/bash", "/app/entrypoint.sh"]
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8081"]