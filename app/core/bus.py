import asyncio
import inspect
from core.logger import get_logger

class GlobalEventBus:
    def __init__(self):
        self.subscribers = {}
        self.log = get_logger("Core:EventBus")
        # Liste der Topics, die das INFO-Log nicht verstopfen sollen
        self._noise_topics = ["system:metrics_update"]
        # Liste der Topics, die sensible Daten enthalten (nicht loggen!)
        self._sensitive_topics = ["vault:unseal_requested", "vault:init_requested"]

    def subscribe(self, topic: str):
        """Ermöglicht die Nutzung als @bus.subscribe('topic') Decorator."""
        def decorator(callback):
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(callback)
            self.log.debug(f"SUBSCRIBE: New Subscriber registered for: {topic} ({callback.__name__})")
            return callback
        return decorator

    def emit(self, topic: str, payload: dict = None):
        """Sendet ein Event an alle Subscriber (Enterprise Format)."""
        if payload is None: 
            payload = {}
        
        # Metriken im Hintergrund lassen
        if topic == "system:metrics_update":
            self.log.debug(f"METRICS: {topic} | Payload: {payload}")
        elif topic in self._sensitive_topics:
            # Sensible Daten ausblenden!
            self.log.info(f"EVENT: {topic} | Data: [REDACTED]")
        else:
            # Professionelles Tagging statt Emojis
            self.log.info(f"EVENT: {topic} | Data: {payload}")
        
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        asyncio.create_task(callback(payload))
                    else:
                        callback(payload)
                except Exception as e:
                    self.log.error(f"ERROR: Error in callback for '{topic}': {e}", exc_info=True)

bus = GlobalEventBus()

