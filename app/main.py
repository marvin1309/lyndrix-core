import os
import sys
from fastapi import FastAPI
from nicegui import ui, app as nicegui_app 

from core.bus import bus
from core.services.vault.vault_service import vault_instance
from core.services.vault.crypto import KEY_FILE
from ui.maintenance import attach_maintenance_overlay # NEU
from ui.unseal_ui import render_unseal_page
from ui.login_ui import render_login_page 
from ui.layout import main_layout
from ui.theme import apply_theme

# Initialisierung...
from core.logger import setup_logging
setup_logging()

app = FastAPI()

# --- SYSTEM EVENTS ---
@bus.subscribe("system:reload")
def handle_reload(payload):
    os.execv(sys.executable, [sys.executable] + sys.argv)

# --- SETUP WIZARD ---
def render_setup_wizard():
    apply_theme()
    attach_maintenance_overlay() # Auch hier Wartungsschutz aktivieren
    # ... (Dein Setup Wizard Code bleibt wie besprochen)

# --- ROUTING LOGIK ---

@ui.page('/')
def entry_point():
    apply_theme()
    attach_maintenance_overlay() # WICHTIG: Root-Schutz
    
    # Im Wartungsmodus stoppen wir hier (Overlay deckt alles ab)
    if getattr(app.state, 'maintenance', {}).get('active', False):
        return

    if vault_instance.is_connected:
        if nicegui_app.storage.user.get('authenticated', False):
            ui.navigate.to('/dashboard')
        else:
            ui.navigate.to('/login')
        return

    if not os.path.exists(KEY_FILE):
        render_setup_wizard()
        return

    render_unseal_page()

@ui.page('/login')
def login_page():
    apply_theme()
    attach_maintenance_overlay() # Login-Schutz
    if nicegui_app.storage.user.get('authenticated', False):
        ui.navigate.to('/dashboard')
    render_login_page()

@ui.page('/dashboard')
@main_layout('Overview')
async def dashboard():
    from ui import pages
    pages.render_dashboard_page()

# ... (Andere Routen wie /settings, /plugins analog)

@app.on_event("startup")
async def startup_event():
    bus.emit("system:started", {})

ui.run_with(app, storage_secret='lyndrix_v3_stable')