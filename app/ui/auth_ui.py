from nicegui import ui, app

def render_user_settings_card():
    # Wir nutzen Mock-Daten oder Session-Daten
    user = app.storage.user
    full_name = str(user.get('full_name', 'Benutzer Name'))
    username = str(user.get('username', 'username'))
    
    with ui.column().classes('w-full gap-6'):
        with ui.row().classes('w-full items-center gap-6 p-4'):
            ui.avatar('UN', color='indigo', text_color='white').classes('text-2xl font-bold')
            with ui.column().classes('gap-0'):
                ui.label(full_name).classes('text-2xl font-bold dark:text-white')
                ui.label(f"Angemeldet als {username}").classes('text-sm text-slate-500')

        ui.separator()

        with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-4'):
            for title, val in [('Account Status', 'Aktiv'), ('Provider', 'Lokal')]:
                with ui.column().classes('p-4 border border-slate-100 dark:border-zinc-800 rounded-2xl bg-slate-50/50 dark:bg-zinc-950/30'):
                    ui.label(title).classes('text-[10px] font-bold uppercase text-slate-400')
                    ui.label(val).classes('text-sm dark:text-zinc-300')

        with ui.row().classes('w-full justify-end gap-4'):
            async def logout():
                app.storage.user.clear()
                ui.navigate.to('/')
            ui.button('Abmelden', color='red', on_click=logout).props('unelevated rounded size=sm')