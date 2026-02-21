from nicegui import ui
from datetime import datetime
import json

PLUGIN_NAME = "Live Event Viewer"
PLUGIN_ICON = "terminal"
PLUGIN_DESCRIPTION = "Zeigt alle internen System-Events in Echtzeit an (Live-Log)."

# Ein globaler Speicher für die letzten 100 Events
event_history = []

def widget_render():
    with ui.column().classes('w-full'):
        ui.label('Letzte 5 Events:').classes('text-xs font-bold')
        for ev in event_history[:5]:
            ui.label(f"{ev['time']} - {ev['topic']}").classes('text-[10px] font-mono')

def setup(app):

    # Eigene Kategorie "System" in der Sidebar
    app.state.nav_items.setdefault('System', [])
    if not any(item['target'] == '/events' for item in app.state.nav_items['System']):
        app.state.nav_items['System'].append({
            'icon': PLUGIN_ICON,
            'label': 'Event Log',
            'target': '/events'
        })

    main_layout = app.state.main_layout

    # --- DER SPY-MECHANISMUS (Monkey-Patch) ---
    if hasattr(app.state, 'event_bus'):
        original_emit = app.state.event_bus.emit

        def spied_emit(topic: str, payload: dict = None):
            timestamp = datetime.now().strftime('%H:%M:%S')
            payload_str = json.dumps(payload) if payload else "{}"
            
            event_history.insert(0, {'time': timestamp, 'topic': topic, 'payload': payload_str})
            
            if len(event_history) > 100:
                event_history.pop()
                
            original_emit(topic, payload)

        app.state.event_bus.emit = spied_emit

    # --- DIE UI ---
    @ui.page('/events')
    @main_layout('Event Log')
    def event_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('Live Event Log').classes('text-2xl font-bold dark:text-zinc-100')
            ui.button('Log leeren', icon='delete_sweep', on_click=lambda: clear_log()).props('unelevated outline rounded size=sm color=red')
            
        with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
            columns = [
                {'name': 'time', 'label': 'Time', 'field': 'time', 'align': 'left', 'classes': 'w-24 text-slate-500'},
                {'name': 'topic', 'label': 'Topic', 'field': 'topic', 'align': 'left', 'classes': 'font-bold text-indigo-500 dark:text-indigo-400'},
                {'name': 'payload', 'label': 'Payload JSON', 'field': 'payload', 'align': 'left', 'classes': 'text-xs opacity-80'},
            ]
            
            table = ui.table(columns=columns, rows=event_history, row_key='time', pagination=15).classes('w-full no-shadow border dark:border-zinc-800 font-mono')
            
            def clear_log():
                event_history.clear()
                table.update()

            ui.timer(1.0, lambda: table.update())

    print(f"Plugin geladen: {PLUGIN_NAME}")