import psutil
import asyncio
from core.bus import bus
from core.logger import get_logger

log = get_logger("MonitorService")

class MonitorService:
    def __init__(self):
        self.stats = {'cpu': 0, 'ram': 0, 'disk': 0}
        bus.subscribe("system:started")(self.start_monitoring)

    async def start_monitoring(self, payload):
        log.info("📊 Starte System-Monitoring Loop...")
        while True:
            self.stats.update({
                'cpu': psutil.cpu_percent(),
                'ram': psutil.virtual_memory().percent,
                'disk': psutil.disk_usage('/').percent
            })
            bus.emit("system:metrics_update", self.stats)
            await asyncio.sleep(2)

monitor_service = MonitorService()