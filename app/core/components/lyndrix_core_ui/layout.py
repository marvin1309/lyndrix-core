from functools import wraps
from nicegui import ui, app
import os
import asyncio

def logout():
    app.storage.user.clear()
    ui.navigate.to('/login')

async def force_exit():
    ui.notify('System wird heruntergefahren...', type='info')
    await asyncio.sleep(1)
    os._exit(0)

def trigger_reload(fastapi_app):
    ui.notify('System wird neu gestartet...', type='ongoing', spinner=True)
    if hasattr(fastapi_app.state, 'event_bus'):
        fastapi_app.state.event_bus.emit('system_reload_requested', {'action': 'reload'})

def main_layout(fastapi_app, page_title: str):
    def decorator(fn):
        @wraps(fn)
        def wrapper(*args, **kwargs):
            if not app.storage.user.get('authenticated', False):
                ui.navigate.to('/login')
                return

            dark = ui.dark_mode()
            try: dark.bind_value(app.storage.user, 'dark_mode')
            except: pass 

            # Header Definition
            with ui.header(elevated=False).classes('!bg-white/80 dark:!bg-zinc-900/80 backdrop-blur-md border-b border-slate-200 dark:border-zinc-800 text-slate-900 dark:text-white'):
                with ui.row().classes('items-center gap-3'):
                    menu_btn = ui.button(icon='menu').props('flat round color=zinc-500')
                    ui.label('LYNDRIX').classes('text-lg font-black tracking-tighter')
                ui.space()
                
                with ui.row().classes('items-center gap-2'):
                    # --- DARKMODE SWITCH (Links neben Reload) ---
                    with ui.row().classes('items-center bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-zinc-700 mr-2'):
                        ui.icon('light_mode', size='14px').classes('text-orange-500')
                        ui.switch().bind_value(dark, 'value').props('dense color=primary')
                        ui.icon('dark_mode', size='14px').classes('text-indigo-400')

                    ui.button(on_click=lambda: trigger_reload(fastapi_app), icon='autorenew').props('flat round size=sm').tooltip('Neustart')
                    ui.button(on_click=force_exit, icon='power_settings_new').props('flat round size=sm').classes('text-red-500').tooltip('Herunterfahren')
                    ui.separator().props('vertical').classes('mx-2 h-6 bg-slate-200 dark:bg-zinc-700')
                    ui.button(on_click=logout, icon='logout').props('flat round size=sm').classes('text-slate-600 dark:text-zinc-400').tooltip('Abmelden')

            # Sidebar (Drawer) mit Trennung
            with ui.left_drawer(value=False).classes('!bg-white dark:!bg-zinc-900 border-r border-slate-200 dark:border-zinc-800 !p-4 flex flex-col') as drawer:
                menu_btn.on_click(drawer.toggle)
                
                # --- OBERE NAVIGATION ---
                top_groups = [
                    {'key': 'Menu', 'label': 'Allgemein'},
                    {'key': 'Extensions', 'label': 'User Plugins'},
                    {'key': 'Data', 'label': 'Daten & Inventar'}
                ]

                with ui.column().classes('w-full flex-grow'):
                    for group in top_groups:
                        items = fastapi_app.state.nav_items.get(group['key'], [])
                        if not items: continue
                        
                        ui.label(group['label']).classes('px-3 mb-2 mt-4 text-[11px] font-bold text-slate-400 dark:text-zinc-500 uppercase tracking-widest')
                        with ui.column().classes('w-full gap-1'):
                            for item in items:
                                is_active = (page_title == item['label'])
                                style = 'bg-blue-50 dark:bg-blue-900/10 text-primary border-l-2 border-primary rounded-r-xl' if is_active else 'text-slate-500 dark:text-zinc-400 hover:bg-slate-50'
                                with ui.link(target=item['target']).classes('w-full flex items-center px-3 py-2 no-underline transition-all ' + style):
                                    ui.icon(item['icon'], size='20px')
                                    ui.label(item['label']).classes('text-sm ml-3')

                # Platzhalter, der die untere Gruppe nach unten drückt
                ui.space()

                # --- UNTERE ANGEPINNTE NAVIGATION ---
                bottom_group = {'key': 'System', 'label': 'Core Komponenten'}
                system_items = fastapi_app.state.nav_items.get(bottom_group['key'], [])
                if system_items:
                    with ui.column().classes('w-full pb-4'): # pb-4 für etwas Abstand zum Bildschirmrand
                        ui.separator().classes('mb-4 bg-slate-200 dark:bg-zinc-800') # Optische Trennung
                        ui.label(bottom_group['label']).classes('px-3 mb-2 text-[11px] font-bold text-slate-400 dark:text-zinc-500 uppercase tracking-widest')
                        with ui.column().classes('w-full gap-1'):
                            for item in system_items:
                                is_active = (page_title == item['label'])
                                style = 'bg-blue-50 dark:bg-blue-900/10 text-primary border-l-2 border-primary rounded-r-xl' if is_active else 'text-slate-500 dark:text-zinc-400 hover:bg-slate-50'
                                with ui.link(target=item['target']).classes('w-full flex items-center px-3 py-2 no-underline transition-all ' + style):
                                    ui.icon(item['icon'], size='20px')
                                    ui.label(item['label']).classes('text-sm ml-3')

            with ui.column().classes('p-6 md:p-12 w-full max-w-7xl mx-auto'):
                fn(*args, **kwargs)
        return wrapper
    return decorator