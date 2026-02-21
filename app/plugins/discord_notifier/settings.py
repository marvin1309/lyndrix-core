from nicegui import ui, app
from . import config

def render():
    current_state = config.get_settings()
    vault_state = {"webhook_url": ""}

    def apply_save():
        config.save_settings(current_state)
        
        if vault_state["webhook_url"]:
            try:
                app.state.vault.set_secret('lyndrix/discord_webhook', vault_state["webhook_url"])
                ui.notify('Settings & Webhook sicher im Vault gespeichert!', type='positive')
            except Exception as e:
                ui.notify(f'Fehler beim Speichern im Vault: {e}', type='negative')
        else:
            ui.notify('Settings gespeichert (Webhook unverändert)', type='info')

    with ui.column().classes('w-full gap-4 pt-2'):
        ui.label('Konfiguration für System-Benachrichtigungen.').classes('text-sm text-slate-500')
        
        with ui.row().classes('w-full items-center gap-4'):
            ui.switch('Benachrichtigungen aktivieren').bind_value(current_state, 'enabled').props('color=primary')
            ui.input('Bot Name').bind_value(current_state, 'bot_name').classes('flex-grow').props('outlined dense')
        
        ui.input('Discord Webhook URL (wird im Vault gespeichert)', password=True).bind_value(vault_state, 'webhook_url').classes('w-full').props('outlined dense')
        
        with ui.row().classes('w-full justify-end mt-2'):
            ui.button('Speichern', on_click=apply_save, icon='save', color='primary').props('unelevated rounded size=sm')