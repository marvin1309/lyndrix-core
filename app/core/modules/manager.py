import importlib
import pkgutil
import os
import sys
from pydantic import ValidationError

from core.logger import get_logger
from .models import ModuleManifest
from .context import ModuleContext

log = get_logger("ModuleManager")

class ModuleManager:
    def __init__(self):
        # Die Registry speichert alle erfolgreich geladenen Module
        # Format: { "module_id": { "manifest": ..., "module": ..., "context": ... } }
        self.registry = {}

    def load_all(self):
        """Scant die definierten Ordner und lädt alle gültigen Module."""
        log.info("🚀 Starte Unified Module Loader...")
        
        # Basis-Verzeichnis ermitteln (sollte /app sein)
        base_path = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
        
        # 1. System-Komponenten (Priorität 1) laden
        core_path = os.path.join(base_path, "core", "components")
        self._discover_and_load("core.components", core_path)
        
        # 2. User-Plugins (Priorität 2) laden
        plugins_path = os.path.join(base_path, "plugins")
        self._discover_and_load("plugins", plugins_path)
        
        log.info(f"✅ Boot-Sequenz abgeschlossen: {len(self.registry)} Module geladen.")

    def _discover_and_load(self, package_prefix: str, directory: str):
        if not os.path.exists(directory):
            log.warning(f"⚠️ Verzeichnis nicht gefunden: {directory}")
            return

        log.debug(f"📂 Scanne Verzeichnis: {directory}")
        
        for loader, name, is_pkg in pkgutil.iter_modules([directory]):
            full_module_name = f"{package_prefix}.{name}"
            try:
                # 1. Modul dynamisch importieren
                module = importlib.import_module(full_module_name)
                
                # 2. Prüfen, ob es ein Lyndrix-Modul ist
                if not hasattr(module, 'manifest') or not hasattr(module, 'setup'):
                    log.debug(f"Überspringe {full_module_name} (Kein Manifest oder Setup gefunden)")
                    continue
                
                # 3. Manifest validieren (Pydantic übernimmt die Typprüfung!)
                raw_manifest = module.manifest
                if isinstance(raw_manifest, dict):
                    manifest = ModuleManifest(**raw_manifest)
                elif isinstance(raw_manifest, ModuleManifest):
                    manifest = raw_manifest
                else:
                    raise ValueError("Manifest muss ein Dictionary oder ModuleManifest-Objekt sein.")

                # 4. Doppel-ID Prüfung
                if manifest.id in self.registry:
                    log.error(f"💥 ID-Konflikt: Modul '{manifest.id}' ist bereits geladen!")
                    continue

                # 5. Kontext erstellen und Modul starten
                ctx = ModuleContext(manifest)
                module.setup(ctx)
                
                # 6. Erfolgreich in der Registry speichern
                self.registry[manifest.id] = {
                    "manifest": manifest,
                    "module": module,
                    "context": ctx
                }
                
                # Schönes Log-Feedback
                icon = "🧩" if manifest.type == "PLUGIN" else "⚙️"
                log.info(f"{icon} {manifest.type} geladen: {manifest.name} (v{manifest.version})")

            except ValidationError as ve:
                log.error(f"❌ Manifest-Fehler in {full_module_name}: {ve}")
            except Exception as e:
                log.error(f"💥 Fataler Fehler beim Laden von {full_module_name}: {e}", exc_info=True)

    def get_manifests(self):
        """Gibt eine Liste aller geladenen Manifeste zurück (z.B. für die UI)."""
        return [entry["manifest"] for entry in self.registry.values()]

# Singleton-Instanz für die gesamte App
module_manager = ModuleManager()