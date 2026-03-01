import os
import sys
from functools import wraps
from nicegui import ui, app

from ui.theme import apply_theme, UIStyles
from ui.maintenance import attach_maintenance_overlay
from core.bus import bus
from core.components.plugins.logic.manager import module_manager


def trigger_reload():
    ui.notify('System wird neu gestartet...', type='ongoing', spinner=True)
    bus.emit('system:reload', {})

def logout():
    app.storage.user.clear()
    ui.navigate.to('/login')

def get_nav_items():
    """Generiert die Navigationslinks dynamisch aus den Modul-Manifesten."""
    core_items = []
    plugin_items = []

    manifests = module_manager.get_manifests()
    # DEBUG: Schalte das ein, um im Log zu sehen, was der Manager findet
    # print(f"DEBUG: Manager hat {len(manifests)} Manifeste gefunden")

    for manifest in manifests:
        # WICHTIG: Prüfe, ob ui_route existiert UND nicht None ist
        if not hasattr(manifest, 'ui_route') or manifest.ui_route is None:
            continue

        item = {
            'label': manifest.name,
            'icon': manifest.icon or 'extension',
            'target': manifest.ui_route,
            'type': manifest.type
        }

        if manifest.type == "CORE":
            core_items.append(item)
        else:
            plugin_items.append(item)

    # Die Einstellungen manuell hinzufügen, falls sie nicht als Modul geladen werden
    core_items.append({
        'label': 'Einstellungen',
        'icon': 'settings',
        'target': '/settings',
        'type': 'CORE'
    })

    return core_items, plugin_items

def main_layout(page_title: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            
            # 1. Präferenz auslesen (Standard ist jetzt fest 'dark', kein schwammiges 'auto' mehr)
            theme_pref = app.storage.user.get('theme_pref', 'dark')
            
            # 2. Präferenz an apply_theme übergeben
            apply_theme(theme_pref) 
            
            # 3. Darkmode initialisieren
            is_dark = theme_pref == 'dark'
            dark = ui.dark_mode(value=is_dark)

            # --- DER NEUE FIX ---
            # Zwingt Tailwind sofort beim Laden der Seite, sich mit Python zu synchronisieren!
            ui.run_javascript(f"document.documentElement.classList.toggle('dark', {'true' if is_dark else 'false'});")

            def on_theme_switch(e):
                """Speichert die Einstellung und wechselt das Theme flüssig ohne Reload."""
                mode = 'dark' if e.value else 'light'
                app.storage.user['theme_pref'] = mode
                
                if e.value:
                    dark.enable()
                else:
                    dark.disable()
                
                # Zwingt Tailwind sofort zum Update
                js_cmd = f"document.documentElement.classList.toggle('dark', {'true' if e.value else 'false'});"
                ui.run_javascript(js_cmd)

            # --- WARTUNGS-LOGIK ---
            attach_maintenance_overlay()

            # --- HEADER ---
            with ui.header(elevated=False).classes(UIStyles.HEADER):
                with ui.row().classes('items-center gap-3 w-full'):
                    ui.button(icon='menu').props('flat round text-color=current').on('click', lambda: left_drawer.toggle())
                    ui.label('LYNDRIX').classes('text-lg font-black tracking-tighter text-primary')
                    ui.space() 
                    
                    with ui.row().classes('items-center gap-2'):
                        # THEME TOGGLE (Jetzt mit Speichern & Live-Update)
                        with ui.row().classes('items-center bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-zinc-700 mr-2'):
                            ui.icon('light_mode', size='14px').classes('text-orange-500')
                            # Wir nutzen jetzt unseren on_theme_switch Handler!
                            ui.switch(value=is_dark, on_change=on_theme_switch).props('dense color=primary')
                            ui.icon('dark_mode', size='14px').classes('text-indigo-400')

                        ui.label(page_title).classes(UIStyles.LABEL_MINI)
                        with ui.button(icon='account_circle').props('flat round text-color=current'):
                            with ui.menu().classes(UIStyles.MENU_CONTAINER):
                                # Das "Darstellung" Untermenü ist jetzt komplett weg!
                                ui.menu_item('Neustart', on_click=trigger_reload).classes(UIStyles.MENU_ITEM)
                                ui.menu_item('Abmelden', on_click=logout).classes(UIStyles.MENU_ITEM)

            # --- SIDEBAR / DYNAMISCHE NAVIGATION ---
            with ui.left_drawer(value=False).classes(UIStyles.SIDEBAR) as left_drawer:
                
                # Hol dir die dynamischen Listen
                core_items, plugin_items = get_nav_items()
                
                with ui.column().classes('w-full flex-grow'):
                    # OBERER BEREICH (System/Core Apps)
                    ui.label("Core Komponenten").classes(UIStyles.NAV_CATEGORY)
                    with ui.column().classes('w-full gap-1'):
                        for item in core_items:
                            is_active = (page_title == item['label'])
                            style = UIStyles.NAV_LINK_ACTIVE if is_active else UIStyles.NAV_LINK_INACTIVE
                            
                            with ui.link(target=item['target']).classes(f'{UIStyles.NAV_LINK_BASE} {style}'):
                                ui.icon(item['icon'], size='20px')
                                ui.label(item['label']).classes('text-sm ml-3 font-medium')
                
                # UNTERER BEREICH (User Plugins)
                if plugin_items:
                    with ui.column().classes('w-full pb-4 mt-auto'): 
                        ui.separator().classes('mb-4 bg-slate-200 dark:bg-zinc-800') 
                        ui.label("User Plugins").classes(UIStyles.NAV_CATEGORY)
                        with ui.column().classes('w-full gap-1'):
                            for item in plugin_items:
                                is_active = (page_title == item['label'])
                                style = UIStyles.NAV_LINK_ACTIVE if is_active else UIStyles.NAV_LINK_INACTIVE
                                
                                with ui.link(target=item['target']).classes(f'{UIStyles.NAV_LINK_BASE} {style}'):
                                    ui.icon(item['icon'], size='20px')
                                    ui.label(item['label']).classes('text-sm ml-3 font-medium')

            # --- CONTENT BEREICH ---
            with ui.column().classes('p-6 md:p-12 w-full max-w-7xl mx-auto flex-grow'):
                import inspect
                if inspect.iscoroutinefunction(fn):
                    return await fn(*args, **kwargs)
                else:
                    return fn(*args, **kwargs)
                
        return wrapper
    return decorator