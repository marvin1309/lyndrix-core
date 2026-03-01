# app/main.py

import os
import sys
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from nicegui import ui, app as nicegui_app 

from core.bus import bus
from core.logger import setup_logging

# --- DER FIX: Nur noch aus der Fassade laden! ---
from core.services import vault_instance, db_instance, auth_service, boot_service

# --- Die Routen-Registrierungen ---
from core.components.auth.ui.routes import register_auth_routes
from core.components.settings.ui.routes import register_settings_routes
from core.components.vault.ui.routes import register_vault_routes
from core.components.dashboard.ui.routes import register_dashboard_routes

# --- Global UI ---
from ui.theme import apply_theme
from ui.maintenance import attach_maintenance_overlay
# ... (restliche main.py wie vorhin)
setup_logging()
app = FastAPI()

# ==========================================
# DER TÜRSTEHER (Middleware)
# ==========================================
@app.middleware("http")
async def boot_interceptor(request: Request, call_next):
    allowed_prefixes = ["/_nicegui", "/static", "/_pywebview", "/favicon.ico"]
    
    # Nutzt jetzt den boot_service aus dem neuen Pfad
    if getattr(boot_service, 'is_booting', True):
        if request.url.path == "/" or any(request.url.path.startswith(p) for p in allowed_prefixes):
            return await call_next(request)
        return RedirectResponse(url="/")
            
    return await call_next(request)

@bus.subscribe("system:reload")
def handle_reload(payload):
    os.execv(sys.executable, [sys.executable] + sys.argv)

# ==========================================
# ROOT ROUTING (Der Dirigent)
# ==========================================
@ui.page('/')
def entry_point():
    apply_theme()
    
    if getattr(app.state, 'maintenance', {}).get('active', False):
        attach_maintenance_overlay()
        return

    # 1. Vault Status prüfen (via vault_instance aus core/services.py)
    if vault_instance.ui_state == "needs_init":
        ui.navigate.to('/setup')
        return
        
    if vault_instance.ui_state == "needs_unseal":
        ui.navigate.to('/unseal')
        return

    # 2. Boot-Sperre (Ladescreen)
    if boot_service.is_booting or vault_instance.ui_state == "loading":
        ui.query('body').style('background-color: #09090b;')
        with ui.column().classes('w-full h-screen items-center justify-center gap-4'):
            ui.spinner('dots', size='3em', color='white')
            ui.label('Lyndrix Boot Sequence...').classes('text-zinc-500 text-sm tracking-widest uppercase')
        
        ui.timer(1.0, lambda: ui.navigate.to('/'), once=True)
        return

    # 3. System ist ready!
    if nicegui_app.storage.user.get('authenticated', False):
        ui.navigate.to('/dashboard')
    else:
        ui.navigate.to('/login')

# ==========================================
# SYSTEM START & REGISTRIERUNG
# ==========================================

# Wir registrieren alle Seiten der Komponenten
register_auth_routes()
register_settings_routes()
register_vault_routes()
register_dashboard_routes()

@app.on_event("startup")
async def startup_event():
    from core.logger import get_logger
    log = get_logger("LyndrixCore")
    log.info("🏗️ Lyndrix Core Engine startet...")
    bus.emit("system:started", {})

ui.run_with(app, storage_secret='lyndrix_v3_stable')