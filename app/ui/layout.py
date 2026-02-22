import os
import sys
from functools import wraps
from nicegui import ui, app

from ui.theme import apply_theme, UIStyles
from ui.maintenance import attach_maintenance_overlay
from core.bus import bus
from core.modules.manager import module_manager # WICHTIG: Holt sich die Modul-Daten

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

    for manifest in module_manager.get_manifests():
        # WICHTIG: Wenn das Modul keine ui_route hat, überspringen wir es für die Sidebar!
        if not manifest.ui_route:
            continue

        item = {
            'label': manifest.name,
            'icon': manifest.icon,
            'target': manifest.ui_route, # Nutzt jetzt direkt die Route aus dem Manifest
            'type': manifest.type
        }

        if manifest.type == "CORE":
            core_items.append(item)
        else:
            plugin_items.append(item)

    return core_items, plugin_items

def main_layout(page_title: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            apply_theme()
            dark = ui.dark_mode()

            # Darkmode Präferenz
            theme_pref = app.storage.user.get('theme_pref', 'auto')
            if theme_pref == 'dark': dark.enable()
            elif theme_pref == 'light': dark.disable()
            else: dark.auto()

            def set_theme(mode: str):
                app.storage.user['theme_pref'] = mode
                if mode == 'dark': dark.enable()
                elif mode == 'light': dark.disable()
                else: dark.auto()
                ui.timer(0.5, lambda: ui.navigate.to(app.request.url.path), once=True)

            # --- WARTUNGS-LOGIK ---
            attach_maintenance_overlay()

            # --- HEADER ---
            with ui.header(elevated=False).classes(UIStyles.HEADER):
                with ui.row().classes('items-center gap-3 w-full'):
                    ui.button(icon='menu').props('flat round text-color=current').on('click', lambda: left_drawer.toggle())
                    ui.label('LYNDRIX').classes('text-lg font-black tracking-tighter text-primary')
                    ui.space() 
                    
                    with ui.row().classes('items-center gap-2'):
                        # THEME TOGGLE
                        with ui.row().classes('items-center bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-zinc-700 mr-2'):
                            ui.icon('light_mode', size='14px').classes('text-orange-500')
                            ui.switch().bind_value(dark, 'value').props('dense color=primary')
                            ui.icon('dark_mode', size='14px').classes('text-indigo-400')

                        ui.label(page_title).classes(UIStyles.LABEL_MINI)
                        with ui.button(icon='account_circle').props('flat round text-color=current'):
                            with ui.menu().classes(UIStyles.MENU_CONTAINER):
                                with ui.menu_item('Darstellung').classes(UIStyles.MENU_ITEM):
                                    with ui.menu().classes(UIStyles.MENU_CONTAINER):
                                        ui.menu_item('Auto', on_click=lambda: set_theme('auto'))
                                        ui.menu_item('Hell', on_click=lambda: set_theme('light'))
                                        ui.menu_item('Dunkel', on_click=lambda: set_theme('dark'))
                                ui.separator()
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
                return await fn(*args, **kwargs)
                
        return wrapper
    return decorator