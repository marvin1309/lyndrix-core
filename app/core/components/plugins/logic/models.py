from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

# --- NEW IMPORTS FOR DATABASE MODEL ---
from sqlalchemy import Column, String, Boolean
from core.components.database.logic.db_service import Base

# ==========================================
# 1. PYDANTIC MODELS (In-Memory Validation)
# ==========================================
class ModulePermissions(BaseModel):
    # Which Bus events is the module allowed to subscribe to?
    subscribe: List[str] = Field(default_factory=list)
    # Which events is it allowed to emit?
    emit: List[str] = Field(default_factory=list)
    # Which additional Vault paths can it access?
    vault_paths: List[str] = Field(default_factory=list)

class ModuleManifest(BaseModel):
    id: str = Field(..., description="Unique ID, e.g., 'lyndrix.core.iam' or 'lyndrix.discord'")
    name: str = Field(..., description="Display name in the UI")
    version: str = Field(..., description="Semantic versioning")
    description: str = Field(default="No description provided")
    author: str = Field(default="Unknown")
    icon: str = Field(default="extension")
    
    # IMPORTANT: Defines whether it belongs to the system or the user!
    type: str = Field(default="PLUGIN", description="'CORE' or 'PLUGIN'")
    # NEW: Only modules with a route will appear in the sidebar!
    ui_route: Optional[str] = Field(default=None, description="URL path for the sidebar")
    
    permissions: ModulePermissions = Field(default_factory=ModulePermissions)
    settings_schema: Dict[str, Any] = Field(default_factory=dict)

# ==========================================
# 2. SQLALCHEMY MODELS (Persistent Storage)
# ==========================================
class PluginState(Base):
    """
    Tracks whether a plugin is enabled or disabled by the user.
    This ensures state survives container restarts.
    """
    __tablename__ = "plugin_states"
    
    module_id = Column(String(100), primary_key=True)
    is_active = Column(Boolean, default=False)