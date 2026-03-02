from pathlib import Path
from typing import Optional
from pydantic import Field, BaseModel

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
except ImportError:
    # Fallback for environments where pydantic-settings is not yet installed
    from pydantic import BaseSettings
    from pydantic import ConfigDict as SettingsConfigDict

class Settings(BaseSettings):
    """
    Zentrale Konfiguration für Lyndrix Core.
    Liest Variablen aus der Umgebung oder der .env Datei.
    """
    # --- APP INFO ---
    APP_NAME: str = "Lyndrix Core"
    ENV_TYPE: str = Field(default="dev")
    LOG_LEVEL: str = "INFO"
    APP_TITLE: str = "LYNDRIX - DEVELOPER MODE"  # Neuer Parameter für den Titel in der UI
    # --- SERVER ---
    PORT: int = 8081
    STORAGE_SECRET: str = "dev_secret_only"

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

# Singleton für die gesamte App
settings = Settings()