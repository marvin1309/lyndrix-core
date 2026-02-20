from fastapi import FastAPI
from nicegui import ui, app as nicegui_app
from core.plugin_loader import load_plugins

STORAGE_SECRET = 'lyndrix_fixed_key_2026_zinc'

app = FastAPI()

# NATIVE FARBEN (Quasar)
nicegui_app.colors(
    primary='#3b82f6',
    dark='#18181b',      
    dark_page='#09090b'  
)

# WICHTIG: Kein globales ui.dark_mode() mehr! Wir übergeben nur noch 'app'
load_plugins(app)

ui.run_with(
    app,
    mount_path="/",
    storage_secret=STORAGE_SECRET
)

if __name__ == "__main__":
    import uvicorn
    # NEUER PORT: 8081 - Das tötet alle alten Zombie-Tabs sofort!
    uvicorn.run(app, host="0.0.0.0", port=8081)