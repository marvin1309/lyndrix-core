from core.database import SessionLocal, DynamicEntity
from core.security import bootstrap
from core.models import ENTITY_TYPE_USER

def seed_initial_admin():
    with SessionLocal() as db:
        user_count = db.query(DynamicEntity).filter(DynamicEntity.entity_type == ENTITY_TYPE_USER).count()
        
        if user_count == 0:
            print("[Auth-Seeder] 🌱 Erstelle initialen Admin-User...")
            admin_pw_hash = bootstrap.hash_password("admin")
            
            admin_payload = {
                "username": "admin",
                "email": "admin@lyndrix.local",
                "full_name": "Lyndrix Administrator",
                "hashed_password": admin_pw_hash, # Hier muss der Argon2-String rein
                "is_active": True,
                "roles": ["admin", "superadmin"],
                "external_identities": {}
            }
            
            new_user = DynamicEntity(entity_type=ENTITY_TYPE_USER, payload=admin_payload)
            db.add(new_user)
            db.commit()
            print("[Auth-Seeder] ✅ Admin-User 'admin' mit PW 'admin' angelegt.")