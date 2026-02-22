from nicegui import ui
from core.modules.models import ModuleManifest
from core.modules.manager import module_manager # Um an die Plugins zu kommen
from ui.theme import UIStyles
from ui.layout import main_layout
from ui.auth_ui import render_user_settings_card

manifest = ModuleManifest(
    id="lyndrix.core.settings",
    name="Einstellungen",
    version="1.0.0",
    description="Verwalte dein Benutzerprofil und die Systemeinstellungen.",
    author="Lyndrix",
    icon="tune",
    type="CORE",
    ui_route="/settings" # NEU: Für die Sidebar!
)

def setup(ctx):
    @ui.page('/settings')
    @main_layout('Einstellungen')
    async def render_settings_page():
        ui.label('Einstellungen').classes(UIStyles.TITLE_H1 + ' mb-8')
        
        # 1. Wir suchen alle Module, die eine "render_settings_ui" Funktion haben
        modules_with_settings = []
        for mod_id, data in module_manager.registry.items():
            # data["module"] ist die importierte __init__.py des Plugins
            if hasattr(data["module"], "render_settings_ui"):
                modules_with_settings.append(data)

        # 2. Tabs aufbauen
        with ui.tabs().classes('w-full dark:text-white') as tabs:
            t1 = ui.tab('Profil', icon='person')
            t2 = ui.tab('System', icon='settings')
            t3 = ui.tab('Security', icon='security')
            
            # Dynamische Tabs für jedes Plugin erstellen
            plugin_tabs = {}
            for mod_data in modules_with_settings:
                manifest = mod_data["manifest"]
                plugin_tabs[manifest.id] = ui.tab(manifest.name, icon=manifest.icon)
            
        # 3. Tab-Panels füllen
        with ui.tab_panels(tabs, value=t1).classes('w-full bg-transparent mt-6'):
            with ui.tab_panel(t1):
                render_user_settings_card()
                
            with ui.tab_panel(t2):
                with ui.card().classes(UIStyles.CARD_GLASS):
                    ui.label('System-Konfiguration').classes(UIStyles.TITLE_H3)
                    ui.label('Hier können bald globale Parameter konfiguriert werden.').classes(UIStyles.TEXT_MUTED)
            
            with ui.tab_panel(t3):
                with ui.card().classes(UIStyles.CARD_GLASS):
                    ui.label('Vault Status').classes(UIStyles.TITLE_H3)
                    ui.label('Der Tresor ist aktuell entsperrt und bereit.').classes('text-emerald-500 text-sm')
            
            # Dynamische Panels für die Plugins rendern
            for mod_data in modules_with_settings:
                manifest = mod_data["manifest"]
                with ui.tab_panel(plugin_tabs[manifest.id]):
                    with ui.card().classes(UIStyles.CARD_GLASS + ' w-full'):
                        ui.label(f'{manifest.name} Konfiguration').classes(UIStyles.TITLE_H3)
                        # Hier rufen wir die UI-Funktion des Plugins auf und übergeben seinen EIGENEN Context!
                        mod_data["module"].render_settings_ui(mod_data["context"])