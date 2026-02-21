from . import config
from . import client

def get_change_requested_handler(app, plugin_name: str):
    """Factory-Funktion, die den Event-Listener mit dem app-Context erstellt."""
    
    def on_change_requested(data):
        cfg = config.get_settings()
        if not cfg.get('enabled', True):
            return

        try:
            webhook_url = app.state.vault.get_secret('lyndrix/discord_webhook')
        except Exception as e:
            print(f"[{plugin_name}] Vault Error: {e}")
            return
            
        if not webhook_url:
            print(f"[{plugin_name}] Abbruch: Kein Webhook im Vault gefunden.")
            return

        print(f"[{plugin_name}] Event empfangen, generiere Discord Embed...")
        
        # Aufruf des isolierten API-Clients
        client.send_webhook(
            webhook_url=webhook_url,
            bot_name=cfg.get('bot_name', "Lyndrix Event Broker"),
            entity=data.get('entity_type', 'Unknown'),
            action=data.get('action', 'UNKNOWN'),
            payload=data.get('after', {}),
            plugin_name=plugin_name
        )
        
    return on_change_requested