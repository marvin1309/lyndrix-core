import hvac
from core.bus import bus as global_bus
from core.logger import get_logger
from core.services import vault_instance
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
                self.log.debug(f"SUBSCRIBE: Subscribed to topic: {topic}")
                global_bus.subscribe(topic)(callback)
            else:
                self.log.warning(f"PERMISSION: Module not allowed to subscribe to '{topic}'!")
            return callback
        return decorator

    def emit(self, topic: str, payload: dict = None):
        if topic in self.manifest.permissions.emit or "*" in self.manifest.permissions.emit:
            global_bus.emit(topic, payload)
        else:
            self.log.warning(f"PERMISSION: Module not allowed to emit '{topic}'!")

    # --- VAULT PROXY (Hier war der Einrückungsfehler) ---

    def _get_vault_path(self) -> str:
        """Bestimmt den Basis-Pfad für dieses Modul im Vault."""
        folder = "core" if self.manifest.type == "CORE" else "plugins"
        return f"{folder}/{self.manifest.id}"

    def get_secret(self, key: str) -> str:
        """Lädt einen einzelnen Wert aus dem KV-V2 Store."""
        if not vault_instance.is_connected:
            return None
            
        path = self._get_vault_path()
        try:
            # hvac v2 read: mount_point 'lyndrix' ist das Haupt-Regal
            response = vault_instance.client.secrets.kv.v2.read_secret_version(
                path=path,
                mount_point="lyndrix"
            )
            # In V2 liegen die echten Daten gekapselt in ['data']['data']
            if response and 'data' in response and 'data' in response['data']:
                return response['data']['data'].get(key)
        except Exception:
            return None
        return None

    def set_secret(self, key: str, value: str):
        """Speichert einen Wert im KV-V2 Store, ohne andere Keys zu löschen."""
        if not vault_instance.is_connected:
            self.log.error("VAULT: Vault not connected.")
            return False
            
        path = self._get_vault_path()
        try:
            # 1. Bestehende Daten laden (um sie beim Update nicht zu löschen)
            current_data = {}
            try:
                response = vault_instance.client.secrets.kv.v2.read_secret_version(
                    path=path, mount_point="lyndrix"
                )
                current_data = response['data']['data']
            except Exception:
                pass # Pfad existiert noch nicht

            # 2. Wert im Dictionary aktualisieren
            current_data[key] = value

            # 3. Komplettes Dictionary zurückschreiben (KV-V2 Standard)
            vault_instance.client.secrets.kv.v2.create_or_update_secret(
                path=path,
                mount_point="lyndrix",
                secret=current_data
            )
            self.log.info(f"SUCCESS: Secret '{key}' persisted securely at '{path}'.")
            return True
        except Exception as e:
            self.log.error(f"ERROR: Failed to write to Vault: {e}", exc_info=True)
            return False