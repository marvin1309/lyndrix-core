import logging
import os
import sys
from logging.handlers import RotatingFileHandler

# ==========================================
# 1. KONFIGURATION & PFADE
# ==========================================
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "lyndrix.log")

# Steuerung über Umgebungsvariable
IS_DEBUG = os.getenv("LYNDRIX_DEBUG", "false").lower() == "true"
LOG_LEVEL = logging.DEBUG if IS_DEBUG else logging.INFO

# DEFINITION DER SPALTENBREITE (Wichtig für das Alignment!)
# %-8s  -> Reserviert 8 Zeichen für das Level (z.B. INFO, CRITICAL)
# %-28s -> Reserviert 28 Zeichen für den Namen (z.B. Plugin:Discord Notifier)
FORMAT_STR = "%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s"
DATE_FORMAT = "%H:%M:%S"

FORMATTER = logging.Formatter(FORMAT_STR, datefmt=DATE_FORMAT)

# ==========================================
# 2. FILTER FÜR SAUBERE KONSOLEN
# ==========================================
class LogNoiseFilter(logging.Filter):
    """
    Unterdrückt unnötigen Spam in der Konsole, 
    damit man die wichtigen System-Events sieht.
    """
    def filter(self, record):
        if IS_DEBUG:
            return True # Im Debug-Modus alles zeigen
            
        # Diese Begriffe fliegen aus der Konsole (INFO-Level) raus
        noise_keywords = [
            "WebSocket", "socket.io", "connection open", 
            "connection closed", "/socket.io/", 
            "system:metrics_update", "heartbeat",
            "POST /api/v1/login", "GET /static"
        ]
        msg = record.getMessage()
        return not any(keyword in msg for keyword in noise_keywords)

# ==========================================
# 3. SETUP FUNKTION
# ==========================================
def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Basis immer auf DEBUG

    # Alte Handler entfernen (wichtig für Hot-Reload)
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # --- A. KONSOLEN HANDLER (Docker / Terminal) ---
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(FORMATTER)
    console_handler.setLevel(LOG_LEVEL) # INFO oder DEBUG je nach ENV
    console_handler.addFilter(LogNoiseFilter()) 
    root_logger.addHandler(console_handler)

    # --- B. DATEI HANDLER (UI Log-Viewer / Dauerarchiv) ---
    # Hier speichern wir IMMER alles im DEBUG, um Fehler später finden zu können
    file_handler = RotatingFileHandler(
        LOG_FILE, 
        maxBytes=10*1024*1024, # 10 MB pro Datei
        backupCount=5,         # Behalte die letzten 5 Logs
        encoding="utf-8"
    )
    file_handler.setFormatter(FORMATTER)
    file_handler.setLevel(logging.DEBUG) 
    root_logger.addHandler(file_handler)

    # --- C. EXTERNE BIBLIOTHEKEN STUMM SCHALTEN ---
    # Wir schalten Bibliotheken, die zu viel labern, eine Stufe leiser
    external_loggers = {
        "uvicorn": logging.WARNING,
        "uvicorn.error": logging.WARNING,
        "uvicorn.access": logging.CRITICAL, # Zugriff-Logs fast komplett aus
        "sqlalchemy.engine": logging.WARNING,
        "hvac": logging.INFO,               # Vault Client
        "urllib3": logging.INFO,            # HTTP Client
        "nicegui": logging.WARNING          # UI Framework
    }

    for logger_name, level in external_loggers.items():
        ext_logger = logging.getLogger(logger_name)
        ext_logger.setLevel(level if not IS_DEBUG else logging.DEBUG)
        ext_logger.handlers = root_logger.handlers
        ext_logger.propagate = False 

    logging.info(f"✨ Lyndrix Logging initialisiert (Level: {'DEBUG' if IS_DEBUG else 'INFO'})")

def get_logger(name: str):
    """Factory Methode für konsistente Logger-Namen."""
    return logging.getLogger(name)