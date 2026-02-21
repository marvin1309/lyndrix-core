from sqlalchemy import Column, Integer, String, JSON
from core.bus import bus
from core.services.database.db_service import Base, db_instance
from core.security import bootstrap
from core.logger import get_logger

log = get_logger("AuthService")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    full_name = Column(String(100))
    email = Column(String(100))
    hashed_password = Column(String(255))
    roles = Column(JSON)

class AuthService:
    def __init__(self):
        bus.subscribe("db:connected")(self.initialize_iam)

    async def initialize_iam(self, payload):
        log.info("🔐 IAM Service: Starte Initialisierung...")
        try:
            Base.metadata.create_all(bind=db_instance.engine)
            log.debug("Datenbank-Tabellen für IAM geprüft/erstellt.")
            self.seed_admin()
            log.info("✅ IAM Service: Bereit.")
            bus.emit("iam:ready")
        except Exception as e:
            log.error(f"❌ IAM Service: Initialisierung fehlgeschlagen: {e}", exc_info=True)

    def seed_admin(self):
        if not db_instance.SessionLocal:
            log.warning("Seed abgebrochen: SessionLocal ist nicht bereit.")
            return
            
        with db_instance.SessionLocal() as session:
            log.debug("Prüfe auf existierenden Admin-User...")
            admin = session.query(User).filter(User.username == "admin").first()
            if not admin:
                log.info("🐣 Kein Admin gefunden. Erstelle Standard-Account...")
                try:
                    new_admin = User(
                        username="admin",
                        full_name="Lyndrix Administrator",
                        email="admin@lyndrix.local",
                        hashed_password=bootstrap.hash_password("admin"),
                        roles=["admin", "superadmin"]
                    )
                    session.add(new_admin)
                    session.commit()
                    log.info("✅ Admin-User erfolgreich erstellt (admin:admin)")
                except Exception as e:
                    log.error(f"❌ Fehler beim Admin-Seeding: {e}")
            else:
                log.debug("Admin-User existiert bereits. Überspringe Seeding.")

    def authenticate_user(self, username, password):
        """Prüft Anmeldedaten und protokolliert den Vorgang detailliert."""
        log.info(f"🔑 Login-Versuch für User: {username}")
        
        if not db_instance.SessionLocal:
            log.error("Login unmöglich: Datenbank-Session nicht verfügbar.")
            return None

        with db_instance.SessionLocal() as session:
            user = session.query(User).filter(User.username == username).first()
            
            if not user:
                log.warning(f"🚫 Login gescheitert: User '{username}' existiert nicht.")
                return None
            
            log.debug(f"User '{username}' gefunden. Prüfe Passwort-Hash...")
            if bootstrap.verify_password(password, user.hashed_password):
                log.info(f"✅ Login erfolgreich: {username} ({user.full_name})")
                return user
            
            log.warning(f"🚫 Login gescheitert: Passwort für '{username}' ist inkorrekt.")
            return None

auth_service = AuthService()