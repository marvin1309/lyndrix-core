import importlib.util
import os
import sys

def prepare_state(app):
    """Initialisiert den Basiszustand der FastAPI App."""
    if not hasattr(app.state, 'nav_items'):
        app.state.nav_items = {'Menu': [], 'System': [], 'Extensions': [], 'Data': []}
    if not hasattr(app.state, 'settings_providers'): app.state.settings_providers = []
    if not hasattr(app.state, 'metrics_providers'): app.state.metrics_providers = []
    if not hasattr(app.state, 'dashboard_providers'): app.state.dashboard_providers = []

def load_core_services():
    """Lädt die Logik-Singletons aus /core/services."""
    # Hier könnten wir Services dynamisch importieren oder fest definieren
    # Da Services Kern-Logik sind, ist ein fester Import oft stabiler:
    from app.core.services.vault.vault_service import vault_service
    print("✅ Core Services (Vault, Bus) initialisiert.")

def _scan_and_load_dir(app, directory, module_prefix, label):
    # ... (Deine bewährte Scan-Logik von vorhin) ...
    # Sie nutzt jetzt 'bus' aus core.bus für alle Plugin-Events
    pass