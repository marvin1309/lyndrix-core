import os
import sys
import asyncio
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from nicegui import ui, app as nicegui_app 

from core.bus import bus
from core.modules.manager import module_manager

# Service Instanzen
from core.services.vault.vault_service import vault_instance
from core.services.database.db_service import db_instance
from core.services.auth.auth_service import auth_service
from core.services.boot.boot_service import boot_service

# UI Komponenten
from ui.maintenance import attach_maintenance_overlay
from ui.setup_ui import render_setup_wizard # <-- NEU HIER IMPORTIERT
from ui.unseal_ui import render_unseal_page
from ui.login_ui import render_login_page 
from ui.theme import apply_theme

from core.logger import setup_logging
setup_logging()

app = FastAPI()

# ==========================================
# DER TÜRSTEHER (Middleware gegen 404)
# ==========================================
@app.middleware("http")
async def boot_interceptor(request: Request, call_next):
    allowed_prefixes = ["/_nicegui", "/static", "/_pywebview", "/favicon.ico"]
    
    if boot_service.is_booting:
        if request.url.path == "/":
            return await call_next(request)
            
        if not any(request.url.path.startswith(p) for p in allowed_prefixes):
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

    # 1. Fragt der Vault nach Initialisierung?
    if vault_instance.ui_state == "needs_init":
        render_setup_wizard()
        return
        
    # 2. Fragt der Vault nach dem Unseal-Key?
    if vault_instance.ui_state == "needs_unseal":
        render_unseal_page()
        return

    # 3. Boot-Sperre (Ladescreen)
    if boot_service.is_booting or vault_instance.ui_state == "loading":
        ui.query('body').style('background-color: #09090b;')
        with ui.column().classes('w-full h-screen items-center justify-center gap-4'):
            ui.spinner('dots', size='3em', color='white')
            ui.label('Lyndrix Boot Sequence...').classes('text-zinc-500 text-sm tracking-widest uppercase')
        
        ui.timer(1.0, lambda: ui.navigate.to('/'), once=True)
        return

    # 4. System ist ready!
    if nicegui_app.storage.user.get('authenticated', False):
        ui.navigate.to('/dashboard')
    else:
        ui.navigate.to('/login')

@ui.page('/login')
def login_page():
    apply_theme()
    attach_maintenance_overlay() 
    if nicegui_app.storage.user.get('authenticated', False):
        ui.navigate.to('/dashboard')
    render_login_page()

@app.on_event("startup")
async def startup_event():
    from core.logger import get_logger
    log = get_logger("LyndrixCore")
    log.info("🏗️ Lyndrix Core Engine startet...")
    bus.emit("system:started", {})

ui.run_with(app, storage_secret='lyndrix_v3_stable')