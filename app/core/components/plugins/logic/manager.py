import os
import sys
import importlib
import inspect
import asyncio
from core.logger import get_logger
from core.bus import bus
from core.components.database.logic.db_service import db_instance
from .models import ModuleManifest, PluginState
from .context import ModuleContext

log = get_logger("Core:ModuleManager")

class ModuleManager:
    def __init__(self):
        self.registry = {}
        current_file_path = os.path.abspath(__file__)
        self.base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file_path)))))
        


    def load_all(self):
        """Scans directories and loads all valid core components and plugins."""
        log.info(f"STARTUP: Initiating unified module discovery process in {self.base_path}")
        
        if self.base_path not in sys.path:
            sys.path.insert(0, self.base_path)
        
        # 1. Load System Components
        core_dir = os.path.join(self.base_path, "core", "components")
        self._scan_directory("core.components", core_dir, is_plugin=False)
        
        # 2. Load User Plugins
        plugin_dir = os.path.join(self.base_path, "plugins")
        self._scan_directory("plugins", plugin_dir, is_plugin=True)
        
        log.info(f"SUCCESS: Boot sequence finished. {len(self.registry)} modules registered")
        
        # --- THE CRITICAL TIMING FIX ---
        # Now that the registry is fully populated, we can safely read the DB states.
        # Since BootService waits for the DB to connect before calling load_all, 
        # we know the database is ready here.
        if db_instance.is_connected:
            asyncio.create_task(self._activate_saved_plugins())
        else:
            log.warning("PLUGIN_MANAGER: DB not connected at end of load_all. Falling back to bus listener.")
            bus.subscribe("db:connected")(self._activate_saved_plugins)

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
                    continue
                
                # Auto-fix dashes to underscores for Python imports
                if "-" in item:
                    new_name = item.replace("-", "_")
                    new_path = os.path.join(directory, new_name)
                    log.warning(f"AUTO-FIX: Renaming '{item}' to '{new_name}' to allow Python import.")
                    os.rename(item_path, new_path)
                    item = new_name 

                if not item.isidentifier():
                    log.error(f"SCAN_ERROR: Folder '{item}' has an invalid name! Only a-z, 0-9 and _ allowed.")
                    continue

                self.load_module(item, is_plugin=is_plugin)

    def load_module(self, module_name: str, is_plugin: bool = True):
        prefix = "plugins" if is_plugin else "core.components"
        full_module_path = f"{prefix}.{module_name}.entrypoint"
        
        try:
            module = importlib.import_module(full_module_path)
            
            if not hasattr(module, 'manifest'):
                log.warning(f"VALIDATION_ERROR: Module '{module_name}' missing 'manifest'")
                return False

            raw_manifest = module.manifest
            manifest = ModuleManifest(**raw_manifest) if isinstance(raw_manifest, dict) else raw_manifest

            if manifest.id in self.registry:
                return False

            ctx = ModuleContext(manifest)

            # Register as initializing/parked
            self.registry[manifest.id] = {
                "manifest": manifest,
                "module": module,
                "context": ctx,
                "status": "initializing" 
            }

            if not is_plugin:
                # Core modules boot instantly without waiting for the DB
                self._execute_setup(manifest.id)
                log.info(f"LOAD_SUCCESS: CORE '{manifest.name}' is online")
            else:
                # Plugins wait for the DB event
                log.info(f"LOAD_PENDING: PLUGIN '{manifest.name}' loaded, awaiting DB state...")

            return True

        except Exception as e:
            log.error(f"LOAD_ERROR: Failed to load '{module_name}': {e}")
            return False

    def _execute_setup(self, module_id):
        """Helper to safely execute the module's setup function."""
        entry = self.registry.get(module_id)
        if not entry:
            return

        module = entry["module"]
        ctx = entry["context"]
        
        if hasattr(module, 'setup'):
            if inspect.iscoroutinefunction(module.setup):
                asyncio.create_task(self._safe_async_setup(module, ctx, module_id))
            else:
                module.setup(ctx)
                entry["status"] = "active"

    async def _safe_async_setup(self, module, ctx, module_id):
        try:
            await module.setup(ctx)
            if module_id in self.registry:
                self.registry[module_id]["status"] = "active"
        except Exception as e:
            log.error(f"RUNTIME_ERROR: Async setup failed for '{module_id}': {e}")

    async def _activate_saved_plugins(self, payload=None):
        """Called when DB connects. Reads states and boots active plugins."""
        log.info("PLUGIN_MANAGER: Verifying plugin states from Database...")
        
        if not db_instance.SessionLocal:
            log.error("PLUGIN_MANAGER: SessionLocal missing during DB activation.")
            return

        with db_instance.SessionLocal() as session:
            for module_id, entry in self.registry.items():
                if entry["manifest"].type == "CORE":
                    continue
                
                # Fetch state from DB
                db_state = session.query(PluginState).filter(PluginState.module_id == module_id).first()
                
                # If it doesn't exist in DB, create it as disabled
                if not db_state:
                    db_state = PluginState(module_id=module_id, is_active=False)
                    session.add(db_state)
                    session.commit()

                if db_state.is_active:
                    log.info(f"DB_RESTORE: Activating plugin '{module_id}'")
                    self._execute_setup(module_id)
                else:
                    log.info(f"DB_RESTORE: Plugin '{module_id}' remains disabled.")
                    entry["status"] = "disabled"

    def toggle_module(self, module_id: str, active: bool):
        """Toggles the module state in RAM and persists it to the DB."""
        if module_id not in self.registry:
            return False
            
        # 1. Persist to DB
        if db_instance.SessionLocal:
            try:
                with db_instance.SessionLocal() as session:
                    db_state = session.query(PluginState).filter(PluginState.module_id == module_id).first()
                    if not db_state:
                        db_state = PluginState(module_id=module_id, is_active=active)
                        session.add(db_state)
                    else:
                        db_state.is_active = active
                    session.commit()
            except Exception as e:
                log.error(f"DB_ERROR: Failed to save toggle state: {e}")
                return False

        # 2. Update RAM status
        entry = self.registry[module_id]
        entry["status"] = "active" if active else "disabled"
        status_icon = "🟢" if active else "🔴"
        log.info(f"MODULE: {status_icon} '{module_id}' is now {'ACTIVE' if active else 'DISABLED'}")
        
        # 3. Boot it up if newly activated
        if active:
            self._execute_setup(module_id)
        else:
            log.warning(f"MODULE: '{module_id}' disabled. Restart container for full cleanup.")
            
        return True

    def get_manifests(self):
        return [entry["manifest"] for entry in self.registry.values()]

    def unload_module(self, module_id: str):
        if module_id not in self.registry:
            return False
        
        entry = self.registry[module_id]
        module_name = entry["module"].__name__
        del self.registry[module_id]
        
        if module_name in sys.modules:
            del sys.modules[module_name]
            
        log.info(f"UNLOAD: Module '{module_id}' unloaded from memory.")
        return True

    async def reload_module(self, module_id: str):
        if module_id not in self.registry:
            return False
            
        entry = self.registry[module_id]
        is_plugin = entry["manifest"].type == "PLUGIN"
        module_folder = entry["module"].__name__.split('.')[-2]

        self.unload_module(module_id)
        await asyncio.sleep(0.2)
        
        # 1. Load the module back into RAM
        success = self.load_module(module_folder, is_plugin=is_plugin)
        
        # 2. CRITICAL FIX: The Hot-Reload State Check
        # If the DB is already connected, we manually trigger the state check
        # instead of waiting for the boot sequence event.
        if success and is_plugin and db_instance.is_connected:
            await self._activate_saved_plugins()
            
        return success

module_manager = ModuleManager()