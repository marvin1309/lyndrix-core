import requests
from datetime import datetime
from plugins.discord_notifier import settings

PLUGIN_NAME = "Discord Notifier"
PLUGIN_ICON = "notifications_active"
PLUGIN_DESCRIPTION = "Sendet System-Events sicher via Vault-Webhook an Discord."

# Globaler Zähler für das Dashboard
notifications_sent = 0

def setup(app):
    
    # 1. In die Core-Settings einklinken
    if not hasattr(app.state, 'settings_providers'): app.state.settings_providers = []
    app.state.settings_providers.append({
        'name': PLUGIN_NAME,
        'icon': PLUGIN_ICON,
        'render': lambda: settings.render_settings_ui(app)
    })

    # 2. Dashboard Provider aktualisiert (mit Gruppe und korrekten Farben)
    def provide_discord_metrics():
        return [
            {
                'id': 'discord_notifs',
                'group': 'Plugin Metrics',
                'label': 'Discord Alerts Sent',
                'color_func': lambda: 'text-indigo-500',
                'icon': 'send',
                'get_val': lambda: str(notifications_sent)
            }
        ]

    if hasattr(app.state, 'dashboard_providers'):
        app.state.dashboard_providers.append(provide_discord_metrics)

    # 3. Der Event Listener
    def on_change_requested(data):
        global notifications_sent
        
        # Check ob Plugin in SQLite aktiviert ist
        cfg = settings.get_settings()
        if not cfg.get('enabled', True):
            return

        # LIVE PULL AUS DEM VAULT
        webhook_url = None
        try:
            webhook_url = app.state.vault.get_secret('lyndrix/discord_webhook')
        except Exception as e:
            print(f"[{PLUGIN_NAME}] Vault Error: {e}")
            
        if not webhook_url:
            print(f"[{PLUGIN_NAME}] Abbruch: Kein Discord-Webhook im Vault gefunden.")
            return

        print(f"[{PLUGIN_NAME}] Event empfangen, generiere Discord Embed...")

        entity = data.get('entity_type', 'Unknown')
        action = data.get('action', 'UNKNOWN')
        payload = data.get('after', {})
        
        embed_color = 5763719 if action == "CREATE" else 16753920 
        
        embed_fields = []
        for key, value in payload.items():
            if value != "" and value is not None:
                # Wir filtern lange YAMLs/Dicts raus, damit das Embed nicht sprengt
                str_val = str(value)
                if len(str_val) > 100: str_val = str_val[:97] + "..."
                
                embed_fields.append({
                    "name": str(key).capitalize(), 
                    "value": f"`{str_val}`",    
                    "inline": True                
                })
                
        embed_fields = embed_fields[:25] # Discord Limit

        discord_msg = {
            "username": cfg.get('bot_name', "Lyndrix Event Broker"),
            "avatar_url": "https://cdn-icons-png.flaticon.com/512/3256/3256013.png", 
            "embeds": [
                {
                    "title": f"🚀 {entity} Approval ausstehend!",
                    "description": f"Ein **{action}** Antrag wartet im Change Manager auf Freigabe.\nZielzustand:",
                    "color": embed_color,
                    "fields": embed_fields,
                    "footer": {
                        "text": "Lyndrix Core System"
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
            ]
        }
        
        try:
            response = requests.post(webhook_url, json=discord_msg, timeout=2)
            if response.status_code == 204:
                notifications_sent += 1
                print(f"[{PLUGIN_NAME}] Embed erfolgreich an Discord gesendet.")
            else:
                print(f"[{PLUGIN_NAME}] Unerwarteter Discord Status: {response.status_code}")
        except Exception as e:
            print(f"[{PLUGIN_NAME}] Fehler beim Senden an Discord: {e}")

    # Hier andocken:
    if hasattr(app.state, 'event_bus'):
        app.state.event_bus.subscribe('change_requested', on_change_requested)
        print(f"[{PLUGIN_NAME}] Erfolgreich an Event-Bus angedockt.")