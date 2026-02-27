# 👨‍💻 Plugin Development Guide

Lyndrix Core ist als modulare Plattform konzipiert. Jedes Tool, das du baust (z. B. ein Docker-Dashboard oder ein Tool für Meeting-Bingo), ist ein isoliertes Plugin.

## Plugin Struktur

Ein Plugin lebt in einem eigenen Ordner unter `app/plugins/dein_plugin_name/` und benötigt mindestens eine `__init__.py`.

```text
app/plugins/mein_plugin/
├── __init__.py     # Hauptlogik & UI
└── assets/         # (Optional) Bilder, CSS, etc.

```

## Das Modul-Manifest

Jedes Plugin beginnt mit einem `ModuleManifest`. Dies sagt dem Core-System, wer du bist und was dein Plugin darf.

```python
from core.modules.models import ModuleManifest

manifest = ModuleManifest(
    id="lyndrix.plugin.beispiel",
    name="Mein erstes Plugin",
    version="1.0.0",
    description="Ein tolles neues Tool.",
    author="Dein Name",
    icon="rocket_launch",
    type="PLUGIN",
    ui_route="/mein-plugin", # Erzeugt automatisch einen Menüeintrag!
    permissions={"subscribe": ["system:boot_complete"], "emit": []}
)

```

## Die `setup(ctx)` Funktion

Der Core ruft beim Booten die `setup()` Funktion deines Plugins auf und übergibt einen Sandbox-Kontext (`ctx`).

```python
from nicegui import ui
from ui.layout import main_layout

def setup(ctx):
    ctx.log.info("Plugin wird geladen...")

    # Eine eigene UI Seite registrieren
    @ui.page('/mein-plugin')
    @main_layout('Mein Plugin')
    async def plugin_page():
        ui.label('Willkommen in meinem neuen Lyndrix Plugin!').classes('text-2xl')

    # Auf globale Events reagieren
    @ctx.subscribe('system:boot_complete')
    async def on_boot(payload):
        ctx.log.info("Juhu, das System ist hochgefahren!")

```

_Tipp: Schau dir das `Meeting Bingo` Plugin im Quellcode an, um ein Gefühl für Echtzeit-Komponenten (WebSockets) in NiceGUI zu bekommen._
