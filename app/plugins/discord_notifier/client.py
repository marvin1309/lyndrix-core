import requests
from datetime import datetime

# Globaler Zähler für das Dashboard wandert hierhin
notifications_sent = 0

def send_webhook(webhook_url: str, bot_name: str, entity: str, action: str, payload: dict, plugin_name: str = "Discord"):
    global notifications_sent
    
    embed_color = 5763719 if action == "CREATE" else 16753920 
    embed_fields = []
    
    for key, value in payload.items():
        if value != "" and value is not None:
            str_val = str(value)
            if len(str_val) > 100: str_val = str_val[:97] + "..."
            embed_fields.append({"name": str(key).capitalize(), "value": f"`{str_val}`", "inline": True})
            
    embed_fields = embed_fields[:25] # Discord Limit

    discord_msg = {
        "username": bot_name,
        "avatar_url": "https://cdn-icons-png.flaticon.com/512/3256/3256013.png", 
        "embeds": [{
            "title": f"🚀 {entity} Approval ausstehend!",
            "description": f"Ein **{action}** Antrag wartet im Change Manager auf Freigabe.\nZielzustand:",
            "color": embed_color,
            "fields": embed_fields,
            "footer": {"text": "Lyndrix Core System"},
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=discord_msg, timeout=2)
        if response.status_code == 204:
            notifications_sent += 1
            print(f"[{plugin_name}] Embed erfolgreich an Discord gesendet.")
            return True
        else:
            print(f"[{plugin_name}] Unerwarteter Discord Status: {response.status_code}")
            return False
    except Exception as e:
        print(f"[{plugin_name}] Fehler beim Senden an Discord: {e}")
        return False