from nicegui import ui, app
from ui.theme import UIStyles
from core.bus import bus

# Sicherstellen, dass das Dictionary existiert
if not hasattr(app.state, 'maintenance_locks'):
    app.state.maintenance_locks = {}

@bus.subscribe("system:maintenance_mode")
def update_maintenance_state(payload):
    service = payload.get("service", "unknown")
    active = payload.get("active", False)
    
    if active:
        # Ein Service meldet ein Problem -> In die Liste der Blockaden aufnehmen
        app.state.maintenance_locks[service] = {
            "title": payload.get("title", "System-Wartung"),
            "msg": payload.get("msg", "Ein Dienst ist aktuell nicht erreichbar.")
        }
    else:
        # Ein Service gibt Entwarnung -> NUR seinen eigenen Eintrag löschen
        if service in app.state.maintenance_locks:
            del app.state.maintenance_locks[service]

def attach_maintenance_overlay():
    with ui.dialog().props('persistent maximized transition-show=fade transition-hide=fade') as maintenance_dialog:
        with ui.card().classes('w-full h-full flex flex-col items-center justify-center border-0 shadow-none lyndrix-glass-card'):
            ui.icon('warning', size='80px').classes('text-red-500 mb-6 animate-pulse')
            title_label = ui.label('').classes(UIStyles.TITLE_H1)
            msg_label = ui.label('').classes(UIStyles.TEXT_MUTED + ' text-lg mt-2 text-center max-w-md')
            ui.spinner('dots', size='3em', color='red').classes('mt-12')

    def check_status():
        locks = app.state.maintenance_locks
        if locks:
            # Wir zeigen immer die Meldung des ersten Fehlers an, der im Dictionary steht
            first_lock = list(locks.values())[0]
            title_label.set_text(first_lock["title"])
            msg_label.set_text(first_lock["msg"])
            if not maintenance_dialog.value:
                maintenance_dialog.open()
        else:
            if maintenance_dialog.value:
                maintenance_dialog.close()

    ui.timer(1.0, check_status)