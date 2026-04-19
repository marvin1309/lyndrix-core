"""
Lyndrix Core Plugin API — Stable Surface v1.0

Plugins SHOULD import from this package rather than reaching into
core.components.* internals. Breaking changes will bump __api_version__.
"""
__api_version__ = "1.0.0"

from core.bus import bus as event_bus, GlobalEventBus
from core.logger import get_logger
from core.components.plugins.logic.models import ModuleManifest, ModulePermissions
from core.components.plugins.logic.context import ModuleContext
from core.components.database.logic.db_service import db_instance, Base

__all__ = [
    "__api_version__",
    "event_bus",
    "GlobalEventBus",
    "get_logger",
    "ModuleManifest",
    "ModulePermissions",
    "ModuleContext",
    "db_instance",
    "Base",
]
