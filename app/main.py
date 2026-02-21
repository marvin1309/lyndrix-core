import os
import sys
import asyncio
from fastapi import FastAPI
from nicegui import ui, app as nicegui_app 

from core.bus import bus
from core.services.vault.vault_service import vault_instance
from core.services.vault.crypto import KEY_FILE
from ui.maintenance import attach_maintenance_overlay
from ui.unseal_ui import render_unseal_page
from ui.login_ui import render_login_page 
from ui.layout import main_layout
from ui.theme import apply_theme

# Initialisierung...
from core.logger import setup_logging
setup_logging()

app = FastAPI()

# Globaler Status für die UI, um Race-Conditions beim Start zu vermeiden
SYSTEM_BOOTING = True

# --- SYSTEM EVENTS ---
@bus.subscribe("system:reload")
def handle_reload(payload):
    os.execv(sys.executable, [sys.executable] + sys.argv)

@bus.subscribe("system:started")
async def handle_boot(payload):
    global SYSTEM_BOOTING
    # Wir geben dem AutoUnsealManager und dem Vault-Loop 
    # 3.5 Sekunden Zeit, ihren Job zu machen, bevor wir der UI erlauben, 
    # manuelle Eingaben zu fordern.
    await asyncio.sleep(3.5)
    SYSTEM_BOOTING = False

# --- ECHTER SETUP WIZARD ---
def render_setup_wizard():
    apply_theme()
    attach_maintenance_overlay() 
    ui.query('body').style('background-color: #09090b;') 
    
    with ui.column().classes('w-full h-screen items-center justify-center bg-slate-50 dark:bg-zinc-950'):
        with ui.card().classes('shadow-2xl p-8 rounded-3xl border border-zinc-800 bg-zinc-900 text-zinc-100 w-full max-w-md'):
            with ui.column().classes('items-center w-full gap-4'):
                ui.icon('auto_awesome', size='48px').classes('text-emerald-500 mb-2')
                ui.label("System Initialisierung").classes('text-2xl font-bold tracking-tight')
                ui.label("Erster Start erkannt. Bitte lege einen sicheren Master-Key fest.").classes('text-center text-sm text-zinc-400 mb-4')
                
                master_key_input = ui.input("Neuer Master-Key").props('type=password outlined dark').classes('w-full mb-2')
                status_label = ui.label('').classes('text-xs font-mono')
                
                def do_init():
                    if len(master_key_input.value) < 8:
                        ui.notify("Der Key muss mindestens 8 Zeichen lang sein!", type="negative")
                        return
                    
                    status_label.set_text('⏳ Initialisiere Vault...')
                    status_label.classes('text-emerald-400')
                    
                    # Event abfeuern -> VaultService übernimmt
                    bus.emit("vault:init_requested", {"key": master_key_input.value})
                    
                ui.button("Vault Initialisieren", on_click=do_init)\
                    .classes('w-full py-4 bg-emerald-600 hover:bg-emerald-500 rounded-xl font-bold transition-all')\
                    .props('unelevated')

    # Dieser Timer läuft nur, während der User auf der Setup-Seite ist
    async def check_setup_status():
        # Sobald der VaultService im Hintergrund fertig ist, wird is_connected True
        if vault_instance.is_connected:
            setup_timer.cancel() # Wichtig: Timer stoppen
            ui.notify('System erfolgreich initialisiert!', type='positive')
            # Kurzer Delay für das Notify, dann Redirect auf Root
            ui.timer(1.0, lambda: ui.navigate.to('/'), once=True)

    setup_timer = ui.timer(1.0, check_setup_status)

# --- ROUTING LOGIK ---

@ui.page('/')
def entry_point():
    apply_theme()
    attach_maintenance_overlay() # WICHTIG: Root-Schutz
    
    # Im Wartungsmodus stoppen wir hier (Overlay deckt alles ab)
    if getattr(app.state, 'maintenance', {}).get('active', False):
        return

    # --- DER BOOTING-PUFFER ---
    # Wenn das System noch hochfährt und der Vault nicht offen ist,
    # zeigen wir kurz einen Ladebildschirm statt sofort den Setup-Wizard.
    if SYSTEM_BOOTING and not vault_instance.is_connected:
        ui.query('body').style('background-color: #09090b;')
        with ui.column().classes('w-full h-screen items-center justify-center gap-4'):
            ui.spinner('dots', size='3em', color='white')
            ui.label('Lyndrix Core startet...').classes('text-zinc-500 text-sm tracking-widest uppercase')
        
        # Die Seite lädt sich nach 1 Sekunde neu, um zu prüfen, ob der Boot-Vorgang 
        # oder der Auto-Unseal im Hintergrund inzwischen fertig ist.
        ui.timer(1.0, lambda: ui.navigate.to('/'), once=True)
        return

    # Wenn der Vault verbunden ist (manuell oder durch Auto-Unseal), ab zum Login/Dashboard
    if vault_instance.is_connected:
        if nicegui_app.storage.user.get('authenticated', False):
            ui.navigate.to('/dashboard')
        else:
            ui.navigate.to('/login')
        return

    # Wenn nach dem Booting immer noch kein Keyfile da ist -> Setup Wizard zeigen
    if not os.path.exists(KEY_FILE):
        render_setup_wizard()
        return

    # Wenn das Keyfile da ist, aber der Vault nicht connected -> Unseal Page zeigen
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

@ui.page('/settings')
@main_layout('Einstellungen')
async def settings_route():
    from ui import pages
    # Prüfe zur Sicherheit, ob der Vault noch offen ist
    if not vault_instance.is_connected:
        ui.navigate.to('/')
        return
    pages.render_settings_page()

@ui.page('/plugins')
@main_layout('Plugins')
async def plugins_route():
    from ui import pages
    # Prüfe zur Sicherheit, ob der Vault noch offen ist
    if not vault_instance.is_connected:
        ui.navigate.to('/')
        return
    pages.render_plugins_page()

# --- STARTUP LOGIK ---

@app.on_event("startup")
async def startup_event():
    # Wir loggen den Start kurz
    from core.logger import get_logger
    log = get_logger("LyndrixCore")
    log.info("🏗️ Lyndrix Core System wird gestartet...")
    
    # Event abfeuern, damit Auto-Unseal etc. anspringen
    bus.emit("system:started", {})

# NiceGUI starten
ui.run_with(app, storage_secret='lyndrix_v3_stable')