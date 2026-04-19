import os
import logging
from core.bus import bus
from core.logger import get_logger
from core.components.database.logic.db_service import Base, db_instance
from .hashing import hash_password, verify_password
from .models import User

log = get_logger("Core:AuthService")

# Environment-backed bootstrap credentials
ADMIN_USERNAME = os.getenv("LYNDRIX_ADMIN_USER", "admin")
ADMIN_PASSWORD = os.getenv("LYNDRIX_ADMIN_PASSWORD", "lyndrix")
ADMIN_EMAIL = os.getenv("LYNDRIX_ADMIN_EMAIL", "admin@lyndrix.local")
BOT_USERNAME = os.getenv("LYNDRIX_BOT_USER", "bot")
BOT_PASSWORD = os.getenv("LYNDRIX_BOT_PASSWORD", "lyndrix-bot")

# Warn if insecure defaults are in use
_warn_logger = logging.getLogger("Core:AuthService")


class AuthService:
    def __init__(self):
        bus.subscribe("db:connected")(self.initialize_iam)

    async def initialize_iam(self, payload):
        log.info("IAM: Starting initialization...")
        try:
            Base.metadata.create_all(bind=db_instance.engine)
            log.debug("DB: IAM tables checked/created.")
            self._seed_users()
            log.info("SUCCESS: IAM Service ready.")
            bus.emit("iam:ready")
        except Exception as e:
            log.error(f"ERROR: IAM Service initialization failed: {e}", exc_info=True)

    def _seed_users(self):
        """Seeds admin and bot accounts from environment or defaults."""
        if not db_instance.SessionLocal:
            log.warning("SEED: Aborted, SessionLocal not ready.")
            return

        with db_instance.SessionLocal() as session:
            self._seed_or_update_user(session, ADMIN_USERNAME, ADMIN_PASSWORD, "Lyndrix Administrator", ADMIN_EMAIL, ["admin", "superadmin"])
            self._seed_or_update_user(session, BOT_USERNAME, BOT_PASSWORD, "Lyndrix Bot", f"{BOT_USERNAME}@lyndrix.local", ["bot"])

        # Emit warnings for insecure defaults
        if ADMIN_PASSWORD == "lyndrix":
            log.warning("SECURITY: Admin is using DEFAULT password. Set LYNDRIX_ADMIN_PASSWORD for production.")
        if BOT_PASSWORD == "lyndrix-bot":
            log.warning("SECURITY: Bot is using DEFAULT password. Set LYNDRIX_BOT_PASSWORD for production.")

    def _seed_or_update_user(self, session, username: str, password: str, full_name: str, email: str, roles: list):
        """Creates user if missing. Updates password if environment differs from stored hash."""
        user = session.query(User).filter(User.username == username).first()
        if not user:
            log.info(f"CREATE: Creating user '{username}'...")
            try:
                new_user = User(
                    username=username,
                    full_name=full_name,
                    email=email,
                    hashed_password=hash_password(password),
                    roles=roles
                )
                session.add(new_user)
                session.commit()
                log.info(f"SUCCESS: User '{username}' created.")
            except Exception as e:
                log.error(f"ERROR: User seeding failed for '{username}': {e}", exc_info=True)
                session.rollback()
        else:
            # Update password if env var changed (allows CI/CD credential rotation)
            if not verify_password(str(user.hashed_password), password):
                user.hashed_password = hash_password(password)
                session.commit()
                log.info(f"UPDATE: Password for '{username}' updated from environment.")

    def authenticate_user(self, username: str, password: str):
        """Verifies credentials and returns the User object or None."""
        log.info(f"AUTH: Login attempt for user: {username}")

        if not db_instance.SessionLocal:
            log.error("AUTH: Login impossible: Database session unavailable.")
            return None

        with db_instance.SessionLocal() as session:
            user = session.query(User).filter(User.username == username).first()

            if not user:
                log.warning(f"AUTH: Login failed: User '{username}' does not exist.")
                return None

            if verify_password(str(user.hashed_password), password):
                log.info(f"SUCCESS: Login successful: {username} ({user.full_name})")
                return user

            log.warning(f"AUTH: Login failed: Incorrect password for '{username}'.")
            return None


auth_service = AuthService()