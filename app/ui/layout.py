import os
import sys
import inspect
from functools import wraps
from nicegui import ui, app

from config import settings
from ui.theme import apply_theme, UIStyles
from ui.maintenance import attach_maintenance_overlay
from core.logger import get_logger
from core.bus import bus
from core.components.plugins.logic.manager import module_manager

log = get_logger("UI:Layout")

def trigger_reload():
    ui.notify('System is rebooting...', type='ongoing', spinner=True)
    bus.emit('system:reload', {})

def logout():
    app.storage.user.clear()
    ui.navigate.to('/login')

def get_nav_items():
    """Generates navigation links dynamically from module manifests."""
    core_items = []
    plugin_items = []

    # Hole alle geladenen Manifeste aus dem Manager
    manifests = module_manager.get_manifests()
    
    for manifest in manifests:
        # Pydantic 2.x speichert Attribute direkt. 
        # Falls ui_route fehlt oder None ist, überspringen wir das Modul.
        # getattr ist hier der sicherste Weg, um Pydantic-Modelle auszulesen.
        route = getattr(manifest, 'ui_route', None)
        
        if route is None or route == "":
            continue

        item = {
            'label': manifest.name,
            'icon': manifest.icon or 'extension',
            'target': route,
            'type': manifest.type
        }

        if manifest.type == "CORE":
            core_items.append(item)
        else:
            plugin_items.append(item)

    # Die Einstellungen (System Core) manuell anfügen
    core_items.append({
        'label': 'Settings',
        'icon': 'settings',
        'target': '/settings',
        'type': 'CORE'
    })

    return core_items, plugin_items

def main_layout(page_title: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            
            theme_pref = app.storage.user.get('theme_pref', 'dark')
            apply_theme(theme_pref) 
            
            is_dark = theme_pref == 'dark'
            dark = ui.dark_mode(value=is_dark)

            ui.run_javascript(f"document.documentElement.classList.toggle('dark', {'true' if is_dark else 'false'});")

            def on_theme_switch(e):
                mode = 'dark' if e.value else 'light'
                app.storage.user['theme_pref'] = mode
                
                if e.value:
                    dark.enable()
                else:
                    dark.disable()
                
                ui.run_javascript(f"document.documentElement.classList.toggle('dark', {'true' if e.value else 'false'});")

            attach_maintenance_overlay()

            # --- HEADER ---
            with ui.header(elevated=False).classes(UIStyles.HEADER):
                with ui.row().classes('items-center gap-3 w-full'):
                    ui.button(icon='menu').props('flat round text-color=current').on('click', lambda: left_drawer.toggle())
                    ui.label(settings.APP_TITLE).classes('text-lg font-black tracking-tighter text-primary')
                    ui.space() 
                    
                    with ui.row().classes('items-center gap-2'):
                        with ui.row().classes('items-center bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-zinc-700 mr-2'):
                            ui.icon('light_mode', size='14px').classes('text-orange-500')
                            ui.switch(value=is_dark, on_change=on_theme_switch).props('dense color=primary')
                            ui.icon('dark_mode', size='14px').classes('text-indigo-400')

                        ui.label(page_title).classes(UIStyles.LABEL_MINI)
                        with ui.button(icon='account_circle').props('flat round text-color=current'):
                            with ui.menu().classes(UIStyles.MENU_CONTAINER):
                                ui.menu_item('Restart Engine', on_click=trigger_reload).classes(UIStyles.MENU_ITEM)
                                ui.menu_item('Logout', on_click=logout).classes(UIStyles.MENU_ITEM)
            # --- SIDEBAR ---
            with ui.left_drawer(value=False).classes(UIStyles.SIDEBAR) as left_drawer:
                core_items, plugin_items = get_nav_items()
                
                # Dieser Column-Container füllt die gesamte Höhe der Sidebar aus
                with ui.column().classes('w-full h-full no-wrap'):
                    
                    # 1. OBERER BEREICH: User Plugins (Dynamisch)
                    with ui.column().classes('w-full flex-grow overflow-y-auto'):
                        if plugin_items:
                            ui.label("User Plugins").classes(UIStyles.NAV_CATEGORY)
                            with ui.column().classes('w-full gap-1'):
                                for item in plugin_items:
                                    is_active = (page_title == item['label'])
                                    style = UIStyles.NAV_LINK_ACTIVE if is_active else UIStyles.NAV_LINK_INACTIVE
                                    
                                    with ui.link(target=item['target']).classes(f'{UIStyles.NAV_LINK_BASE} {style}'):
                                        ui.icon(item['icon'], size='20px')
                                        ui.label(item['label']).classes('text-sm ml-3 font-medium')
                        else:
                            # Platzhalter falls keine Plugins da sind
                            ui.label("No Plugins active").classes('text-xs text-slate-500 italic p-4')
                    
                    # 2. UNTERER BEREICH: Core Komponenten (Fest angepinnt)
                    # mt-auto schiebt diesen Block nach ganz unten
                    with ui.column().classes('w-full mt-auto pb-4'): 
                        ui.separator().classes('mb-4 bg-slate-200 dark:bg-zinc-800') 
                        ui.label("System").classes(UIStyles.NAV_CATEGORY)
                        with ui.column().classes('w-full gap-1'):
                            for item in core_items:
                                is_active = (page_title == item['label'])
                                style = UIStyles.NAV_LINK_ACTIVE if is_active else UIStyles.NAV_LINK_INACTIVE
                                
                                with ui.link(target=item['target']).classes(f'{UIStyles.NAV_LINK_BASE} {style}'):
                                    ui.icon(item['icon'], size='20px')
                                    ui.label(item['label']).classes('text-sm ml-3 font-medium')

            # --- CONTENT ---
            with ui.column().classes('p-6 md:p-12 w-full max-w-7xl mx-auto flex-grow'):
                if inspect.iscoroutinefunction(fn):
                    return await fn(*args, **kwargs)
                else:
                    return fn(*args, **kwargs)
                
        return wrapper
    return decorator