import os
from pathlib import Path
from typing import Optional
from pydantic import Field, BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """
    Zentrale Konfiguration für Lyndrix Core.
    Liest Variablen aus der Umgebung oder der .env Datei.
    """
    # --- APP INFO ---
    APP_NAME: str = "Lyndrix Core"
    ENV_TYPE: str = Field(default="dev")
    LOG_LEVEL: str = "INFO"
    APP_TITLE: str = "LYNDRIX - DEVELOPER MODE" 
    # --- SERVER ---
    PORT: int = 8081
    STORAGE_SECRET: str = "dev_secret_only"

    # --- PATHS (Cloud Native) ---
    STORAGE_DIR: str = "/data/storage"
    SECURITY_DIR: str = "/data/security"
    LOGS_DIR: str = "/app/logs"
    PLUGINS_DIR: str = "/app/plugins"

    # --- DATENBANK ---
    # Diese Namen müssen EXAKT so in der .env stehen
    DB_HOST: str = "db"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "secret"
    DB_NAME: str = "lyndrix_db"

    # --- VAULT ---
    VAULT_URL: str = "http://vault:8200"
    VAULT_SKIP_VERIFY: bool = True
    LYNDRIX_MASTER_KEY: Optional[str] = None

    # --- CRYPTO & SECURITY ---
    LYNDRIX_ARGON_TIME: int = 3
    LYNDRIX_ARGON_MEM: int = 65536
    LYNDRIX_ARGON_PARALLEL: int = 4

    # Konfiguration für Pydantic
    model_config = SettingsConfigDict(
        # Docker sucht die .env Datei normalerweise im Root oder docker-Ordner
        # Wir priorisieren echte Umgebungsvariablen (Docker-Environment)
        env_file=".env", 
        extra="ignore"
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def LYNDRIX_VAULT_KEY_FILE(self) -> str:
        return f"{self.SECURITY_DIR}/vault_keys.enc"

    def get(self, env_var: str, vault_key: str = None, default: str = None) -> str:
        """
        Cloud-Native Configuration Hierarchy (ENV First):
        1. OS Environment Variable
        2. .env File (via Pydantic)
        3. Vault KV (If connected)
        4. Default Value
        """
        # 1. Strict OS Environment check
        val = os.getenv(env_var)
        if val is not None:
            return val
        
        # 2. Pydantic config (falls back to .env automatically)
        if hasattr(self, env_var):
            val = getattr(self, env_var)
            if val is not None:
                return val
                
        # 3. Secure Vault integration (Lazy import to avoid circular dependency)
        if vault_key:
            try:
                from core.services import vault_instance
                if vault_instance.is_connected:
                    secret = vault_instance.client.secrets.kv.v2.read_secret_version(path="core/settings", mount_point="lyndrix")
                    if secret and 'data' in secret and 'data' in secret['data']:
                        v_val = secret['data']['data'].get(vault_key)
                        if v_val is not None: return v_val
            except Exception:
                pass

        # 4. Fallback
        return default

# Singleton für die gesamte App
settings = Settings()