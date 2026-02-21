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
        self.client = None
        self.is_connected = False
        self.url = os.getenv("VAULT_URL", "http://vault:8200")
        self.initializer = VaultInitializer(self.url)
        self._last_used_key = None 

        bus.subscribe("system:started")(self.start_loop)
        bus.subscribe("vault:unseal_requested")(self.handle_unseal)
        bus.subscribe("vault:init_requested")(self.handle_initial_setup)

    async def start_loop(self, payload):
        asyncio.create_task(self._connection_loop())

    async def _connection_loop(self):
        log.info("🔄 Starte Vault-Scanner-Loop...")
        while not self.is_connected:
            try:
                self.client = hvac.Client(url=self.url)
                
                try:
                    is_initialized = self.client.sys.is_initialized()
                except Exception:
                    bus.emit("system:maintenance_mode", {
                        "service": "vault",
                        "active": True, 
                        "title": "Sicherheitssystem Offline", 
                        "msg": "Die Verbindung zum Vault-Server wird aufgebaut..."
                    })
                    await asyncio.sleep(5)
                    continue

                # VAULT ONLINE -> Lock für 'vault' entfernen
                bus.emit("system:maintenance_mode", {"service": "vault", "active": False})

                # In der _connection_loop von VaultService
                if not is_initialized:
                    # NEU: Wir signalisieren, dass wir bereit für ein Init sind!
                    bus.emit("vault:ready_for_init") 
                    await asyncio.sleep(2)
                    continue

                # --- Ab hier: Vault ist initialisiert ---
                if self.client.sys.is_sealed() or not self.client.token:
                    if not self._last_used_key:
                        await asyncio.sleep(2)
                        continue 
                    
                    with open(KEY_FILE, 'rb') as f:
                        creds = decrypt_vault_keys(self._last_used_key, f.read())
                    
                    self.client.token = creds['root_token']
                    if self.client.sys.is_sealed():
                        log.info("Vault ist versiegelt. Führe Unseal durch...")
                        self.client.sys.submit_unseal_key(creds['unseal_keys'][0])

                if self.client.is_authenticated() and not self.client.sys.is_sealed():
                    self.is_connected = True
                    log.info("✅ Vault erfolgreich verbunden und entsperrt!")
                    bus.emit("vault:opened", {"status": "success"})
                    asyncio.create_task(self._watchdog())
                    break
                else:
                    raise Exception("Vault erreicht, aber Auth fehlgeschlagen.")

            except Exception as e:
                log.error(f"❌ Fehler im Vault-Loop: {e}")
                if "Auth fehlgeschlagen" in str(e):
                    self._last_used_key = None 
                await asyncio.sleep(2)

    async def _watchdog(self):
        while self.is_connected:
            await asyncio.sleep(10)
            try:
                if self.client.sys.is_sealed():
                    raise Exception("Vault hat sich unerwartet versiegelt.")
                self.client.auth.token.lookup_self()
            except Exception as e:
                log.error(f"❌ Vault-Verbindung abgerissen: {e}")
                self.is_connected = False
                
                bus.emit("system:maintenance_mode", {
                    "service": "vault",
                    "active": True, 
                    "title": "Sicherheitswarnung", 
                    "msg": "Die Verbindung zum Verschlüsselungssystem wurde getrennt."
                })
                
                asyncio.create_task(self._connection_loop())
                break

    async def handle_unseal(self, payload):
        self._last_used_key = payload.get("key")

    async def handle_initial_setup(self, payload):
        master_key = payload.get("key")
        log.info("🛠️ Initialisiere neuen Vault...")
        try:
            self.initializer.setup_fresh_vault(master_key)
            log.info("✅ Vault Initialisierung erfolgreich.")
            # WICHTIG: Setze den Key, damit der Loop im nächsten Durchlauf unsealed!
            self._last_used_key = master_key
            bus.emit("vault:init_success", {})
        except Exception as e:
            log.error(f"❌ Vault Initialisierung fehlgeschlagen: {e}")
            bus.emit("vault:error", {"msg": str(e)})

vault_instance = VaultService()