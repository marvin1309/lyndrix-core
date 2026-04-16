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

# ==========================================
# ZENTRALE SETTINGS POPUP LOGIK
# ==========================================

# ==========================================
# RESTLICHE LAYOUT FUNKTIONEN
# ==========================================
def trigger_reload():
    """Triggers a client-side page reload."""
    ui.notify('Refreshing UI...', type='info')
    ui.run_javascript('window.location.reload();')

def logout():
    app.storage.user.clear()
    ui.navigate.to('/login')

def get_nav_items():
    """Generates navigation links dynamically from module manifests."""
    core_items = []
    plugin_items = []

    manifests = module_manager.get_manifests()
    
    for manifest in manifests:
        # NEW: Only show active modules in the navigation
        entry = module_manager.registry.get(manifest.id, {})
        if entry.get("status") != "active":
            continue

        route = getattr(manifest, 'ui_route', None)
        if not route: continue

        item = {
            'id': manifest.id, 
            'label': manifest.name,
            'icon': manifest.icon or 'extension',
            'target': route,
            'type': manifest.type
        }

        if manifest.type == "CORE": core_items.append(item)
        else: plugin_items.append(item)

    core_items.append({'id': 'core.settings', 'label': 'Settings', 'icon': 'settings', 'target': '/settings', 'type': 'CORE'})
    return core_items, plugin_items

def open_plugin_settings_modal(manifest_id: str):
    """Sucht das Modul in der Registry und öffnet dessen Settings-UI in einem gestylten Dialog."""
    entry = module_manager.registry.get(manifest_id)
    if not entry or entry.get("status") != "active":
        ui.notify('Fehler: Modul ist nicht aktiv oder nicht gefunden.', type='negative')
        return

    manifest = entry["manifest"]
    mod = entry["module"]
    ctx = entry["context"]

    if not hasattr(mod, 'render_settings_ui'):
        ui.notify(f'{manifest.name} hat keine konfigurierbaren Einstellungen.', type='info')
        return

    with ui.dialog() as settings_dialog, ui.card().classes(f'w-full max-w-xl p-0 overflow-hidden {UIStyles.CARD_GLASS}'):
        
        with ui.row().classes('w-full justify-between items-center p-4 border-b border-slate-200 dark:border-zinc-800 bg-slate-50/50 dark:bg-zinc-900/50'):
            with ui.row().classes('items-center gap-3'):
                ui.icon(manifest.icon, size='24px').classes('text-primary')
                with ui.column().classes('gap-0'):
                    ui.label(manifest.name).classes('font-bold text-lg leading-tight text-slate-800 dark:text-zinc-100')
                    ui.label(f'v{manifest.version}').classes('text-xs font-mono text-slate-500 dark:text-zinc-400')
            
            ui.button(icon='close', on_click=settings_dialog.close).props('flat round dense').classes('text-slate-500 hover:text-slate-800 dark:hover:text-white transition-colors')
        
        with ui.scroll_area().classes('w-full max-h-[70vh] p-6'):
            try:
                mod.render_settings_ui(ctx)
            except Exception as e:
                ui.label(f"Fehler in Plugin-UI: {str(e)}").classes('text-red-500 text-xs')

    settings_dialog.open()


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
                if e.value: dark.enable()
                else: dark.disable()
                ui.run_javascript(f"document.documentElement.classList.toggle('dark', {'true' if e.value else 'false'});")

            @bus.subscribe("ui:needs_refresh")
            def on_ui_refresh(payload):
                trigger_reload()

            attach_maintenance_overlay()
            core_items, plugin_items = get_nav_items()
            
            # Finde die Manifest-ID der aktuellen Seite
            active_manifest_id = None
            for item in plugin_items + core_items:
                if item['label'] == page_title:
                    active_manifest_id = item['id']
                    break

            # --- HEADER ---
            with ui.header(elevated=False).classes(UIStyles.HEADER):
                with ui.row().classes('items-center gap-3 w-full'):
                    ui.button(icon='menu').props('flat round text-color=current').on('click', lambda: left_drawer.toggle())
                    ui.label(settings.APP_TITLE).classes('text-lg font-black tracking-tighter text-primary')
                    ui.space() 
                    
                    with ui.row().classes('items-center gap-2'):
                        
                        # --- DYNAMISCHER SETTINGS BUTTON ---
                        if active_manifest_id and active_manifest_id != 'core.settings':
                            entry = module_manager.registry.get(active_manifest_id)
                            if entry and hasattr(entry.get("module"), 'render_settings_ui'):
                                # FIX: text-color=current passt sich dem Theme an!
                                ui.button(
                                    icon='settings_applications', 
                                    on_click=lambda: open_plugin_settings_modal(active_manifest_id)
                                ).props('flat round text-color=current').tooltip(f'{page_title} Einstellungen')
                                ui.separator().props('vertical').classes('mx-1 h-6 self-center opacity-30')

                        with ui.row().classes('items-center bg-slate-100 dark:bg-zinc-800 px-2 py-0.5 rounded-full border border-slate-200 dark:border-zinc-700 mr-2'):
                            ui.icon('light_mode', size='14px').classes('text-orange-500')
                            ui.switch(value=is_dark, on_change=on_theme_switch).props('dense color=primary')
                            ui.icon('dark_mode', size='14px').classes('text-indigo-400')

                        ui.label(page_title).classes(UIStyles.LABEL_MINI)
                        with ui.button(icon='account_circle').props('flat round text-color=current'):
                            with ui.menu().classes(UIStyles.MENU_CONTAINER):
                                ui.menu_item('Refresh UI', on_click=trigger_reload).classes(UIStyles.MENU_ITEM)
                                ui.menu_item('Logout', on_click=logout).classes(UIStyles.MENU_ITEM)

            # --- SIDEBAR ---
            with ui.left_drawer(value=False).classes(UIStyles.SIDEBAR) as left_drawer:
                with ui.column().classes('w-full h-full no-wrap'):
                    with ui.column().classes('w-full flex-grow overflow-y-auto'):
                        if plugin_items:
                            ui.label("Services").classes(UIStyles.NAV_CATEGORY)
                            with ui.column().classes('w-full gap-1'):
                                for item in plugin_items:
                                    is_active = (page_title == item['label'])
                                    style = UIStyles.NAV_LINK_ACTIVE if is_active else UIStyles.NAV_LINK_INACTIVE
                                    with ui.link(target=item['target']).classes(f'{UIStyles.NAV_LINK_BASE} {style}'):
                                        ui.icon(item['icon'], size='20px')
                                        ui.label(item['label']).classes('text-sm ml-3 font-medium')
                        else:
                            ui.label("No Plugins active").classes('text-xs text-slate-500 italic p-4')

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