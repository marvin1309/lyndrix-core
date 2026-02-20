import os
from nicegui import ui
from core.database import SessionLocal, DynamicEntity

SETTINGS_TYPE = "PLUGIN_SETTINGS_SECRETS_MANAGER"

# Prüfen, ob wir im Docker-Container laufen
IS_DOCKER = os.path.exists('/.dockerenv')

def get_settings():
    """
    Holt Einstellungen mit folgender Priorität:
    1. Umgebungsvariablen (.env / Docker env)
    2. Datenbank (was in der UI gespeichert wurde)
    3. Standardwerte (Fallback)
    """
    # 1. Standardwerte definieren
    default_vault_url = "http://vault:8200" if IS_DOCKER else "http://127.0.0.1:8200"
    
    defaults = {
        "vault_url": os.getenv("VAULT_URL", default_vault_url),
        "auth_method": os.getenv("VAULT_AUTH_METHOD", "userpass"),
        "username": os.getenv("VAULT_USER", "admin"),
        "password": os.getenv("VAULT_PASSWORD", "mein_super_sicheres_passwort"),
        "mount_point": os.getenv("VAULT_MOUNT", "secret")
    }

    # 2. Aus Datenbank laden (überschreibt Defaults, wenn vorhanden)
    with SessionLocal() as db:
        record = db.query(DynamicEntity).filter(DynamicEntity.entity_type == SETTINGS_TYPE).first()
        if record and record.payload:
            # Wir mergen die DB-Werte in unsere Defaults
            defaults.update(record.payload)
            
    return defaults

def save_settings(new_settings):
    with SessionLocal() as db:
        record = db.query(DynamicEntity).filter(DynamicEntity.entity_type == SETTINGS_TYPE).first()
        if record:
            record.payload = new_settings
        else:
            db.add(DynamicEntity(entity_type=SETTINGS_TYPE, payload=new_settings))
        db.commit()

def render_settings_ui(app):
    current_state = get_settings()

    def apply_save():
        save_settings(current_state)
        # Verbinde Vault nach dem Speichern sofort neu!
        if hasattr(app.state, 'vault'):
            app.state.vault.connect()
        ui.notify('Vault Settings gespeichert und verbunden!', type='positive')

    with ui.column().classes('w-full gap-4 pt-2'):
        ui.label('HashiCorp Vault / OpenBao Connection').classes('text-sm text-slate-500')
        
        # Info-Badge wenn Umgebungsvariablen aktiv sind
        if os.getenv("VAULT_URL"):
            ui.badge('Gesteuert durch .env / System Environment', color='orange').classes('self-start')

        ui.input('Vault URL').bind_value(current_state, 'vault_url').classes('w-full').props('outlined dense')
        ui.input('KV Mount Point (z.B. secret)').bind_value(current_state, 'mount_point').classes('w-full').props('outlined dense')
        ui.select(['userpass'], label='Auth Method').bind_value(current_state, 'auth_method').classes('w-full').props('outlined dense')
        
        with ui.row().classes('w-full gap-4 flex-nowrap'):
            ui.input('Username').bind_value(current_state, 'username').classes('w-1/2').props('outlined dense')
            ui.input('Password', password=True).bind_value(current_state, 'password').classes('w-1/2').props('outlined dense')
        
        with ui.row().classes('w-full justify-end mt-2'):
            ui.button('Verbinden & Speichern', on_click=apply_save, icon='security', color='primary').props('unelevated rounded size=sm')