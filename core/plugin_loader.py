import os
import sys  # WICHTIG für den System-Restart
import importlib.util
import inspect
import asyncio
import json # <--- NEU: Für die Seed-Dateien
from fastapi import FastAPI
from core.database import SessionLocal, DynamicEntity # <--- NEU: Für den DB-Zugriff

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
        print(f"[EventBus] Neuer Subscriber für Topic: '{topic}'")

    def emit(self, topic: str, payload: dict = None):
        if payload is None:
            payload = {}
            
        print(f"[EventBus] EMIT -> Topic: '{topic}'")
        
        if topic in self.subscribers:
            for callback in self.subscribers[topic]:
                try:
                    if inspect.iscoroutinefunction(callback):
                        asyncio.create_task(callback(payload))
                    else:
                        callback(payload)
                except Exception as e:
                    print(f"[EventBus] FEHLER im Listener für '{topic}': {e}")


def load_plugins(app: FastAPI):
    # 1. Broker initialisieren
    app.state.event_bus = GlobalEventBus()
    
    # ==========================================
    # 2. SYSTEM CORE EVENTS (RELOAD LOGIK)
    # ==========================================
    def handle_system_reload(payload):
        print("\n" + "="*50)
        print("🔄 SYSTEM RELOAD INITIATED...")
        print("="*50 + "\n")
        os.execv(sys.executable, [sys.executable] + sys.argv)

    app.state.event_bus.subscribe('system_reload_requested', handle_system_reload)

    # 3. State Setup
    app.state.plugins = []
    app.state.nav_items = {
        'Menu': [],
        'Data': [],
        'Infrastructure': [],
        'System': [],
        'Extensions': []
    }

    plugins_dir = "plugins"
    if not os.path.exists(plugins_dir):
        return

    plugin_folders = os.listdir(plugins_dir)
    
    # Core-UI IMMER zuerst laden, damit das Layout als erstes bereitsteht
    if 'lyndrix_core_ui' in plugin_folders:
        plugin_folders.remove('lyndrix_core_ui')
        plugin_folders.insert(0, 'lyndrix_core_ui')

    for plugin_name in plugin_folders:
        plugin_path = os.path.join(plugins_dir, plugin_name)
        if not os.path.isdir(plugin_path):
            continue

        logic_file_path = os.path.join(plugin_path, "logic.py")
        if not os.path.exists(logic_file_path):
            continue

        try:
            spec = importlib.util.spec_from_file_location(f"plugins.{plugin_name}.logic", logic_file_path)
            if spec and spec.loader:
                plugin_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(plugin_module)
                
                friendly_name = getattr(plugin_module, "PLUGIN_NAME", plugin_name.replace('_', ' ').title())
                icon = getattr(plugin_module, "PLUGIN_ICON", "extension") 
                desc = getattr(plugin_module, "PLUGIN_DESCRIPTION", "")

                if hasattr(plugin_module, "setup") and callable(plugin_module.setup):
                    print(f"Loading plugin: {friendly_name}")
                    plugin_module.setup(app)
                    
                    app.state.plugins.append({
                        'id': plugin_name, 
                        'name': friendly_name,
                        'icon': icon,
                        'description': desc,
                        'status': 'Aktiv'
                    })

                    # ==========================================
                    # NEU: AUTOMATISCHES DEV-SEEDING!
                    # ==========================================
                    seed_file = os.path.join(plugin_path, "dev", "seed.json")
                    if os.path.exists(seed_file):
                        try:
                            with open(seed_file, 'r', encoding='utf-8') as f:
                                seed_data = json.load(f)
                            
                            with SessionLocal() as db:
                                for entity_type, records in seed_data.items():
                                    # Prüft, ob es für diesen Typ (z.B. "Server Node") schon Einträge in der DB gibt
                                    if db.query(DynamicEntity).filter(DynamicEntity.entity_type == entity_type).count() == 0:
                                        for record in records:
                                            db.add(DynamicEntity(entity_type=entity_type, payload=record))
                                        db.commit()
                                        print(f"   🌱 [Seeder] {len(records)} '{entity_type}' aus {plugin_name} in DB geladen.")
                        except Exception as seed_err:
                            print(f"   ❌ [Seeder] Fehler beim Laden von {seed_file}: {seed_err}")

        except Exception as e:
            print(f"Failed to load plugin '{plugin_name}': {e}")
            app.state.plugins.append({
                'id': plugin_name, 
                'name': plugin_name.replace('_', ' ').title(), 
                'icon': 'error', 
                'description': str(e),
                'status': 'Fehler'
            })