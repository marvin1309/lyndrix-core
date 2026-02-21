from nicegui import ui
from . import layout, pages

def setup(fastapi_app):
    # Den Layout-Decorator global registrieren
    fastapi_app.state.main_layout = lambda title: layout.main_layout(fastapi_app, title)

    # Navigation initialisieren
    fastapi_app.state.nav_items['Menu'].extend([
        {'icon': 'dashboard', 'label': 'Overview', 'target': '/'},
    ])
    
    fastapi_app.state.nav_items['System'].extend([
        {'icon': 'extension', 'label': 'Plugins', 'target': '/plugins'},
        {'icon': 'settings', 'label': 'Einstellungen', 'target': '/settings'},
    ])

    # --- ROUTEN DEFINIEREN ---
    @ui.page('/')
    @fastapi_app.state.main_layout('Overview')
    def index():
        pages.render_dashboard_page(fastapi_app)

    @ui.page('/settings')
    @fastapi_app.state.main_layout('Einstellungen')
    def settings():
        pages.render_settings_page(fastapi_app)

    @ui.page('/plugins')
    @fastapi_app.state.main_layout('Plugins')
    def plugins():
        # Wir rufen die render_plugins_page Funktion aus pages.py auf
        pages.render_plugins_page(fastapi_app)

    print("Lyndrix Core UI (Modular & Clean) geladen.")