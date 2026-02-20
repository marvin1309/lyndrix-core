import os
import time
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.exc import OperationalError # <--- WICHTIG: Das fängt den MariaDB Fehler ab!

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./lyndrix_core.db")

# ==========================================
# ROBUSTER DATENBANK-AUFBAU (Warte auf DB)
# ==========================================
def get_engine_with_retry(url, retries=15, delay=3): # <--- Retries leicht erhöht
    """Versucht sich mit der Datenbank zu verbinden und wartet, falls sie noch nicht da ist."""
    connect_args = {"check_same_thread": False} if "sqlite" in url else {}
    
    # 1. Engine Objekt initial erstellen (Das löst noch keine echte Netzwerkverbindung aus)
    engine = create_engine(url, connect_args=connect_args, pool_pre_ping=True)
    
    for i in range(retries):
        try:
            # 2. HIER wird die echte Netzwerk-Verbindung erzwungen!
            with engine.connect() as conn:
                print(f"\n[Database] ✅ Verbindung zur Datenbank erfolgreich hergestellt!\n")
                return engine
                
        except OperationalError as e:
            # Dies fängt den SQLAlchemy "Connection Refused" Fehler ab
            print(f"[Database] ⏳ Warte auf MariaDB... (Versuch {i+1}/{retries})")
            time.sleep(delay)
        except Exception as e:
            # Für alle anderen, generischen Fehler
            print(f"[Database] ⏳ Warte auf Datenbank... (Versuch {i+1}/{retries}) - Fehler: {e.__class__.__name__}")
            time.sleep(delay)
            
    raise Exception(f"Konnte nach {retries} Versuchen keine Verbindung zur Datenbank aufbauen!")

# 1. Engine mit der Warteschleife starten
engine = get_engine_with_retry(DATABASE_URL)

# 2. Session und Base initialisieren
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 3. Tabellen definieren
class DynamicEntity(Base):
    __tablename__ = "dynamic_entities"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), index=True) 
    payload = Column(JSON)

# 4. Tabellen erstellen
Base.metadata.create_all(bind=engine)

# ==========================================
# GLOBALE HELPER FÜR ALLE PLUGINS
# ==========================================
def get_all_records(entity_type: str):
    """Holt alle Datensätze eines bestimmten Typs und packt die ID ins Dictionary."""
    with SessionLocal() as db:
        records = db.query(DynamicEntity).filter(DynamicEntity.entity_type == entity_type).all()
        result = []
        for r in records:
            data = r.payload.copy() if r.payload else {}
            data['id'] = r.id
            result.append(data)
        return result