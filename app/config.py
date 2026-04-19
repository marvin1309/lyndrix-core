import os
import logging
import re
from pathlib import Path
from typing import Optional, List, Dict
from pydantic import Field, BaseModel

from pydantic_settings import BaseSettings, SettingsConfigDict

_config_log = logging.getLogger("Core:Config")


class Settings(BaseSettings):
    """
    Central configuration for Lyndrix Core.
    Reads from environment variables, then .env file, then Vault.
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

    # --- DATABASE ---
    DB_HOST: str = "db"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "secret"
    DB_NAME: str = "lyndrix_db"

    # --- BOOTSTRAP CREDENTIALS ---
    LYNDRIX_ADMIN_USER: str = "admin"
    LYNDRIX_ADMIN_PASSWORD: str = "lyndrix"
    LYNDRIX_ADMIN_EMAIL: str = "admin@lyndrix.local"
    LYNDRIX_BOT_USER: str = "bot"
    LYNDRIX_BOT_PASSWORD: str = "lyndrix-bot"

    # --- VAULT ---
    VAULT_URL: str = "http://vault:8200"
    VAULT_SKIP_VERIFY: bool = True
    LYNDRIX_MASTER_KEY: Optional[str] = None

    # --- CRYPTO & SECURITY ---
    LYNDRIX_ARGON_TIME: int = 3
    LYNDRIX_ARGON_MEM: int = 65536
    LYNDRIX_ARGON_PARALLEL: int = 4

    # --- PLUGIN RECONCILIATION ---
    # Comma-separated list of plugin specs to auto-install on first boot.
    # Format: https://github.com/org/repo[@version]
    LYNDRIX_PLUGINS_DESIRED: Optional[str] = None
    # Whether to auto-update plugins to latest on reboot
    LYNDRIX_PLUGINS_AUTO_UPDATE: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    @property
    def DATABASE_URL(self) -> str:
        return f"mysql+pymysql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def DATABASE_URL_SAFE(self) -> str:
        """Connection string with credentials redacted for logging."""
        return f"mysql+pymysql://{self.DB_USER}:***@{self.DB_HOST}/{self.DB_NAME}"

    @property
    def LYNDRIX_VAULT_KEY_FILE(self) -> str:
        return f"{self.SECURITY_DIR}/vault_keys.enc"

    @property
    def desired_plugins(self) -> List[str]:
        """Parses LYNDRIX_PLUGINS_DESIRED into a list of plugin URLs."""
        return [plugin["url"] for plugin in self.desired_plugin_specs]

    @property
    def desired_plugin_specs(self) -> List[Dict[str, str]]:
        """Parses desired plugin specs into url/version pairs."""
        if not self.LYNDRIX_PLUGINS_DESIRED:
            return []

        specs = []
        for raw_entry in self.LYNDRIX_PLUGINS_DESIRED.split(","):
            entry = raw_entry.strip()
            if not entry:
                continue

            url = entry
            version = "latest"
            match = re.match(r"^(https?://[^@]+?)(?:@([^/@]+))?$", entry)
            if match:
                url = match.group(1)
                if match.group(2):
                    version = match.group(2)

            specs.append({"url": url, "version": version})

        return specs

    def warn_insecure_defaults(self):
        """Emits log warnings when production-unsafe defaults are active."""
        if self.ENV_TYPE != "dev":
            if self.STORAGE_SECRET == "dev_secret_only":
                _config_log.warning("SECURITY: STORAGE_SECRET is using development default! Set a secure value for production.")
            if self.DB_PASSWORD == "secret":
                _config_log.warning("SECURITY: DB_PASSWORD is using development default! Set a secure value for production.")
            if self.LYNDRIX_ADMIN_PASSWORD == "lyndrix":
                _config_log.warning("SECURITY: LYNDRIX_ADMIN_PASSWORD is using default. Set a secure value for production.")

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
                        if v_val is not None:
                            return v_val
            except Exception:
                pass

        # 4. Fallback
        if default is None:
            _config_log.warning(f"CONFIG: No value found for '{env_var}' and no default provided.")
        return default


# Singleton for the entire application
settings = Settings()