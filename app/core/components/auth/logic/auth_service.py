from sqlalchemy import Column, Integer, String, JSON
from core.bus import bus
from core.logger import get_logger
from core.components.database.logic.db_service import Base, db_instance
from .hashing import hash_password, verify_password

log = get_logger("Core:AuthService")

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
        log.info("IAM: Starting initialization...")
        try:
            Base.metadata.create_all(bind=db_instance.engine)
            log.debug("DB: IAM tables checked/created.")
            self.seed_admin()
            log.info("SUCCESS: IAM Service ready.")
            bus.emit("iam:ready")
        except Exception as e:
            log.error(f"ERROR: IAM Service initialization failed: {e}", exc_info=True)

    def seed_admin(self):
        if not db_instance.SessionLocal:
            log.warning("SEED: Aborted, SessionLocal not ready.")
            return
            
        with db_instance.SessionLocal() as session:
            log.debug("CHECK: Checking for existing admin user...")
            admin = session.query(User).filter(User.username == "admin").first()
            if not admin:
                log.info("CREATE: No admin found. Creating default account...")
                try:
                    new_admin = User(
                        username="admin",
                        full_name="Lyndrix Administrator",
                        email="admin@lyndrix.local",
                        hashed_password=hash_password("admin"),
                        roles=["admin", "superadmin"]
                    )
                    session.add(new_admin)
                    session.commit()
                    log.info("SUCCESS: Admin user created successfully (admin:admin)")
                except Exception as e:
                    log.error(f"ERROR: Admin seeding failed: {e}", exc_info=True)
            else:
                log.debug("SKIP: Admin user already exists.")

    def authenticate_user(self, username, password):
        """Prüft Anmeldedaten und protokolliert den Vorgang detailliert."""
        log.info(f"AUTH: Login attempt for user: {username}")
        
        if not db_instance.SessionLocal:
            log.error("AUTH: Login impossible: Database session unavailable.")
            return None

        with db_instance.SessionLocal() as session:
            user = session.query(User).filter(User.username == username).first()
            
            if not user:
                log.warning(f"AUTH: Login failed: User '{username}' does not exist.")
                return None
            
            log.debug(f"AUTH: User '{username}' found. Verifying password hash...")
            
            # WICHTIG: Erst der Hash aus der DB, dann das eingegebene Passwort
            if verify_password(str(user.hashed_password), password):
                log.info(f"SUCCESS: Login successful: {username} ({user.full_name})")
                return user
            
            log.warning(f"AUTH: Login failed: Incorrect password for '{username}'.")
            return None

auth_service = AuthService()