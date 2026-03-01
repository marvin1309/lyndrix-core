from core.components.plugins.logic.models import ModuleManifest

manifest = ModuleManifest(
    id="lyndrix.core.dashboard",
    name="System Dashboard",
    version="1.0.0",
    description="Das Haupt-Dashboard für die Systemüberwachung.",
    author="Lyndrix",
    icon="dashboard",
    ui_route="/dashboard",
    type="CORE",
    permissions={"subscribe": ["system:started"], "emit": []}
)

def setup(ctx):
    # Die Route wird bereits über main.py registriert, 
    # daher müssen wir hier nichts tun.
    ctx.log.info("Dashboard-Modul vom ModuleManager erkannt.")