# Das ist jetzt die einzige Datei, die der Core-Loader anfassen muss!
from plugins.ssot_infra_importer import settings
from plugins.ssot_infra_importer import ui as plugin_ui

PLUGIN_NAME = "SSOT Infra Manager"
PLUGIN_ICON = "account_tree"
PLUGIN_DESCRIPTION = "Synchronisiert Server & Infrastruktur aus dem IaC Controller Repository."

def setup(app):
    # 1. Navigations-Eintrag registrieren
    app.state.nav_items.setdefault('Infrastructure', [])
    if not any(item['target'] == '/ssot-infra' for item in app.state.nav_items['Infrastructure']):
        app.state.nav_items['Infrastructure'].append({'icon': PLUGIN_ICON, 'label': 'SSOT Infra Manager', 'target': '/ssot-infra'})

    # 2. Plugin-Settings im Core registrieren!
    if not hasattr(app.state, 'settings_providers'):
        app.state.settings_providers = []
        
    app.state.settings_providers.append({
        'name': PLUGIN_NAME,
        'icon': PLUGIN_ICON,
        'render': lambda: settings.render_settings_ui(app)  # <--- Hier das `(app)` hinzufügen!
    })

    # 3. Die Haupt-UI des Plugins laden
    plugin_ui.mount_ui(app, PLUGIN_NAME)

    print(f"Plugin geladen: {PLUGIN_NAME}")