from core.auth.base import BaseAuthProvider
from core.database import SessionLocal, DynamicEntity
from core.security import bootstrap
from core.models import ENTITY_TYPE_USER
from typing import Optional, Dict
import logging

class LocalProvider(BaseAuthProvider):
    def __init__(self, app):
        self.app = app

    def get_provider_name(self) -> str:
        return "local"

    async def authenticate(self, credentials: Dict) -> Optional[Dict]:
        username = credentials.get("username")
        password = credentials.get("password")
        
        print(f"[Auth-Debug] Login-Versuch für User: '{username}'")

        with SessionLocal() as db:
            # Suche den User
            user_entity = db.query(DynamicEntity).filter(
                DynamicEntity.entity_type == ENTITY_TYPE_USER,
                DynamicEntity.payload['username'].as_string() == username
            ).first()

            if not user_entity:
                print(f"[Auth-Debug] ❌ User '{username}' nicht in der DB gefunden.")
                return None

            user_data = user_entity.payload
            print(f"[Auth-Debug] User gefunden. Prüfe Passwort-Hash...")
            
            stored_hash = user_data.get("hashed_password")
            
            # Passwort-Check via Argon2 (bootstrap.py)
            if bootstrap.verify_password(stored_hash, password):
                print(f"[Auth-Debug] ✅ Passwort korrekt für '{username}'")
                return {
                    "id": user_entity.id,
                    "username": user_data["username"],
                    "roles": user_data.get("roles", []),
                    "provider": self.get_provider_name()
                }
            else:
                print(f"[Auth-Debug] ❌ Passwort falsch für '{username}'")
                # Debug: Zeig mir den Hash-Anfang zum Vergleich
                if stored_hash:
                    print(f"[Auth-Debug] Hash beginnt mit: {stored_hash[:20]}...")
        
        return None