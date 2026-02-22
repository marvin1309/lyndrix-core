import asyncio
from core.bus import bus
from core.logger import get_logger
from core.modules.manager import module_manager

log = get_logger("BootService")

class BootService:
    def __init__(self):
        self.is_booting = True
        bus.subscribe("iam:ready")(self.on_core_ready)

    async def on_core_ready(self, payload):
        log.info("🚀 Alle Kernsysteme (Vault, DB, IAM) sind online.")
        log.info("📦 Lade System-Module und Plugins...")
        
        module_manager.load_all()
        
        await asyncio.sleep(0.5)
        self.is_booting = False
        log.info("✅ Boot-Sequenz abgeschlossen. System freigegeben.")
        
        # NEU: Das Signal an alle interessierten Plugins senden
        bus.emit("system:boot_complete", {"status": "success"})

boot_service = BootService()