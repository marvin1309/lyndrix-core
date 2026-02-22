import os
import asyncio
from core.bus import bus
from core.logger import get_logger
from core.services.vault.crypto import KEY_FILE

log = get_logger("AutoUnseal")

class AutoUnsealManager:
    def __init__(self):
        # Wir hören nur noch auf den zentralen Systemstart
        bus.subscribe("system:started")(self.on_system_started)

    async def on_system_started(self, payload):
        """
        Wird gerufen, wenn der ModuleManager alle Module geladen hat.
        Wir prüfen jetzt aktiv den Zustand von Vault und Keyfile.
        """
        auto_key = os.getenv("LYNDRIX_MASTER_KEY")
        
        if not auto_key:
            log.info("ℹ️ Kein LYNDRIX_MASTER_KEY in ENV. Warte auf manuelle Eingabe in UI.")
            return

        # Ein kleiner Sicherheits-Sleep (2s), damit der Vault-Container 
        # und der VaultService Zeit haben, die Sockets zu öffnen.
        await asyncio.sleep(2)
        
        # LOGIK-ENTSCHEIDUNG:
        
        # 1. Fall: Das System ist komplett neu (Kein Keyfile da)
        if not os.path.exists(KEY_FILE):
            log.info("🪄 Frischer Vault erkannt (kein Keyfile). Starte AUTO-INIT...")
            bus.emit("vault:init_requested", {"key": auto_key})
        
        # 2. Fall: Vault wurde schon mal initialisiert (Keyfile existiert)
        else:
            log.info("🔑 Bestehendes Keyfile gefunden. Starte AUTO-UNSEAL...")
            bus.emit("vault:unseal_requested", {"key": auto_key})

auto_unseal_manager = AutoUnsealManager()