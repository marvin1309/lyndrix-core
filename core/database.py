import os
from sqlalchemy import create_engine, Column, Integer, String, JSON
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./lyndrix_core.db")
connect_args = {"check_same_thread": False} if "sqlite" in DATABASE_URL else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DynamicEntity(Base):
    __tablename__ = "dynamic_entities"
    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String, index=True)
    payload = Column(JSON)

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