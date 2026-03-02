import asyncio
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from core.bus import bus
from core.logger import get_logger
from config import settings

log = get_logger("Core:DatabaseService")
Base = declarative_base()

class DatabaseService:
    def __init__(self):
        self.engine = None
        self.SessionLocal = None
        self.is_connected = False
        bus.subscribe("vault:opened")(self.init_db_connection)

    async def init_db_connection(self, payload=None):
        log.info("DATABASE: Vault is open. Initializing engine...")
        try:
            # WICHTIG: connect_timeout auf 5 Sekunden setzen
            self.engine = create_engine(
                settings.DATABASE_URL, 
                pool_pre_ping=True,
                connect_args={'connect_timeout': 5} 
            )
            
            self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
            
            # Wir starten den Loop explizit als Task
            asyncio.create_task(self._connection_loop())
            
        except Exception as e:
            log.error(f"CRITICAL: Engine initialization failed: {e}")

    async def _connection_loop(self):
        log.info(f"CONNECT: Attempting connection to {settings.DB_HOST}...")
        loop = asyncio.get_event_loop()
        
        while not self.is_connected:
            try:
                # FIX: Wir führen den synchronen Connect in einem separaten Thread aus!
                # Das verhindert, dass die gesamte App einfriert.
                await loop.run_in_executor(None, self._check_db_sync)
                
                self.is_connected = True
                log.info("SUCCESS: Database connection established.")
                
                bus.emit("db:connected", {"status": "ready"})
                bus.emit("system:maintenance_mode", {"service": "db", "active": False})
                
                asyncio.create_task(self._watchdog())
                break 
                    
            except Exception as e:
                log.warning(f"RETRY: Database not reachable. Retrying in 5s... ({e})")
                await asyncio.sleep(5)

    def _check_db_sync(self):
        """Synchroner Helper-Check für den Executor-Thread."""
        with self.engine.connect() as conn:
            conn.execute(text("SELECT 1"))

    async def _watchdog(self):
        """Überwacht die Verbindung im Hintergrund."""
        loop = asyncio.get_event_loop()
        while self.is_connected:
            await asyncio.sleep(15)
            try:
                await loop.run_in_executor(None, self._check_db_sync)
            except Exception:
                log.error("LOST: Database connection timed out.")
                self.is_connected = False
                asyncio.create_task(self._connection_loop())
                break

db_instance = DatabaseService()