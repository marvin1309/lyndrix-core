import time
from nicegui import ui
from core.bus import bus
import asyncio

# Rate limiting state
_unseal_attempts = []
_MAX_ATTEMPTS = 5
_LOCKOUT_SECONDS = 60


def render_unseal_page():
    """Renders a minimal, isolated unseal mask with rate limiting."""

    ui.query('body').style('background-color: #09090b;')

    with ui.card().classes('absolute-center shadow-2xl p-8 rounded-3xl border border-zinc-800 bg-zinc-900 text-zinc-100 w-full max-w-md'):
        with ui.column().classes('items-center w-full gap-4'):
            ui.icon('lock', size='48px').classes('text-indigo-500 mb-2')
            ui.label('Lyndrix Vault').classes('text-2xl font-bold tracking-tight')
            ui.label('The system is encrypted. Please enter the Master Key.')\
                .classes('text-center text-sm text-zinc-400 mb-4')

            master_key = ui.input('Master Key')\
                .props('dark outlined password autofocus')\
                .classes('w-full mb-2')

            status_label = ui.label('').classes('text-xs font-mono')

            async def attempt_unseal():
                global _unseal_attempts
                now = time.time()

                # Purge old attempts outside the lockout window
                _unseal_attempts = [t for t in _unseal_attempts if now - t < _LOCKOUT_SECONDS]

                if len(_unseal_attempts) >= _MAX_ATTEMPTS:
                    remaining = int(_LOCKOUT_SECONDS - (now - _unseal_attempts[0]))
                    status_label.set_text(f'Too many attempts. Locked for {remaining}s.')
                    status_label.classes('text-red-500', remove='text-indigo-400')
                    return

                if not master_key.value:
                    ui.notify('Please enter a key.', type='warning')
                    return

                _unseal_attempts.append(now)
                status_label.set_text('Decrypting Vault...')
                status_label.classes('text-indigo-400', remove='text-red-500')

                bus.emit("vault:unseal_requested", {"key": master_key.value})

            # FIX: Use NiceGUI's async-aware on_click (passes coroutine properly)
            master_key.on('keydown.enter', attempt_unseal)

            ui.button('Unlock Vault', on_click=attempt_unseal)\
                .classes('w-full py-4 bg-indigo-600 hover:bg-indigo-500 rounded-xl font-bold transition-all')\
                .props('unelevated')

            with ui.row().classes('items-center gap-2 opacity-30 mt-4'):
                ui.element('div').classes('w-2 h-2 rounded-full bg-emerald-500')
                ui.label('Kernel Bus Active').classes('text-[10px] uppercase tracking-tighter')

    # Poll vault connection status in the UI context
    async def check_status():
        from core.services import vault_instance
        if vault_instance.is_connected:
            status_timer.cancel()
            ui.notify('Vault unlocked successfully!', type='positive')
            await asyncio.sleep(0.5)
            ui.navigate.to('/')

    status_timer = ui.timer(0.5, check_status)

    @bus.subscribe("vault:unseal_failed")
    def on_vault_failed(payload):
        status_label.set_text('Incorrect Master Key.')
        status_label.classes('text-red-500', remove='text-indigo-400')