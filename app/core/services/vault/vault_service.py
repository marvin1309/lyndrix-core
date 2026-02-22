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
        self._is_initializing = False
        
        # NEU: Der Status für die Frontend-UI!
        self.ui_state = "loading" # "loading" | "needs_init" | "needs_unseal" | "ready"

        bus.subscribe("system:started")(self.start_loop)
        bus.subscribe("vault:unseal_requested")(self.handle_unseal)
        bus.subscribe("vault:init_requested")(self.handle_initial_setup)

    async def start_loop(self, payload):
        asyncio.create_task(self._connection_loop())

    async def _connection_loop(self):
        log.info("🔄 Starte Vault-Scanner-Loop...")
        await asyncio.sleep(2)
        
        while not self.is_connected:
            try:
                self.client = hvac.Client(url=self.url)
                
                try:
                    is_initialized = self.client.sys.is_initialized()
                except Exception:
                    self.ui_state = "loading"
                    bus.emit("system:maintenance_mode", {"service": "vault", "active": True, "title": "Sicherheitssystem Offline", "msg": "Warte auf Vault-Container..."})
                    await asyncio.sleep(3)
                    continue

                bus.emit("system:maintenance_mode", {"service": "vault", "active": False})

                # --- FALL 1: Vault ist leer (Nicht initialisiert) ---
                if not is_initialized:
                    auto_key = os.getenv("LYNDRIX_MASTER_KEY")
                    if auto_key and not os.path.exists(KEY_FILE) and not self._is_initializing:
                        self.ui_state = "loading"
                        log.info("🪄 Frischer Vault & Master-Key in ENV erkannt. Starte AUTO-INIT...")
                        await self.handle_initial_setup({"key": auto_key})
                    else:
                        # NEU: Signal an die UI, dass die Init-Maske benötigt wird!
                        self.ui_state = "needs_init"
                        log.debug("Warte auf manuelle Vault-Initialisierung über UI...")
                        await asyncio.sleep(2)
                    continue

                # --- FALL 2: Vault ist versiegelt ---
                if self.client.sys.is_sealed() or not self.client.token:
                    auto_key = os.getenv("LYNDRIX_MASTER_KEY")
                    
                    if auto_key and os.path.exists(KEY_FILE) and not self._last_used_key:
                        self._last_used_key = auto_key
                        
                    if not self._last_used_key:
                        # NEU: Signal an die UI, dass der Unseal-Key benötigt wird!
                        self.ui_state = "needs_unseal"
                        await asyncio.sleep(2)
                        continue 
                    
                    self.ui_state = "loading"
                    try:
                        with open(KEY_FILE, 'rb') as f:
                            creds = decrypt_vault_keys(self._last_used_key, f.read())
                        self.client.token = creds['root_token']
                        if self.client.sys.is_sealed():
                            log.info("🔓 Vault ist versiegelt. Führe Unseal durch...")
                            self.client.sys.submit_unseal_key(creds['unseal_keys'][0])
                    except Exception as dec_err:
                        log.error(f"❌ Entschlüsselungsfehler (Falscher Key?): {dec_err}")
                        self._last_used_key = None
                        await asyncio.sleep(2)
                        continue

                # --- FALL 3: Vault ist OFFEN & BEREIT ---
                if self.client.is_authenticated() and not self.client.sys.is_sealed():
                    self.is_connected = True
                    self.ui_state = "ready"
                    log.info("✅ Vault erfolgreich verbunden und entsperrt!")
                    
                    try:
                        mounts = self.client.sys.list_mounted_secrets_engines()
                        if 'lyndrix/' not in mounts:
                            log.info("🛠️ Erstelle isolierten 'lyndrix' Secret-Store (KV v2)...")
                            self.client.sys.enable_secrets_engine(backend_type='kv', path='lyndrix', options={'version': '2'})
                    except Exception as e:
                        log.error(f"⚠️ Fehler beim Mounten des Secret-Stores: {e}")

                    bus.emit("vault:opened", {"status": "success"})
                    asyncio.create_task(self._watchdog())
                    break
                else:
                    raise Exception("Auth fehlgeschlagen.")

            except Exception as e:
                log.error(f"❌ Fehler im Vault-Loop: {e}")
                if "Auth fehlgeschlagen" in str(e):
                    self._last_used_key = None 
                await asyncio.sleep(2)

    async def _watchdog(self):
        while self.is_connected:
            await asyncio.sleep(10)
            try:
                if self.client.sys.is_sealed(): raise Exception("Vault versiegelt sich selbst.")
                self.client.auth.token.lookup_self()
            except Exception as e:
                log.error(f"❌ Vault-Verbindung abgerissen: {e}")
                self.is_connected = False
                self.ui_state = "loading"
                bus.emit("system:maintenance_mode", {"service": "vault", "active": True, "title": "Sicherheitswarnung", "msg": "Die Verbindung zum Verschlüsselungssystem wurde getrennt."})
                asyncio.create_task(self._connection_loop())
                break

    async def handle_unseal(self, payload):
        self._last_used_key = payload.get("key")

    async def handle_initial_setup(self, payload):
        if self._is_initializing: return
        self._is_initializing = True
        self.ui_state = "loading"
        master_key = payload.get("key")
        
        log.info("🛠️ Führe Vault-Initialisierung aus...")
        try:
            self.initializer.setup_fresh_vault(master_key)
            log.info("✨ Initialisierung abgeschlossen.")
            self._last_used_key = master_key
            bus.emit("vault:init_success", {})
        except Exception as e:
            log.error(f"❌ Vault Initialisierung fehlgeschlagen: {e}")
            bus.emit("vault:error", {"msg": str(e)})
        finally:
            self._is_initializing = False

vault_instance = VaultService()