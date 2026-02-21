from fastapi import FastAPI
from nicegui import ui, app as nicegui_app
import core.plugin_loader as plugin_loader
from core.security import bootstrap
import os
import asyncio
import sys

STORAGE_SECRET = 'lyndrix_fixed_key_2026_zinc'
KEY_FILE = "/data/security/vault_keys.enc"
# Key aus .env lesen (z.B. LYNDRIX_MASTER_KEY=mein_geheimnis)
AUTO_MASTER_KEY = os.getenv("LYNDRIX_MASTER_KEY")

app = FastAPI()

# 1. Grundzustand vorbereiten
plugin_loader.prepare_state(app)

# Reload Handler für den Event-Bus
def handle_system_reload(payload):
    print("[System] Reload angefordert. Starte Prozess neu...")
    os.execv(sys.executable, [sys.executable] + sys.argv)

if hasattr(app.state, 'event_bus'):
    app.state.event_bus.subscribe('system_reload_requested', handle_system_reload)

def setup_auth(fastapi_app):
    """Initialisiert das IAM System nach dem Unseal."""
    from core.auth.manager import auth_manager
    from core.auth.providers.local import LocalProvider
    from core.auth.ui import create_login_page
    from core.auth.seeder import seed_initial_admin
    
    print("[Auth] Initialisiere IAM-System...")
    seed_initial_admin()
    auth_manager.register_provider(LocalProvider(fastapi_app))
    fastapi_app.state.auth = auth_manager
    create_login_page(fastapi_app)

async def perform_auto_unseal():
    """
    Versucht das System automatisch zu entsperren, 
    wenn der Key in der Umgebungsvariable vorhanden ist.
    """
    if not os.path.exists(KEY_FILE) or not AUTO_MASTER_KEY:
        if AUTO_MASTER_KEY:
            print("[Bootstrap] ℹ️ Key vorhanden, aber Tresor-Datei fehlt noch (Setup nötig).")
        return False
    
    try:
        from core.components.secrets_manager.logic import VaultService
        app.state.vault = VaultService()
        
        # Versuch den Tresor mit dem ENV-Key zu öffnen
        if app.state.vault.unseal_and_connect(AUTO_MASTER_KEY):
            print("[Bootstrap] 🚀 Auto-Unseal erfolgreich (via ENV).")
            setup_auth(app)
            plugin_loader.initialize_all(app)
            return True
        else:
            print("[Bootstrap] ❌ Auto-Unseal fehlgeschlagen: Key aus ENV ist ungültig.")
    except Exception as e:
        print(f"[Bootstrap] ❌ Fehler während Auto-Unseal: {e}")
    return False

# --- LIFECYCLE HANDLER ---
@app.on_event("startup")
async def startup_event():
    # Führe Auto-Unseal beim Booten aus
    await perform_auto_unseal()

# --- ROUTES ---

if not os.path.exists(KEY_FILE):
    # --- ZUSTAND 1: SETUP MODE (Tresor existiert noch nicht) ---
    plugin_loader._scan_and_load_dir(app, 'core/components/lyndrix_core_ui', 'core.components', 'CORE')
    
    @ui.page('/')
    def setup_wizard():
        with ui.card().classes('absolute-center shadow-2xl p-8 rounded-3xl border border-zinc-800 bg-zinc-900 text-white w-full max-w-lg'):
            ui.label('Lyndrix Initialisierung').classes('text-2xl font-bold mb-4')
            ui.label('Bitte lege einen Master-Key fest.').classes('text-zinc-400 text-sm mb-6')
            
            pw = ui.input('Master Key', password=True).classes('w-full mb-4').props('dark outlined')
            pw_confirm = ui.input('Key bestätigen', password=True).classes('w-full mb-6').props('dark outlined')

            async def run_init():
                if pw.value != pw_confirm.value or not pw.value:
                    ui.notify('Keys passen nicht zusammen!', type='negative')
                    return
                
                try:
                    from core.components.secrets_manager.logic import VaultService
                    vault = VaultService()
                    init_data = vault.initial_vault_setup()
                    
                    if init_data:
                        encrypted_blob = bootstrap.encrypt_vault_data(pw.value, init_data)
                        os.makedirs(os.path.dirname(KEY_FILE), exist_ok=True)
                        with open(KEY_FILE, 'wb') as f:
                            f.write(encrypted_blob)
                        
                        ui.notify('Erfolg! System startet neu...', type='positive')
                        await asyncio.sleep(2)
                        app.state.event_bus.emit('system_reload_requested')
                except Exception as e:
                    ui.notify(f'Fehler: {str(e)}', type='negative')

            ui.button('Tresor erstellen & Starten', on_click=run_init).classes('w-full py-4 bg-blue-600 rounded-xl font-bold')

else:
    # --- ZUSTAND 2: SYSTEM BEREIT (Locked oder Auto-Unsealed) ---
    @ui.page('/')
    def index_page():
        # Falls durch Auto-Unseal schon offen -> sofort zum Login
        if hasattr(app.state, 'vault') and app.state.vault.is_connected:
            ui.navigate.to('/login')
        else:
            # Manuelle Entsperr-Maske
            with ui.card().classes('absolute-center shadow-2xl p-8 rounded-3xl border border-zinc-800 bg-zinc-900 text-white w-full max-w-md'):
                ui.label('System gesperrt').classes('text-2xl font-bold mb-6')
                master_pw = ui.input('Master Key', password=True).classes('w-full mb-6').props('dark outlined autofocus')

                async def attempt_unseal():
                    from core.components.secrets_manager.logic import VaultService
                    app.state.vault = VaultService()
                    if app.state.vault.unseal_and_connect(master_pw.value):
                        ui.notify('Tresor entsperrt!', type='positive')
                        setup_auth(app)
                        plugin_loader.initialize_all(app)
                        await asyncio.sleep(0.5)
                        ui.navigate.to('/login') 
                    else:
                        ui.notify('Falscher Schlüssel!', type='negative')

                ui.button('Entsperren', on_click=attempt_unseal).classes('w-full py-4 bg-emerald-600 rounded-xl')

# 3. NiceGUI Startup
ui.run_with(app, mount_path="/", storage_secret=STORAGE_SECRET)

if __name__ == "__main__":
    import uvicorn
    # Konfiguration: Nur Änderungen in core/ oder plugins/ triggern den Restart
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=8081, 
        reload=True,
        reload_dirs=["app/core", "app/plugins"],
        reload_includes=["*.py", "*.json"]
    )