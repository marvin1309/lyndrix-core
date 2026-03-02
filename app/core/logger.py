import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from collections import deque

# Pfade
LOG_DIR = "/app/logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "lyndrix.log")

IS_DEBUG = os.getenv("LYNDRIX_DEBUG", "false").lower() == "true"
LOG_LEVEL = logging.DEBUG if IS_DEBUG else logging.INFO

# ENTERPRISE FORMATTING
# [Zeit] | [Level] | [Komponente (25 Zeichen)] | Nachricht
FORMAT_STR = "%(asctime)s | %(levelname)-8s | %(name)-25s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Globaler Speicher für UI-Logs (Die letzten 1000 Einträge)
# Wird von der UI abgefragt, um Logs pro Plugin zu filtern
log_capture_buffer = deque(maxlen=1000)

class EnterpriseFormatter(logging.Formatter):
    """Sorgt für absolut sauberes Alignment ohne Emoji-Varianz."""
    def format(self, record):
        # Falls doch mal ein Emoji durchrutscht, hier könnte man es filtern
        return super().format(record)

class RingBufferHandler(logging.Handler):
    """Speichert Logs im RAM für die UI-Anzeige."""
    def emit(self, record):
        log_entry = self.format(record)
        log_capture_buffer.append((record.name, record.levelname, log_entry))

def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Formatter Instanz
    formatter = EnterpriseFormatter(FORMAT_STR, datefmt="%H:%M:%S")

    # 1. STREAM HANDLER (Konsole)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(LOG_LEVEL)
    root_logger.addHandler(console_handler)

    # 2. FILE HANDLER
    file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10*1024*1024, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)

    # 3. MEMORY HANDLER (Für UI Log-Viewer)
    memory_handler = RingBufferHandler()
    memory_handler.setFormatter(formatter)
    memory_handler.setLevel(logging.DEBUG)
    root_logger.addHandler(memory_handler)

    # Externe Logger dämpfen
    silent_loggers = ["uvicorn", "uvicorn.access", "sqlalchemy.engine", "hvac", "urllib3", "nicegui"]
    for name in silent_loggers:
        l = logging.getLogger(name)
        l.setLevel(logging.WARNING if not IS_DEBUG else logging.DEBUG)
        l.propagate = False
        l.handlers = root_logger.handlers

    logging.info(f"LOGGING: Initialized with level {'DEBUG' if IS_DEBUG else 'INFO'}")

def get_logger(name: str):
    """Factory Methode für konsistente Logger-Namen."""
    return logging.getLogger(name)