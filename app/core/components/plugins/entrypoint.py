from core.components.plugins.logic.models import ModuleManifest
from .ui.routes import register_plugin_routes

manifest = ModuleManifest(
    id="lyndrix.core.plugins",
    name="Plugin Manager",
    version="1.0.0",
    description="Verwaltung von System-Erweiterungen.",
    author="Lyndrix",
    icon="extension",
    ui_route="/plugins",
    type="CORE",
    permissions={"subscribe": [], "emit": []}
)

def setup(ctx):
    ctx.log.info("Plugin-System wird registriert...")
    # Falls du die Plugins-Seite global registrieren willst:
    register_plugin_routes()