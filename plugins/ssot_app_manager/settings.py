from nicegui import ui
from core.database import SessionLocal, DynamicEntity

SETTINGS_TYPE = "PLUGIN_SETTINGS_SSOT_APP"

# --- DEFAULT WERTE (Ohne pat_token!) ---
DEFAULT_SETTINGS = {
    "gitlab_url": "https://gitlab.int.fam-feser.de",
    "group_path": "aac-application-definitions"
}

def get_settings():
    """Holt die Einstellungen aus der SQLite DB oder gibt Defaults zurück."""
    with SessionLocal() as db:
        record = db.query(DynamicEntity).filter(DynamicEntity.entity_type == SETTINGS_TYPE).first()
        if record and record.payload:
            return record.payload
    return DEFAULT_SETTINGS.copy()

def save_settings(new_settings):
    """Speichert die Einstellungen in der SQLite DB."""
    with SessionLocal() as db:
        record = db.query(DynamicEntity).filter(DynamicEntity.entity_type == SETTINGS_TYPE).first()
        if record:
            record.payload = new_settings
        else:
            db.add(DynamicEntity(entity_type=SETTINGS_TYPE, payload=new_settings))
        db.commit()

# ACHTUNG: Wir übergeben jetzt 'app' an die Funktion, um an den Vault zu kommen!
def render_settings_ui(app):
    current_state = get_settings()
    
    # Lokaler State nur für die UI, wird NICHT in SQLite gespeichert!
    vault_state = {"pat_token": ""}

    def apply_save():
        # 1. Normale Settings (URL, Pfad) in SQLite speichern
        save_settings(current_state)
        
        # 2. Token sicher im Vault speichern (falls einer eingetippt wurde)
        if vault_state["pat_token"]:
            try:
                app.state.vault.set_secret('lyndrix/gitlab_pat', vault_state["pat_token"])
                ui.notify('Settings & Vault-Token sicher gespeichert!', type='positive')
            except Exception as e:
                ui.notify(f'Fehler beim Speichern im Vault: {e}', type='negative')
        else:
            ui.notify('Settings gespeichert (Token unverändert im Vault)', type='info')

    with ui.column().classes('w-full gap-4 pt-2'):
        ui.label('Zugangsdaten für die GitLab Application Group.').classes('text-sm text-slate-500')
        
        ui.input('GitLab Base URL').bind_value(current_state, 'gitlab_url').classes('w-full').props('outlined dense')
        ui.input('Group Path').bind_value(current_state, 'group_path').classes('w-full').props('outlined dense')
        
        # Passwortfeld bindet jetzt an vault_state, nicht an current_state!
        ui.input('Personal Access Token (wird im Vault gespeichert)', password=True).bind_value(vault_state, 'pat_token').classes('w-full').props('outlined dense')
        
        with ui.row().classes('w-full justify-end mt-2'):
            ui.button('Speichern', on_click=apply_save, icon='save', color='primary').props('unelevated rounded size=sm')