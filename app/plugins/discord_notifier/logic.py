from . import client
from . import handlers
from . import settings

PLUGIN_NAME = "Discord Notifier"
PLUGIN_ICON = "notifications_active"
PLUGIN_DESCRIPTION = "Sendet System-Events sicher via Vault-Webhook an Discord."

def provide_metrics():
    return [
        {
            'id': 'discord_notifs',
            'group': 'Plugin Metrics',
            'label': 'Discord Alerts Sent',
            'color_func': lambda: 'text-indigo-500',
            'icon': 'send',
            'get_val': lambda: str(client.notifications_sent)
        }
    ]

def setup(app):
    if hasattr(app.state, 'event_bus'):
        # Wir holen uns den isolierten Handler und abonnieren das Event
        handler = handlers.get_change_requested_handler(app, PLUGIN_NAME)
        app.state.event_bus.subscribe('change_requested', handler)
        print(f"[{PLUGIN_NAME}] Erfolgreich an Event-Bus angedockt.")