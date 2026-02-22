from nicegui import ui
import psutil
from .auth_ui import render_user_settings_card
from .theme import UIStyles 


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