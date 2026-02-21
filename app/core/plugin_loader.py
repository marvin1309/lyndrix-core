import os
import sys
import importlib.util
import inspect
import asyncio
from fastapi import FastAPI

# ==========================================
# DER GLOBALE EVENT BROKER
# ==========================================
class GlobalEventBus:
    def __init__(self):
        self.subscribers = {}

    def subscribe(self, topic: str, callback):
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)

    def emit(self, topic: str, payload: dict = None):
        if payload is None: payload = {}
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        asyncio.create_task(callback(payload))
                    else:
                        callback(payload)
                except Exception as e:
                    print(f"[EventBus] FEHLER in '{topic}': {e}")

# ==========================================
# LOADER LOGIK
# ==========================================
def prepare_state(app: FastAPI):
    """Bereitet den globalen App-State absolut sicher vor."""
    # Infrastruktur
    if not hasattr(app.state, 'event_bus'):
        app.state.event_bus = GlobalEventBus()
    if not hasattr(app.state, 'plugins'):
        app.state.plugins = []
    
    # Navigation
    if not hasattr(app.state, 'nav_items'):
        app.state.nav_items = {
            'Menu': [], 'Data': [], 'Infrastructure': [], 'System': [], 'Extensions': []
        }
    
    # UI & Dashboard Provider (Die Herzstücke)
    if not hasattr(app.state, 'settings_providers'):
        app.state.settings_providers = []
    if not hasattr(app.state, 'dashboard_providers'):
        app.state.dashboard_providers = []
    if not hasattr(app.state, 'metrics_providers'):
        app.state.metrics_providers = []

def _scan_and_load_dir(app: FastAPI, directory: str, module_prefix: str, label: str):
    """Scannt Verzeichnisse und registriert Logik, UI und Metriken automatisch."""
    full_path = os.path.abspath(directory)
    if not os.path.exists(full_path):
        return

    folders = [f for f in os.listdir(full_path) if os.path.isdir(os.path.join(full_path, f))]
    
    # Priorisierung CORE
    if label == "CORE":
        priority = ['lyndrix_core_ui', 'secrets_manager']
        for p in reversed(priority):
            if p in folders:
                folders.remove(p)
                folders.insert(0, p)

    for mod_name in folders:
        logic_file = os.path.join(full_path, mod_name, "logic.py")
        if not os.path.exists(logic_file):
            continue

        try:
            module_path = f"{module_prefix}.{mod_name}.logic"
            spec = importlib.util.spec_from_file_location(module_path, logic_file)
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_path] = module
            spec.loader.exec_module(module)

            # 1. Setup ausführen
            if hasattr(module, "setup"):
                module.setup(app)
                
            # 2. Plugin-Metadaten speichern
            app.state.plugins.append({
                'id': mod_name, 
                'name': getattr(module, "PLUGIN_NAME", mod_name.title()),
                'description': getattr(module, "PLUGIN_DESCRIPTION", ""),
                'icon': getattr(module, "PLUGIN_ICON", "extension"),
                'type': label,
                'status': 'Aktiv'
            })

            # 3. AUTOMATIK: Einstellungen (Settings)
            if hasattr(module, "settings") and hasattr(module.settings, "render"):
                app.state.settings_providers.append({
                    'name': getattr(module, "PLUGIN_NAME", mod_name.title()),
                    'icon': getattr(module, "PLUGIN_ICON", "settings"),
                    'type': label,
                    'render': lambda m=module: m.settings.render()
                })

            # 4. AUTOMATIK: Dashboard Widgets (Komplexe UI)
            if hasattr(module, "widget_render"):
                app.state.dashboard_providers.append({
                    'name': getattr(module, "PLUGIN_NAME", mod_name.title()),
                    'type': label,
                    'render': lambda m=module: m.widget_render()
                })
            
            # 5. AUTOMATIK: Metriken (Zahlen-Karten)
            if hasattr(module, "provide_metrics"):
                app.state.metrics_providers.append(module.provide_metrics)

            # 6. AUTOMATIK: Navigation
            # Erkennt Variablen auf Modulebene: NAV_LABEL, NAV_TARGET, NAV_ICON, NAV_CATEGORY
            if hasattr(module, "NAV_LABEL") and hasattr(module, "NAV_TARGET"):
                # Automatische Zuweisung: CORE -> System, PLUGIN -> Extensions
                default_cat = 'System' if label == 'CORE' else 'Extensions'
                category = getattr(module, "NAV_CATEGORY", default_cat)
                
                # Dubletten-Check (verhindert doppelte Links bei Reload)
                if not any(i['target'] == module.NAV_TARGET for i in app.state.nav_items.get(category, [])):
                    app.state.nav_items[category].append({
                        'icon': getattr(module, "NAV_ICON", getattr(module, "PLUGIN_ICON", "extension")),
                        'label': module.NAV_LABEL,
                        'target': module.NAV_TARGET
                    })

            print(f"  ✅ [{label}] {mod_name}")

        except Exception as e:
            print(f"  ❌ [{label}] Fehler bei {mod_name}: {e}")

def initialize_all(app: FastAPI):
    """Startpunkt für den System-Bootup."""
    # Erst State vorbereiten, dann laden
    prepare_state(app)
    
    # 1. Core-Infrastruktur
    _scan_and_load_dir(app, 'core/components', 'core.components', 'CORE')
    
    # 2. User-Erweiterungen
    _scan_and_load_dir(app, 'plugins', 'plugins', 'PLUGIN')