import os
import asyncio
from core.bus import bus
from core.logger import get_logger

# WICHTIG: Relativer Import für die Datei im gleichen Ordner
from .crypto import KEY_FILE

log = get_logger("AutoUnseal")

class AutoUnsealManager:
    def __init__(self):
        bus.subscribe("system:started")(self.on_system_started)

    async def on_system_started(self, payload):
        """
        Wird gerufen, wenn das System bereit ist.
        """
        auto_key = os.getenv("LYNDRIX_MASTER_KEY")
        
        if not auto_key:
            log.info("ℹ️ Kein LYNDRIX_MASTER_KEY in ENV. Warte auf manuelle Eingabe.")
            return

        # Kurze Pause für die Sockets
        await asyncio.sleep(2)
        
        # LOGIK-ENTSCHEIDUNG
        if not os.path.exists(KEY_FILE):
            log.info("🪄 Frischer Vault erkannt. Starte AUTO-INIT...")
            bus.emit("vault:init_requested", {"key": auto_key})
        else:
            log.info("🔑 Keyfile gefunden. Starte AUTO-UNSEAL...")
            bus.emit("vault:unseal_requested", {"key": auto_key})

# Die Instanz wird hier erstellt
auto_unseal_manager = AutoUnsealManager()