import importlib
import os
import sys
from core.logger import get_logger
from .models import ModuleManifest
from .context import ModuleContext

log = get_logger("ModuleManager")

class ModuleManager:
    def __init__(self):
        self.registry = {}

    def load_all(self):
        """Scant die definierten Ordner und lädt alle gültigen Module."""
        log.info("🚀 Starte Unified Module Loader...")
        
        # Sicherstellen, dass /app im Python-Pfad ist
        base_path = "/app"
        if base_path not in sys.path:
            sys.path.insert(0, base_path)
        
        # 1. System-Komponenten laden
        core_path = os.path.join(base_path, "core", "components")
        self._discover_and_load("core.components", core_path)
        
        # 2. User-Plugins laden
        plugins_path = os.path.join(base_path, "plugins")
        self._discover_and_load("plugins", plugins_path)
        
        log.info(f"✅ Boot-Sequenz abgeschlossen: {len(self.registry)} Module geladen.")

    def _discover_and_load(self, package_prefix: str, directory: str):
        if not os.path.exists(directory):
            log.warning(f"⚠️ Verzeichnis nicht gefunden: {directory}")
            return

        for item in os.listdir(directory):
            item_path = os.path.join(directory, item)
            
            if os.path.isdir(item_path) and not item.startswith("__"):
                # PRÜFUNG: Existiert überhaupt ein Entrypoint?
                entrypoint_file = os.path.join(item_path, "entrypoint.py")
                if not os.path.exists(entrypoint_file):
                    continue # Überspringen ohne Error im Log
                
                full_module_name = f"{package_prefix}.{item}.entrypoint"
                try:
                    module = importlib.import_module(full_module_name)
                    
                    # Prüfen auf Pflicht-Attribute
                    if not hasattr(module, 'manifest') or not hasattr(module, 'setup'):
                        log.warning(f"⏩ {full_module_name} übersprungen: 'manifest' oder 'setup' fehlt.")
                        continue
                    
                    # Manifest validieren
                    raw_manifest = module.manifest
                    if isinstance(raw_manifest, dict):
                        manifest = ModuleManifest(**raw_manifest)
                    else:
                        manifest = raw_manifest

                    # Doppel-ID Prüfung
                    if manifest.id in self.registry:
                        log.warning(f"💥 ID-Konflikt: Modul '{manifest.id}' ist bereits registriert.")
                        continue

                    # Kontext erstellen und Setup ausführen
                    ctx = ModuleContext(manifest)
                    module.setup(ctx)
                    
                    # In Registry speichern
                    self.registry[manifest.id] = {
                        "manifest": manifest,
                        "module": module,
                        "context": ctx
                    }
                    
                    icon = "🧩" if manifest.type == "PLUGIN" else "⚙️"
                    log.info(f"{icon} {manifest.type} geladen: {manifest.name} (v{manifest.version})")

                except Exception as e:
                    log.error(f"💥 Fehler beim Laden von {full_module_name}: {e}")

    def get_manifests(self):
        """Gibt eine Liste aller geladenen Manifeste zurück."""
        return [entry["manifest"] for entry in self.registry.values()]

module_manager = ModuleManager()