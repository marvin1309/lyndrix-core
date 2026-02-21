import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# Pfade und Basis-Konfiguration
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "lyndrix.log")

# --- ENV STEUERUNG ---
# Wir holen uns die Variable und setzen Defaults
# LYNDRIX_DEBUG=true -> Volles Rohr (DEBUG)
# LYNDRIX_DEBUG=false -> Sauberer Betrieb (INFO)
IS_DEBUG = os.getenv("LYNDRIX_DEBUG", "false").lower() == "true"
LOG_LEVEL = logging.DEBUG if IS_DEBUG else logging.INFO

FORMATTER = logging.Formatter(
    "%(asctime)s | %(levelname)-7s | %(name)-15s | %(message)s",
    datefmt="%H:%M:%S" 
)

class LogNoiseFilter(logging.Filter):
    """Filtert WebSocket-Müll aus der Konsole, außer wir sind im Debug-Modus."""
    def filter(self, record):
        if IS_DEBUG:
            return True # Im Debug-Modus wollen wir alles sehen!
            
        noise_keywords = ["WebSocket", "socket.io", "connection open", "connection closed", "/socket.io/"]
        return not any(keyword in record.getMessage() for keyword in noise_keywords)

def setup_logging():
    # 1. Den Root-Logger (Python Basis) konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Root immer auf DEBUG, Handler filtern dann

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 2. DOCKER HANDLER (Konsole)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    # Hier greift die Steuerung über die ENV Var!
    console_handler.setLevel(LOG_LEVEL)
    console_handler.addFilter(LogNoiseFilter()) 
    root_logger.addHandler(console_handler)

    # 3. FILE HANDLER
    # In der Datei speichern wir IMMER alles (DEBUG), egal was in der ENV steht
    # Das ist dein Sicherheitsnetz für die UI-Log-Anzeige
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5)
    file_handler.setFormatter(FORMATTER)
    file_handler.setLevel(logging.DEBUG) 
    root_logger.addHandler(file_handler)

    # 4. DRITTANBIETER LOGS (Uvicorn, etc.)
    # Wenn IS_DEBUG=false, schalten wir Uvicorn etwas leiser
    uvicorn_level = logging.DEBUG if IS_DEBUG else logging.WARNING
    for l_name in ["uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"]:
        l = logging.getLogger(l_name)
        l.setLevel(uvicorn_level)
        l.handlers = root_logger.handlers
        l.propagate = False 

    logging.info(f"✨ Lyndrix Logging initialisiert (Level: {'DEBUG' if IS_DEBUG else 'INFO'})")

def get_logger(name: str):
    return logging.getLogger(name)