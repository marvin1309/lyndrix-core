import asyncio
import inspect
from core.logger import get_logger

class GlobalEventBus:
    def __init__(self):
        self.subscribers = {}
        self.log = get_logger("LyndrixBus")
        # Liste der Topics, die das INFO-Log nicht verstopfen sollen
        self._noise_topics = ["system:metrics_update"]

    def subscribe(self, topic: str):
        """Ermöglicht die Nutzung als @bus.subscribe('topic') Decorator."""
        def decorator(callback):
            if topic not in self.subscribers:
                self.subscribers[topic] = []
            self.subscribers[topic].append(callback)
            self.log.debug(f"👂 New Subscriber registered for: {topic} ({callback.__name__})")
            return callback
        return decorator

    def emit(self, topic: str, payload: dict = None):
        """Sendet ein Event an alle Subscriber."""
        if payload is None: 
            payload = {}
        
        # --- LOG-FILTER LOGIK ---
        if topic in self._noise_topics:
            # Metriken etc. nur im DEBUG (taucht in Konsole bei INFO nicht auf)
            self.log.debug(f"📡 [EVENT] {topic} | Payload: {payload}")
        else:
            # Wichtige System-Events weiterhin als INFO
            self.log.info(f"📡 [EVENT] {topic} | Payload: {payload}")
        # ------------------------
        
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        asyncio.create_task(callback(payload))
                    else:
                        callback(payload)
                except Exception as e:
                    self.log.error(f"❌ Error in callback for '{topic}': {e}", exc_info=True)

bus = GlobalEventBus()