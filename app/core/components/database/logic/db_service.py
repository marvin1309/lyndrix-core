from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from core.bus import bus
from core.logger import get_logger
import asyncio

# WICHTIG: Settings importieren
from config import settings

log = get_logger("DatabaseService")
Base = declarative_base()

class DatabaseService:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.is_connected = False
        # Wir abonnieren das Event, wenn der Vault bereit ist
        bus.subscribe("vault:opened")(self.init_db_connection)

    async def init_db_connection(self, payload=None):
        log.info("🗄️ Vault ist offen. Bereite Datenbank-Verbindung vor...")
        
        try:
            # Debug-Log um zu sehen was wirklich geladen wurde
            log.debug(f"Konfiguration geladen: Host={settings.DB_HOST}, User={settings.DB_USER}, DB={settings.DB_NAME}")
            
            self.db_url = settings.DATABASE_URL
            log.info(f"🔗 Verbinde mit: mysql+pymysql://{settings.DB_USER}:***@{settings.DB_HOST}/{settings.DB_NAME}")
            
            self.engine = create_engine(
                self.db_url, 
                pool_pre_ping=True,
                echo=False # Auf True setzen für SQL-Logs
            )
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            asyncio.create_task(self._connection_loop())
            
        except Exception as e:
            log.error(f"💥 Kritischer Fehler bei DB-Initialisierung: {e}")
                

    async def _connection_loop(self):
        log.info(f"🔄 Reconnect-Loop: Versuche Verbindung zu {settings.DB_HOST}...")
        while not self.is_connected:
            try:
                if self.engine:
                    with self.engine.connect() as conn:
                        conn.execute(text("SELECT 1"))
                    
                    self.is_connected = True
                    log.info("✅ Verbindung zur MariaDB hergestellt!")
                    
                    bus.emit("db:connected", {"status": "ready"})
                    bus.emit("system:maintenance_mode", {"service": "db", "active": False})
                    
                    # Watchdog starten, um Abstürze während der Laufzeit zu fangen
                    asyncio.create_task(self._watchdog())
                    break 
                    
            except Exception as e:
                log.warning(f"⏳ Datenbank noch nicht erreichbar... ({e})")
                bus.emit("system:maintenance_mode", {
                    "service": "db",
                    "active": True, 
                    "title": "Datenbank Offline", 
                    "msg": "Warte auf MariaDB unter " + settings.DB_HOST
                })
                await asyncio.sleep(5)

    async def _watchdog(self):
        """Prüft alle 10 Sekunden, ob die DB noch da ist."""
        while self.is_connected:
            await asyncio.sleep(10)
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                log.error(f"❌ Datenbankverbindung verloren: {e}")
                self.is_connected = False
                bus.emit("system:maintenance_mode", {
                    "service": "db",
                    "active": True, 
                    "title": "Datenbank verloren", 
                    "msg": "Reconnect läuft..."
                })
                asyncio.create_task(self._connection_loop())
                break

db_instance = DatabaseService()