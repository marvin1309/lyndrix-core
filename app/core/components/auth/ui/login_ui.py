from nicegui import ui, app
from core.logger import get_logger
# FIX 1: 'app.' Präfixe entfernt
from core.components.database.logic.db_service import db_instance
from core.components.auth.logic.auth_service import User
# FIX 2: Von bootstrap auf unsere neue hashing.py umgestellt
from core.components.auth.logic.hashing import verify_password

log = get_logger("UI:Login")

def render_login_page():
    # Hintergrund-Styling
    ui.query('body').style('background-color: #09090b;') 

    with ui.card().classes('absolute-center shadow-2xl p-8 rounded-3xl border border-zinc-800 bg-zinc-900 text-zinc-100 w-full max-w-md'):
        with ui.column().classes('items-center w-full gap-4'):
            ui.icon('account_circle', size='64px').classes('text-indigo-500 mb-2')
            ui.label('Lyndrix Login').classes('text-2xl font-bold tracking-tight')
            
            user_input = ui.input('Benutzername').props('dark outlined autofocus').classes('w-full')
            pass_input = ui.input('Passwort').props('dark outlined password').classes('w-full')

            async def try_login():
                if not db_instance.SessionLocal:
                    ui.notify('Datenbank nicht bereit!', type='negative')
                    return

                with db_instance.SessionLocal() as session:
                    user = session.query(User).filter(User.username == user_input.value).first()
                    
                    # FIX 3: Nutzt jetzt die neue verify_password Funktion
                    # WICHTIG: Erst der Hash aus der DB, dann das User-Passwort
                    if user and verify_password(user.hashed_password, pass_input.value):
                        app.storage.user.update({
                            'authenticated': True,
                            'username': user.username,
                            'full_name': user.full_name,
                            'roles': user.roles,
                            'email': user.email
                        })
                        ui.notify(f'Willkommen zurück, {user.full_name}!', type='positive')
                        ui.navigate.to('/dashboard')
                    else:
                        ui.notify('Anmeldung fehlgeschlagen: Falscher User oder Passwort', type='negative')

            ui.button('Einloggen', on_click=try_login).classes('w-full py-4 bg-indigo-600 rounded-xl font-bold')
            
            with ui.row().classes('items-center gap-2 opacity-50 mt-2'):
                ui.label('Standard: admin / lyndrix').classes('text-[10px] uppercase tracking-widest')