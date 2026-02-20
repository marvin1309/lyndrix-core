from core.database import SessionLocal, DynamicEntity
from plugins.ssot_app_manager import settings
from plugins.ssot_app_manager import ui as plugin_ui
import os
import yaml
from git import Repo
from urllib.parse import urlparse

PLUGIN_NAME = "SSOT App Manager"
PLUGIN_ICON = "edit_document"
PLUGIN_DESCRIPTION = "GitOps Editor für die SSOT Application Definitions."
ENTITY_TYPE = "SSOT Application"
LOCAL_CLONE_BASE_DIR = "./temp_ssot_apps"

def setup(app):
    # 1. Navigation
    app.state.nav_items.setdefault('Infrastructure', [])
    if not any(item['target'] == '/ssot-apps' for item in app.state.nav_items['Infrastructure']):
        app.state.nav_items['Infrastructure'].append({'icon': PLUGIN_ICON, 'label': 'SSOT Apps', 'target': '/ssot-apps'})

    # 2. Settings im Core registrieren
    if not hasattr(app.state, 'settings_providers'):
        app.state.settings_providers = []
        
    app.state.settings_providers.append({
        'name': PLUGIN_NAME,
        'icon': PLUGIN_ICON,
        'render': lambda: settings.render_settings_ui(app)
    })

    # ==========================================
    # NEU: DIE GIT PUSH LOGIK (ROBUST)
    # ==========================================
    def push_to_gitlab(repo_name, raw_yaml_data):
        try:
            # SICHERHEITSNETZ 1: Niemals eine leere YAML schreiben!
            if not raw_yaml_data or len(raw_yaml_data.keys()) == 0:
                print(f"[{PLUGIN_NAME}] 🛑 FATAL: raw_yaml_data ist leer! Breche Git Push ab, um Datenverlust zu verhindern.")
                return False

            cfg = settings.get_settings()
            pat_token = None
            try:
                pat_token = app.state.vault.get_secret('lyndrix/gitlab_pat')
            except Exception: pass
            
            if not pat_token:
                print(f"[{PLUGIN_NAME}] 🛑 Git Push abgebrochen: Kein Token im Vault gefunden.")
                return False

            clone_path = os.path.join(LOCAL_CLONE_BASE_DIR, repo_name)
            if not os.path.exists(clone_path):
                print(f"[{PLUGIN_NAME}] 🛑 Repo {repo_name} lokal nicht gefunden. Bitte erst syncen.")
                return False

            # 1. Die neue YAML-Datei formatgetreu schreiben
            service_path = os.path.join(clone_path, 'service.yml')
            with open(service_path, 'w', encoding='utf-8') as f:
                yaml.dump(raw_yaml_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

            # 2. Git Operationen starten
            repo = Repo(clone_path)
            
            # Lyndrix Bot Identität setzen
            with repo.config_writer() as git_config:
                git_config.set_value('user', 'name', 'Lyndrix Bot')
                git_config.set_value('user', 'email', 'bot@lyndrix.local')
            
            # Datei zum Staging hinzufügen
            repo.git.add('service.yml')
            
            # SICHERHEITSNETZ 2: Prüfen, ob es wirklich Änderungen gab
            try:
                # Versuche zu committen. Wirft einen Fehler, wenn die Datei unverändert ist!
                repo.git.commit('-m', 'chore(lyndrix): update service.yml via Web-UI')
            except Exception as e:
                if "nothing to commit" in str(e).lower() or "nichts zu committen" in str(e).lower():
                    print(f"[{PLUGIN_NAME}] ℹ️ Keine echten Änderungen in {repo_name} erkannt. Nichts zu pushen.")
                    return True
                else:
                    raise e # Andere Fehler weiterwerfen
                
            # Auth URL für den Push sicher zusammenbauen
            group_path = cfg['group_path'].strip('/')
            base_url = cfg['gitlab_url'].rstrip('/')
            repo_url = f"{base_url}/{group_path}/{repo_name}.git"
            
            parsed = urlparse(repo_url)
            auth_url = f"{parsed.scheme}://oauth2:{pat_token}@{parsed.netloc}{parsed.path}"
            
            # Remote URL kurzzeitig mit Token versehen und Pushen
            origin = repo.remotes.origin
            origin.set_url(auth_url)
            
            print(f"[{PLUGIN_NAME}] ⏳ Sende Push an GitLab ({repo_name})...")
            push_info = origin.push()
            
            # Push-Status auswerten
            for info in push_info:
                if info.flags & info.ERROR:
                    print(f"[{PLUGIN_NAME}] 🛑 Push fehlgeschlagen: {info.summary}")
                    return False
            
            print(f"[{PLUGIN_NAME}] ✅ Git Push erfolgreich für: {repo_name}")
            return True
                
        except Exception as e:
            print(f"[{PLUGIN_NAME}] 🛑 Fehler beim Git Push: {e}")
            return False

    # 3. Datenbank Schreib-Logik (Lauscht auf den Editor)
    def on_change_approved(payload):
        if payload.get('entity_type') != ENTITY_TYPE: return
        action = payload['action']
        approved_data = payload['after']
        repo_name = approved_data.get('repo_name')
        
        with SessionLocal() as db:
            if action == 'CREATE':
                db.add(DynamicEntity(entity_type=ENTITY_TYPE, payload=approved_data))
                db.commit()
            elif action == 'UPDATE':
                entity = db.query(DynamicEntity).filter(
                    DynamicEntity.entity_type == ENTITY_TYPE,
                    DynamicEntity.payload['repo_name'].as_string() == repo_name
                ).first()
                
                if entity:
                    entity.payload = approved_data
                    db.commit()
                    print(f"[{PLUGIN_NAME}] UPDATE für {repo_name} in lokaler DB gespeichert.")
                    
                    # --- NACH DEM SPEICHERN: PUSH INS GITLAB ---
                    raw_yaml = approved_data.get('raw_yaml_data')
                    if raw_yaml:
                        push_to_gitlab(repo_name, raw_yaml)
                        
        # UI Table Update triggern
        for cb in plugin_ui.ui_refresh_callbacks: cb()

    if hasattr(app.state, 'event_bus'): 
        app.state.event_bus.subscribe('change_approved', on_change_approved)

    # 4. Frontend laden
    plugin_ui.mount_ui(app, PLUGIN_NAME)

    print(f"Plugin geladen: {PLUGIN_NAME}")