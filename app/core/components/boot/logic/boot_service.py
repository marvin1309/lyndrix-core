import asyncio
from core.bus import bus
from core.logger import get_logger


log = get_logger("Core:BootService")

class BootService:
    def __init__(self):
        self.is_booting = True
        bus.subscribe("iam:ready")(self.on_core_ready)
        
    async def on_core_ready(self, payload):
        log.info("STARTUP: All core systems (Vault, DB, IAM) are online.")
        log.info("LOAD: Loading system modules and plugins...")
        
        # ---------------------------------------------------------
        # LOKALER IMPORT: Löst den Zirkelbezug auf!
        # Wird erst ausgeführt, wenn die Funktion wirklich läuft.
        # ---------------------------------------------------------
        from core.components.plugins.logic.manager import module_manager        
        module_manager.load_all()
        
        await asyncio.sleep(0.5)
        self.is_booting = False
        log.info("SUCCESS: Boot sequence completed. System released.")
        
        # NEU: Das Signal an alle interessierten Plugins senden
        bus.emit("system:boot_complete", {"status": "success"})

boot_service = BootService()