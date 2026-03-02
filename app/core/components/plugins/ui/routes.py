from nicegui import ui
from ui.layout import main_layout
from .plugins_ui import render_plugins_page

def register_plugin_routes(): # <--- Dieser Name muss exakt so stimmen!
    @ui.page('/plugins')
    @main_layout('Plugins & Module')
    def plugins_page():
        render_plugins_page()