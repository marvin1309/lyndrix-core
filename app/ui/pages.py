from nicegui import ui
import psutil
from .auth_ui import render_user_settings_card
from .theme import UIStyles 

def render_dashboard_page():
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
                
                # Zahlenwert
                lbl = ui.label('0%').classes(f"text-4xl font-black text-{config['color']}-500")
                # Fortschrittsbalken
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

    def update_ui():
        try:
            c, r, d = psutil.cpu_percent(), psutil.virtual_memory().percent, psutil.disk_usage('/').percent
            ui_elements['CPU LOAD'][0].set_text(f"{c}%"); ui_elements['CPU LOAD'][1].set_value(c/100)
            ui_elements['RAM USAGE'][0].set_text(f"{r}%"); ui_elements['RAM USAGE'][1].set_value(r/100)
            ui_elements['DISK SPACE'][0].set_text(f"{d}%"); ui_elements['DISK SPACE'][1].set_value(d/100)
        except: pass

    ui.timer(2.0, update_ui)

def render_settings_page():
    ui.label('Einstellungen').classes(UIStyles.TITLE_H1 + ' mb-8')
    
    with ui.tabs().classes('w-full dark:text-white') as tabs:
        t1 = ui.tab('Profil', icon='person')
        t2 = ui.tab('System', icon='settings')
        
    with ui.tab_panels(tabs, value=t1).classes('w-full bg-transparent mt-6'):
        with ui.tab_panel(t1):
            render_user_settings_card()
        with ui.tab_panel(t2):
            ui.label('System-Konfiguration folgt hier.').classes(UIStyles.TEXT_MUTED + ' italic')

def render_plugins_page():
    ui.label('Plugin Management').classes(UIStyles.TITLE_H1)
    ui.label('Verwalte installierte Module.').classes(UIStyles.TEXT_MUTED + ' mb-8')
    
    with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'):
        for i in range(3):
            # Hier war vorher border-slate-200 hartkodiert -> jetzt CARD_GLASS
            with ui.card().classes(UIStyles.CARD_GLASS):
                with ui.row().classes('w-full items-center justify-between mb-4'):
                    ui.icon('extension', size='24px').classes('text-primary')
                    ui.switch().props('color=primary')
                
                ui.label(f'Plugin Modul {i+1}').classes(UIStyles.TITLE_H3)
                ui.label('Modulbeschreibung Platzhalter...').classes(UIStyles.TEXT_MUTED)