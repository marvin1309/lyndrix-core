from nicegui import ui, app

def render_user_settings_card():
    """Wird in der Einstellungsseite aufgerufen."""
    user = app.storage.user
    with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 rounded-3xl !bg-white dark:!bg-zinc-900'):
        with ui.row().classes('items-center gap-3 mb-4'):
            ui.icon('account_circle', size='24px').classes('text-primary')
            ui.label('Benutzerprofil').classes('text-lg font-bold')
        
        ui.label(f"Benutzername: {user.get('username', 'Guest')}").classes('text-sm font-mono bg-slate-100 dark:bg-zinc-800 p-2 rounded w-full')
        
        ui.separator().classes('my-4')
        
        # User-spezifische Toggles
        ui.switch('Dark Mode manuell').bind_value(user, 'dark_mode')
        
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Passwort ändern', icon='lock').props('flat rounded size=sm')