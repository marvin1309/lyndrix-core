import importlib
import os
import sys
import inspect
from core.logger import get_logger
from .models import ModuleManifest
from .context import ModuleContext

log = get_logger("Core:ModuleManager")

class ModuleManager:
    def __init__(self):
        self.registry = {}
        
        # FIX: Wir holen uns den exakten, absoluten Pfad zur Laufzeit!
        # Diese Datei ist in: app/core/components/plugins/logic/manager.py
        # Wir wollen nach: app/
        current_file_path = os.path.abspath(__file__)
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))))

    def load_all(self):
        """Scans directories and loads all valid core components and plugins."""
        log.info(f"STARTUP: Initiating unified module discovery process in {self.base_path}")
        
        # Füge app/ zum Python Path hinzu, damit Importe wie 'core.xyz' klappen
        if self.base_path not in sys.path:
            sys.path.insert(0, self.base_path)
        
        # 1. Load System Components
        core_dir = os.path.join(self.base_path, "core", "components")
        self._scan_directory("core.components", core_dir, is_plugin=False)
        
        # 2. Load User Plugins
        plugin_dir = os.path.join(self.base_path, "plugins")
        self._scan_directory("plugins", plugin_dir, is_plugin=True)
        
        log.info(f"SUCCESS: Boot sequence finished. {len(self.registry)} modules registered")

    def load_module(self, module_name: str, is_plugin: bool = True):
        prefix = "plugins" if is_plugin else "core.components"
        full_module_path = f"{prefix}.{module_name}.entrypoint"
        
        try:
            # 1. Dynamic Import
            log.debug(f"DEBUG: Attempting to import {full_module_path}")
            module = importlib.import_module(full_module_path)
            
            # 2. Basic Validation
            if not hasattr(module, 'manifest'):
                log.warning(f"VALIDATION_ERROR: Module '{module_name}' missing 'manifest' attribute")
                return False

            # 3. Manifest Handling
            raw_manifest = module.manifest
            manifest = ModuleManifest(**raw_manifest) if isinstance(raw_manifest, dict) else raw_manifest

            if manifest.id in self.registry:
                log.debug(f"SKIP: Module ID '{manifest.id}' already registered.")
                return False

            # 4. Context Creation
            ctx = ModuleContext(manifest)

            # 5. REGISTRATION
            self.registry[manifest.id] = {
                "manifest": manifest,
                "module": module,
                "context": ctx,
                "status": "initializing"
            }

            # 6. Setup Execution
            if hasattr(module, 'setup'):
                if inspect.iscoroutinefunction(module.setup):
                    import asyncio
                    asyncio.create_task(self._safe_async_setup(module, ctx, manifest.id))
                else:
                    module.setup(ctx)
                    self.registry[manifest.id]["status"] = "active"

            log.info(f"LOAD_SUCCESS: {manifest.type} '{manifest.name}' (v{manifest.version}) is now online")
            return True

        except ImportError as e:
            log.error(f"IMPORT_ERROR: Cannot load '{module_name}'. Check imports in entrypoint.py! Error: {e}")
            return False
        except Exception as e:
            log.error(f"LOAD_ERROR: Failed to load module '{module_name}': {str(e)}", exc_info=True)
            return False

    async def _safe_async_setup(self, module, ctx, module_id):
        try:
            await module.setup(ctx)
            if module_id in self.registry:
                self.registry[module_id]["status"] = "active"
        except Exception as e:
            log.error(f"RUNTIME_ERROR: Async setup failed for '{module_id}': {str(e)}")

    def _scan_directory(self, package_prefix: str, directory: str, is_plugin: bool):
        if not os.path.exists(directory):
            log.warning(f"SYSTEM: Directory not found: {directory}")
            return

        for item in os.listdir(directory):
            if item.startswith("__") or item.startswith("."):
                continue
            
            item_path = os.path.join(directory, item)
            
            if os.path.isdir(item_path):
                entrypoint_path = os.path.join(item_path, "entrypoint.py")
                
                if not os.path.exists(entrypoint_path):
                    log.debug(f"SCAN_SKIP: No entrypoint.py found in '{item}'")
                    continue
                
                # FIX: Automatische Korrektur von Bindestrichen (GitHub Style -> Python Style)
                if "-" in item:
                    new_name = item.replace("-", "_")
                    new_path = os.path.join(directory, new_name)
                    log.warning(f"AUTO-FIX: Renaming '{item}' to '{new_name}' to allow Python import.")
                    os.rename(item_path, new_path)
                    item = new_name # Update für den Ladevorgang
                    # item_path ist jetzt ungültig, aber wir nutzen 'item' für load_module

                if not item.isidentifier():
                    log.error(f"SCAN_ERROR: Folder '{item}' has an invalid name! Only a-z, 0-9 and _ allowed.")
                    continue

                log.debug(f"SCAN_FOUND: Valid module directory '{item}' detected. Attempting load...")
                self.load_module(item, is_plugin=is_plugin)

    def get_manifests(self):
        return [entry["manifest"] for entry in self.registry.values()]

    def toggle_module(self, module_id: str, active: bool):
        """Aktiviert oder Deaktiviert ein Modul zur Laufzeit."""
        if module_id in self.registry:
            self.registry[module_id]["status"] = "active" if active else "disabled"
            status_icon = "🟢" if active else "🔴"
            log.info(f"MODULE: {status_icon} Module '{module_id}' is now {'ACTIVE' if active else 'DISABLED'}")
            # TODO: Hier könnte man auch Event-Bus Subscriptions pausieren
            return True
        return False

    def unload_module(self, module_id: str):
        """Entfernt ein Modul aus der Registry und versucht Cleanup."""
        if module_id not in self.registry:
            return False
        
        entry = self.registry[module_id]
        module_name = entry["module"].__name__
        
        # 1. Aus Registry entfernen
        del self.registry[module_id]
        
        # 2. Versuch, aus sys.modules zu entfernen (für Reload wichtig)
        # Das ist in Python tricky, aber wir versuchen das Entrypoint-Modul zu kicken
        if module_name in sys.modules:
            del sys.modules[module_name]
            
        log.info(f"UNLOAD: Module '{module_id}' unloaded from memory.")
        return True

    async def reload_module(self, module_id: str):
        """Führt Unload -> Load aus."""
        if module_id not in self.registry:
            return False
            
        entry = self.registry[module_id]
        is_plugin = entry["manifest"].type == "PLUGIN"
        # Extrahiere den Ordnernamen aus dem Modulpfad (z.B. plugins.my_plugin.entrypoint)
        module_folder = entry["module"].__name__.split('.')[-2]

        self.unload_module(module_id)
        
        import asyncio
        await asyncio.sleep(0.2)
        
        # Gezieltes Neuladen des einzelnen Moduls
        return self.load_module(module_folder, is_plugin=is_plugin)

module_manager = ModuleManager()