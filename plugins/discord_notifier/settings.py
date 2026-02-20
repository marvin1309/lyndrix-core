from nicegui import ui
from core.database import SessionLocal, DynamicEntity

SETTINGS_TYPE = "PLUGIN_SETTINGS_DISCORD_NOTIFIER"

# Unkritische Standard-Einstellungen für die Datenbank
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

def render_settings_ui(app):
    current_state = get_settings()
    
    # Lokaler State für das UI-Feld (wird NICHT in SQLite gespeichert)
    vault_state = {"webhook_url": ""}

    def apply_save():
        save_settings(current_state)
        
        # Webhook im Vault speichern, falls etwas eingegeben wurde
        if vault_state["webhook_url"]:
            try:
                # Wir legen es unter 'lyndrix/discord_webhook' im Vault ab
                app.state.vault.set_secret('lyndrix/discord_webhook', vault_state["webhook_url"])
                ui.notify('Settings & Webhook sicher im Vault gespeichert!', type='positive')
            except Exception as e:
                ui.notify(f'Fehler beim Speichern im Vault: {e}', type='negative')
        else:
            ui.notify('Settings gespeichert (Webhook unverändert im Vault)', type='info')

    with ui.column().classes('w-full gap-4 pt-2'):
        ui.label('Konfiguration für System-Benachrichtigungen.').classes('text-sm text-slate-500')
        
        with ui.row().classes('w-full items-center gap-4'):
            ui.switch('Benachrichtigungen aktivieren').bind_value(current_state, 'enabled').props('color=primary')
            ui.input('Bot Name').bind_value(current_state, 'bot_name').classes('flex-grow').props('outlined dense')
        
        # Webhook Input (Maskiert wie ein Passwort, weil es ein Secret ist)
        ui.input('Discord Webhook URL (wird im Vault gespeichert)', password=True).bind_value(vault_state, 'webhook_url').classes('w-full').props('outlined dense')
        
        with ui.row().classes('w-full justify-end mt-2'):
            ui.button('Speichern', on_click=apply_save, icon='save', color='primary').props('unelevated rounded size=sm')