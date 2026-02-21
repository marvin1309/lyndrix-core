from core.database import SessionLocal, DynamicEntity

SETTINGS_TYPE = "PLUGIN_SETTINGS_DISCORD_NOTIFIER"

DEFAULT_SETTINGS = {
    "enabled": True,
    "bot_name": "Lyndrix Event Broker"
}

def get_settings():
    with SessionLocal() as db:
        record = db.query(DynamicEntity).filter(DynamicEntity.entity_type == SETTINGS_TYPE).first()
        if record and record.payload:
            return record.payload
    return DEFAULT_SETTINGS.copy()

def save_settings(new_settings):
    with SessionLocal() as db:
        record = db.query(DynamicEntity).filter(DynamicEntity.entity_type == SETTINGS_TYPE).first()
        if record:
            record.payload = new_settings
        else:
            db.add(DynamicEntity(entity_type=SETTINGS_TYPE, payload=new_settings))
        db.commit()