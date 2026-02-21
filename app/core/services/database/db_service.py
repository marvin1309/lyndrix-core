from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from core.bus import bus
from core.logger import get_logger
import asyncio
import os

log = get_logger("DatabaseService")
Base = declarative_base()

class DatabaseService:
    def __init__(self):
        self.engine: any = None # Typ-Hint gegen IDE-Warnung
        self.SessionLocal = None
        self.is_connected = False
        self.db_url = None
        bus.subscribe("vault:opened")(self.init_db_connection)

    async def init_db_connection(self, payload):
        log.info("🗄️ Vault ist offen. Bereite Datenbank-Verbindung vor...")
        db_user = os.getenv("DB_USER", "admin")
        db_pass = os.getenv("DB_PASSWORD", "admin_pass")
        db_host = os.getenv("DB_HOST", "lyndrix-db-dev")
        db_name = os.getenv("DB_NAME", "lyndrix_db")
        self.db_url = f"mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}"
        
        self.engine = create_engine(self.db_url, pool_pre_ping=True)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        asyncio.create_task(self._connection_loop())

    async def _connection_loop(self):
        log.info("🔄 Starte Datenbank-Reconnect-Loop...")
        while not self.is_connected:
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
                self.is_connected = True
                log.info("✅ Verbindung zur MariaDB hergestellt!")
                bus.emit("db:connected", {"status": "ready"})
                bus.emit("system:maintenance_mode", {"service": "db", "active": False}) # LOCK LÖSCHEN
                asyncio.create_task(self._watchdog())
                break 
            except Exception as e:
                bus.emit("system:maintenance_mode", {
                    "service": "db",
                    "active": True, 
                    "title": "Datenbank Offline", 
                    "msg": "Die Verbindung zur MariaDB wird aufgebaut..."
                })
                await asyncio.sleep(5)

    async def _watchdog(self):
        while self.is_connected:
            await asyncio.sleep(10)
            if not self.engine: continue
            try:
                with self.engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                log.error(f"❌ Datenbankverbindung abgerissen: {e}")
                self.is_connected = False
                bus.emit("system:maintenance_mode", {
                    "service": "db", # WICHTIG: Service ID hier
                    "active": True, 
                    "title": "Datenbank verloren", 
                    "msg": "Verbindung unterbrochen. Reconnect läuft..."
                })
                asyncio.create_task(self._connection_loop())
                break

db_instance = DatabaseService()