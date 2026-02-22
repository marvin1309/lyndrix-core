from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class ModulePermissions(BaseModel):
    # Welche Bus-Events darf das Modul abonnieren?
    subscribe: List[str] = Field(default_factory=list)
    # Welche Events darf es selbst feuern?
    emit: List[str] = Field(default_factory=list)
    # Auf welche zusätzlichen Vault-Pfade darf es zugreifen?
    vault_paths: List[str] = Field(default_factory=list)

class ModuleManifest(BaseModel):
    id: str = Field(..., description="Eindeutige ID, z.B. 'lyndrix.core.iam' oder 'lyndrix.discord'")
    name: str = Field(..., description="Anzeigename in der UI")
    version: str = Field(..., description="Semantische Versionierung")
    description: str = Field(default="Keine Beschreibung")
    author: str = Field(default="Unknown")
    icon: str = Field(default="extension")
    
    # WICHTIG: Hier definieren wir, ob es zum System oder zum User gehört!
    type: str = Field(default="PLUGIN", description="'CORE' oder 'PLUGIN'")
    # NEU: Nur Module mit einer Route tauchen in der Sidebar auf!
    ui_route: Optional[str] = Field(default=None, description="URL-Pfad für die Sidebar")
    
    permissions: ModulePermissions = Field(default_factory=ModulePermissions)
    settings_schema: Dict[str, Any] = Field(default_factory=dict)