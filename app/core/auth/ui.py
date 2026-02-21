from nicegui import ui, app as nicegui_app
import asyncio

def create_login_page(fastapi_app):
    @ui.page('/login')
    def login():
        # Luxuriöser Hintergrund (Tiefes Slate/Schwarz mit zentralem Leuchten)
        ui.query('body').classes('bg-gradient-to-br from-slate-900 via-zinc-900 to-black min-h-screen flex items-center justify-center')
        ui.html('<div class="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-indigo-500/10 via-transparent to-transparent pointer-events-none"></div>')

        if nicegui_app.storage.user.get('authenticated', False):
            ui.navigate.to('/')
            return

        # Hauptkarte mit feinem Rand, starkem Blur und farbigem Schatten (Glow)
        with ui.card().classes('w-full max-w-md p-10 shadow-[0_0_60px_-15px_rgba(79,70,229,0.3)] rounded-[2rem] border border-white/5 bg-zinc-900/60 backdrop-blur-xl flex flex-col items-center'):
            
            # Header Bereich mit leuchtendem Icon
            ui.icon('lock_person', size='48px').classes('text-indigo-400 drop-shadow-[0_0_15px_rgba(79,70,229,0.5)] mb-4')
            ui.label('LYNDRIX').classes('text-3xl font-black text-white tracking-[0.2em] mb-1')
            ui.label('Secure Core Access').classes('text-xs font-semibold text-zinc-400 uppercase tracking-widest mb-8')
            
            # Input Felder mit integrierten Icons
            with ui.column().classes('w-full gap-4'):
                username = ui.input('Benutzername').classes('w-full text-lg').props('dark outlined rounded clearable')
                with username.add_slot('prepend'):
                    ui.icon('person').classes('text-zinc-500')
                    
                password = ui.input('Passwort', password=True, password_toggle_button=True).classes('w-full text-lg').props('dark outlined rounded')
                with password.add_slot('prepend'):
                    ui.icon('vpn_key').classes('text-zinc-500')
            
            # Button Container
            btn_container = ui.column().classes('w-full mt-8')
            with btn_container:
                # Button mit Hover-Glow und Transitionen
                login_btn = ui.button('SYSTEM BETRETEN', on_click=lambda: try_login()).classes('w-full py-4 rounded-xl font-bold tracking-widest bg-indigo-600 hover:bg-indigo-500 hover:shadow-[0_0_20px_rgba(79,70,229,0.4)] transition-all duration-300')
            
            async def try_login():
                # UI Feedback: Button "laden" lassen
                login_btn.disable()
                login_btn.text = 'AUTHENTIFIZIERE...'
                
                auth = getattr(fastapi_app.state, 'auth', None)
                if not auth:
                    ui.notify('Systemfehler: Auth-Dienst nicht bereit', type='negative', position='top')
                    login_btn.enable()
                    login_btn.text = 'SYSTEM BETRETEN'
                    return

                try:
                    user_data = await auth.login(username.value, password.value)
                    
                    if user_data:
                        nicegui_app.storage.user.update({
                            'authenticated': True,
                            'username': user_data['username'],
                            'roles': user_data['roles']
                        })
                        # Erfolgs-Animation auf dem Button
                        login_btn.classes(remove='bg-indigo-600 hover:bg-indigo-500', add='bg-emerald-500 shadow-[0_0_20px_rgba(16,185,129,0.4)] text-white')
                        login_btn.text = 'ZUGRIFF GEWÄHRT'
                        ui.notify(f'Willkommen zurück, {user_data["username"]}!', type='positive', position='top')
                        
                        # Kurze Pause für den psychologischen Effekt (Nutzer sieht, dass es geklappt hat)
                        await asyncio.sleep(0.8)
                        ui.navigate.to('/')
                    else:
                        ui.notify('Zugriff verweigert: Ungültige Anmeldedaten', type='negative', position='top')
                        login_btn.enable()
                        login_btn.text = 'SYSTEM BETRETEN'
                        password.value = '' # Passwort-Feld bei Fehler sicherheitshalber leeren
                except Exception as e:
                    ui.notify(f'Interner Fehler: {e}', type='negative', position='top')
                    login_btn.enable()
                    login_btn.text = 'SYSTEM BETRETEN'

            # Footer Links (Optisch schick, aktuell ohne Funktion)
            with ui.row().classes('w-full justify-center mt-6 gap-4 text-xs text-zinc-500'):
                ui.link('Passwort vergessen?', '#').classes('hover:text-indigo-400 transition-colors no-underline')
                ui.label('•')
                ui.link('Support kontaktieren', '#').classes('hover:text-indigo-400 transition-colors no-underline')