import os
from core.bus import bus
from core.logger import get_logger
from core.services.vault.crypto import KEY_FILE # NEU: Importiere den Pfad

log = get_logger("AutoUnseal")

class AutoUnsealManager:
    def __init__(self):
        bus.subscribe("system:started")(self.attempt_auto_unseal)

    async def attempt_auto_unseal(self, payload):
        auto_key = os.getenv("LYNDRIX_MASTER_KEY")
        
        if auto_key:
            # CHECK: Ist es ein komplett frisches System?
            if not os.path.exists(KEY_FILE):
                log.info("🪄 Frischer Vault erkannt & Master-Key in ENV. Starte AUTO-INIT...")
                bus.emit("vault:init_requested", {"key": auto_key})
            else:
                log.info("🔑 Master-Key in ENV gefunden. Starte AUTO-UNSEAL...")
                bus.emit("vault:unseal_requested", {"key": auto_key})
        else:
            log.info("ℹ️ Kein Master-Key gefunden. Warten auf Benutzereingabe über UI.")

auto_unseal_manager = AutoUnsealManager()