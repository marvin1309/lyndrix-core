import hvac
import os
import asyncio
from core.bus import bus
from core.logger import get_logger

from .crypto import decrypt_vault_keys, KEY_FILE
from .vault_init import VaultInitializer

log = get_logger("VaultService")

class VaultService:
    def __init__(self):
        self.url = os.getenv("VAULT_ADDR", "http://lyndrix-vault-dev:8200")
        self.client = hvac.Client(url=self.url)
        self.is_connected = False
        self.ui_state = "loading" # loading, needs_init, needs_unseal, ready

        # Bus-Events abonnieren
        bus.subscribe("system:started")(self.check_vault_health)
        bus.subscribe("vault:init_requested")(self.handle_init)
        bus.subscribe("vault:unseal_requested")(self.handle_unseal)

    async def _ensure_lyndrix_mount(self):
        """Stellt sicher, dass die Secret Engine 'lyndrix' existiert."""
        try:
            mounts = self.client.sys.list_mounted_secrets_engines()
            if 'lyndrix/' not in mounts:
                log.info("🛠️ Erstelle isolierten 'lyndrix' Secret-Store (KV v2)...")
                self.client.sys.enable_secrets_engine(
                    backend_type='kv', 
                    path='lyndrix', 
                    options={'version': '2'}
                )
            return True
        except Exception as e:
            log.error(f"⚠️ Fehler beim Mount-Check: {e}")
            return False

    async def check_vault_health(self, payload=None):
        log.info("🔍 Prüfe Vault Status...")
        try:
            if not self.client.sys.is_initialized():
                self.ui_state = "needs_init"
                log.warning("⚠️ Vault ist noch nicht initialisiert!")
                return

            if self.client.sys.is_sealed():
                self.ui_state = "needs_unseal"
                log.info("🔓 Vault ist versiegelt. Warte auf Key...")
            else:
                # --- FIX FÜR TOKEN-VERLUST ---
                self.ui_state = "ready"
                self.is_connected = True
                
                # Wenn wir ein Keyfile haben, laden wir den Token sofort wieder in den Client
                if os.path.exists(KEY_FILE):
                    auto_key = os.getenv("LYNDRIX_MASTER_KEY")
                    if auto_key:
                        try:
                            with open(KEY_FILE, 'rb') as f:
                                keys = decrypt_vault_keys(auto_key, f.read())
                                self.client.token = keys['root_token']
                                log.info("🔑 Token im laufenden Betrieb wiederhergestellt.")
                        except:
                            log.error("❌ Token-Wiederherstellung fehlgeschlagen (Falscher Master Key?)")

                await self._ensure_lyndrix_mount()
                log.info("✅ Vault ist bereits offen und bereit.")
                bus.emit("vault:opened", {})
                bus.emit("vault:ready_for_data", {}) # Plugins dürfen jetzt laden
        except Exception as e:
            log.error(f"❌ Vault Verbindungsfehler: {e}")

    async def handle_init(self, payload):
        key = payload.get("key")
        log.info("🪄 Initialisiere neuen Vault...")
        try:
            init_helper = VaultInitializer(self.url)
            keys = init_helper.setup_fresh_vault(key)
            self.client.token = keys['root_token']
            self.client.sys.submit_unseal_keys(keys['unseal_keys'])
            
            # WICHTIG: Mount erstellen nach Init
            await self._ensure_lyndrix_mount()
            
            self.ui_state = "ready"
            self.is_connected = True
            bus.emit("vault:opened", {})
        except Exception as e:
            log.error(f"💥 Init fehlgeschlagen: {e}")



    async def handle_unseal(self, payload):
        key = payload.get("key")
        try:
            with open(KEY_FILE, 'rb') as f:
                encrypted_blob = f.read()
            keys = decrypt_vault_keys(key, encrypted_blob)
            
            self.client.token = keys['root_token'] 
            self.client.sys.submit_unseal_keys(keys['unseal_keys'])
            
            success = await self._ensure_lyndrix_mount()
            if success:
                self.ui_state = "ready"
                self.is_connected = True
                log.info("🔓 Vault erfolgreich entsiegelt und bereit!")
                bus.emit("vault:opened", {})
                bus.emit("vault:ready_for_data", {}) # Plugins dürfen jetzt laden
        except Exception as e:
            log.error(f"❌ Unseal fehlgeschlagen: {e}")

vault_instance = VaultService()