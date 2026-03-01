import psutil
from nicegui import ui
from ui.theme import UIStyles

async def render_dashboard_page():
    ui.label('System Dashboard').classes('text-2xl font-bold')
    
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

    # Die Update-Funktion für die Metriken
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
        except Exception: 
            pass

    ui.timer(2.0, update_ui)