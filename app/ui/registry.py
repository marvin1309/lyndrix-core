# /app/ui/registry.py

class UIRegistry:
    def __init__(self):
        # 1. Navigation: Kategorien mit Listen von Nav-Items
        self.nav_items = {
            'System': [
                {'label': 'Dashboard', 'icon': 'dashboard', 'target': '/dashboard'},
                {'label': 'Einstellungen', 'icon': 'settings', 'target': '/settings'},
                {'label': 'Plugins', 'icon': 'extension', 'target': '/plugins'}
            ],
            'Module': []  # Hier pushen Plugins später ihre Links rein
        }

        # 2. Settings: Plugins können hier eigene Tabs registrieren
        # Format: {'id': 'cmdb', 'label': 'CMDB', 'icon': 'dns', 'render_fn': callable}
        self.settings_tabs = []

        # 3. Dashboard Widgets: Plugins können Render-Funktionen für Karten hinterlegen
        self.dashboard_widgets = []

        # 4. Plugin Übersicht: Metadaten für die /plugins Seite
        # Format: {'name': 'Docker', 'description': '...', 'version': '1.0', 'icon': 'docker', 'active': True}
        self.plugins = []

# Singleton-Instanz, die von allen UI-Dateien und Plugins genutzt wird
ui_registry = UIRegistry()