from nicegui import ui
from ui.layout import main_layout # Globales Layout aus /app/ui/
from .settings_ui import render_settings_page # Lokale UI aus dem selben Ordner

def register_settings_routes():
    @ui.page('/settings')
    @main_layout('Einstellungen')
    async def settings_page(): # Ändere 'def' zu 'async def'
        await render_settings_page() # Füge 'await' hinzu