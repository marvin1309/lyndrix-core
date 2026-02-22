import psutil
from nicegui import ui
from core.modules.models import ModuleManifest
from ui.theme import UIStyles
from ui.layout import main_layout

# 1. Das Manifest für den ModuleManager
manifest = ModuleManifest(
    id="lyndrix.core.dashboard",
    name="System Dashboard",
    version="1.0.0",
    description="Das Haupt-Dashboard für die Systemüberwachung.",
    author="Lyndrix",
    icon="dashboard",
    ui_route="/dashboard",
    type="CORE",
    permissions={
        "subscribe": ["system:started"], # Darf den Systemstart hören
        "emit": []
    }
)

# 2. Die Setup-Funktion (Wird vom ModuleManager mit dem Context aufgerufen)
def setup(ctx):
    ctx.log.info("Initialisiere Dashboard Modul...")

    # Wir registrieren die Route direkt hier im Modul!
    @ui.page('/dashboard')
    @main_layout('Overview')
    async def render_dashboard_page():
        ctx.log.debug("Dashboard Seite wurde von einem User aufgerufen.")
        
        # Header Bereich
        with ui.card().classes(UIStyles.CARD_GLASS + ' w-full mb-6'):
            ui.label('Willkommen bei Lyndrix').classes(UIStyles.TITLE_H1)
            ui.label('Systemübersicht und Echtzeit-Statusberichte.').classes(UIStyles.TEXT_MUTED)

        # Monitoring Sektion
        with ui.row().classes('w-full gap-6'):
            stats_config = [
                {'label': 'CPU LOAD', 'color': 'blue', 'icon': 'speed'},
                {'label': 'RAM USAGE', 'color': 'indigo', 'icon': 'memory'},
                {'label': 'DISK SPACE', 'color': 'emerald', 'icon': 'storage'},
            ]
            
            ui_elements = {}

            for config in stats_config:
                with ui.card().classes(UIStyles.CARD_BASE + ' flex-1'):
                    with ui.row().classes('items-center gap-2 mb-2'):
                        ui.icon(config['icon']).classes(f"text-{config['color']}-500")
                        ui.label(config['label']).classes(UIStyles.LABEL_MINI)
                    
                    lbl = ui.label('0%').classes(f"text-4xl font-black text-{config['color']}-500")
                    prog = ui.linear_progress(value=0).props(f"color={config['color']} rounded")
                    
                    ui_elements[config['label']] = (lbl, prog)

        # Button Sektion
        with ui.row().classes('w-full mt-8 gap-4'):
            ui.button('System Refresh', icon='refresh', on_click=lambda: ui.notify('Refreshing...')) \
                .classes(UIStyles.BUTTON_PRIMARY + ' md:w-64') \
                .props('unelevated')

            ui.button('Logs einsehen', icon='list_alt') \
                .classes(UIStyles.BUTTON_SECONDARY + ' md:w-64') \
                .props('unelevated')

        # Die Update-Funktion für die Graphen
        def update_ui():
            try:
                c = psutil.cpu_percent()
                r = psutil.virtual_memory().percent
                d = psutil.disk_usage('/').percent
                
                ui_elements['CPU LOAD'][0].set_text(f"{c}%")
                ui_elements['CPU LOAD'][1].set_value(c/100)
                
                ui_elements['RAM USAGE'][0].set_text(f"{r}%")
                ui_elements['RAM USAGE'][1].set_value(r/100)
                
                ui_elements['DISK SPACE'][0].set_text(f"{d}%")
                ui_elements['DISK SPACE'][1].set_value(d/100)
            except Exception as e: 
                ctx.log.error(f"Fehler beim Lesen der Metriken: {e}")

        # Der Timer, der nur läuft, solange die Seite offen ist
        ui.timer(2.0, update_ui)