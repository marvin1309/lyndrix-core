import hvac
from core.bus import bus as global_bus
from core.logger import get_logger
from core.services.vault.vault_service import vault_instance
from .models import ModuleManifest

class ModuleContext:
    """
    Der isolierte Sandkasten für JEDES Modul (Core & Plugin).
    """
    def __init__(self, manifest: ModuleManifest):
        self.manifest = manifest
        # Logger zeigt z.B. [Core: IAM] oder [Plugin: Discord]
        prefix = "Core" if manifest.type == "CORE" else "Plugin"
        self.log = get_logger(f"{prefix}:{manifest.name}")
        self.state = {}

    # --- EVENT BUS PROXY ---

    def subscribe(self, topic: str):
        def decorator(callback):
            if topic in self.manifest.permissions.subscribe or "*" in self.manifest.permissions.subscribe:
                self.log.debug(f"Abonniert Topic: {topic}")
                global_bus.subscribe(topic)(callback)
            else:
                self.log.warning(f"🚫 Rechtefehler: Modul darf '{topic}' nicht abonnieren!")
            return callback
        return decorator

    def emit(self, topic: str, payload: dict = None):
        if topic in self.manifest.permissions.emit or "*" in self.manifest.permissions.emit:
            global_bus.emit(topic, payload)
        else:
            self.log.warning(f"🚫 Rechtefehler: Modul darf '{topic}' nicht senden!")

    # --- VAULT PROXY ---

    def _get_vault_path(self, key: str) -> str:
        """Bestimmt den Speicherort basierend auf dem Modultyp."""
        folder = "core" if self.manifest.type == "CORE" else "plugins"
        return f"{folder}/{self.manifest.id}/{key}"

    def get_secret(self, key: str) -> str:
        if not vault_instance.is_connected:
            self.log.error("Vault ist nicht verbunden!")
            return None
            
        path = self._get_vault_path(key)
        try:
            response = vault_instance.client.secrets.kv.v2.read_secret_version(
                path=path, mount_point="lyndrix"
            )
            return response['data']['data'].get('value')
        except hvac.exceptions.InvalidPath:
            self.log.debug(f"Secret '{key}' nicht im Vault gefunden.")
            return None
        except Exception as e:
            self.log.error(f"Fehler beim Vault-Zugriff: {e}")
            return None

    def set_secret(self, key: str, value: str):
        if not vault_instance.is_connected:
            self.log.error("❌ Speichern fehlgeschlagen: Vault ist nicht verbunden oder versiegelt.")
            return False
            
        path = self._get_vault_path(key)
        try:
            vault_instance.client.secrets.kv.v2.create_or_update_secret(
                path=path, mount_point="lyndrix", secret={"value": value}
            )
            self.log.info(f"✅ Secret '{key}' sicher im Vault unter '{path}' gespeichert.")
            return True
        except hvac.exceptions.InvalidPath:
            # Das passiert, wenn das "lyndrix" Secret-Engine noch nicht fertig gemountet ist!
            self.log.error(f"❌ Pfad-Fehler. Das Vault-Regal 'lyndrix/' existiert noch nicht!")
            return False
        except Exception as e:
            self.log.error(f"❌ Fehler beim Speichern im Vault: {e}")
            return False