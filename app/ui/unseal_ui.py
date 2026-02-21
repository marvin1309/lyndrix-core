from nicegui import ui
from core.bus import bus
import asyncio

def render_unseal_page():
    """Rendert eine minimalistische, isolierte Unseal-Maske."""
    
    # Hintergrund-Styling für den "Locked"-Zustand
    ui.query('body').style('background-color: #09090b;') 

    with ui.card().classes('absolute-center shadow-2xl p-8 rounded-3xl border border-zinc-800 bg-zinc-900 text-zinc-100 w-full max-w-md'):
        with ui.column().classes('items-center w-full gap-4'):
            # Icon & Titel
            ui.icon('lock', size='48px').classes('text-indigo-500 mb-2')
            ui.label('Lyndrix Vault').classes('text-2xl font-bold tracking-tight')
            ui.label('Das System ist verschlüsselt. Bitte gib den Master-Key ein.')\
                .classes('text-center text-sm text-zinc-400 mb-4')

            # Input Feld
            master_key = ui.input('Master Key')\
                .props('dark outlined password autofocus')\
                .classes('w-full mb-2')\
                .on('keydown.enter', lambda: attempt_unseal())

            # Status-Anzeige
            status_label = ui.label('').classes('text-xs font-mono')

            async def attempt_unseal():
                if not master_key.value:
                    ui.notify('Bitte Key eingeben', type='warning')
                    return
                
                status_label.set_text('⏳ Entschlüssele Vault...')
                status_label.classes('text-indigo-400', remove='text-red-500')
                
                # Key über den Bus an den VaultService senden
                bus.emit("vault:unseal_requested", {"key": master_key.value})

            # Button
            ui.button('Tresor öffnen', on_click=attempt_unseal)\
                .classes('w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-bold transition-all')\
                .props('unelevated')

            # Kernel Info
            with ui.row().classes('items-center gap-2 opacity-30 mt-4'):
                ui.element('div').classes('w-2 h-2 rounded-full bg-emerald-500')
                ui.label('Kernel Bus Active').classes('text-[10px] uppercase tracking-tighter')

    # --- UI-REAKTION VIA POLLING ---
    # Da Bus-Events im Hintergrund-Thread laufen, prüfen wir hier 
    # im UI-Kontext, ob der Service die Verbindung hergestellt hat.
    
    async def check_status():
        from core.services.vault.vault_service import vault_instance
        if vault_instance.is_connected:
            status_timer.cancel()
            ui.notify('Vault erfolgreich geöffnet!', type='positive')
            await asyncio.sleep(0.5)
            ui.navigate.to('/') # Sicherer Redirect zum Login/Dashboard

    # Check alle 500ms
    status_timer = ui.timer(0.5, check_status)

    # Optional: Fehler-Listener (Nur für die Anzeige, Navigation bleibt oben beim Timer)
    @bus.subscribe("vault:unseal_failed")
    def on_vault_failed(payload):
        # Hinweis: UI-Updates hier können instabil sein, der Timer oben ist die primäre Logik
        status_label.set_text('❌ Falscher Master-Key')
        status_label.classes('text-red-500')