import hvac
import json
import os
from plugins.secrets_manager import settings
from plugins.secrets_manager import ui as plugin_ui

PLUGIN_NAME = "Secrets Manager"
PLUGIN_ICON = "key"
PLUGIN_DESCRIPTION = "Zentrale Verwaltung von Credentials via HashiCorp Vault / OpenBao."

class VaultService:
    def __init__(self):
        self.client = None
        self.mount_point = "secret"
        self.is_connected = False

    def auto_provision_vault(self, cfg):
        """Führt ein komplettes Auto-Setup des Vaults durch inkl. ACL Policies."""
        try:
            root_token = None
            
            # 1. Vault initialisieren oder Unsealen
            if not self.client.sys.is_initialized():
                print("[Vault] ⚠️ Initialisiere neuen Vault...")
                init_res = self.client.sys.initialize(secret_shares=1, secret_threshold=1)
                with open('vault_recovery_keys.json', 'w') as f:
                    json.dump(init_res, f, indent=4)
                
                unseal_key = init_res['keys'][0]
                root_token = init_res['root_token']
                self.client.sys.submit_unseal_key(unseal_key)
                print("[Vault] ✅ Initialisiert und Unsealed.")
            else:
                if os.path.exists('vault_recovery_keys.json'):
                    with open('vault_recovery_keys.json', 'r') as f:
                        keys = json.load(f)
                    if self.client.sys.is_sealed():
                        self.client.sys.submit_unseal_key(keys['keys'][0])
                    root_token = keys['root_token']
                else:
                    print("[Vault] 🛑 Abbruch: Vault initialisiert, aber keine Recovery-Keys lokal gefunden!")
                    return

            # Temporäre Root-Authentifizierung für Setup-Aufgaben
            self.client.token = root_token

            # 2. KV Engine aktivieren (v2 für Versionierung)
            try:
                self.client.sys.enable_secrets_engine(backend_type='kv', path=self.mount_point, options={'version': '2'})
                print(f"[Vault] ✅ KV Engine auf '{self.mount_point}/' aktiviert.")
            except: pass

            # 3. ACL Policy definieren & schreiben
            policy_name = 'lyndrix-policy'
            policy_hcl = f"""
            path "{self.mount_point}/data/lyndrix/*" {{ capabilities = ["create", "read", "update", "delete", "list"] }}
            path "{self.mount_point}/metadata/lyndrix/*" {{ capabilities = ["create", "read", "update", "delete", "list"] }}
            """
            self.client.sys.create_or_update_policy(name=policy_name, policy=policy_hcl)
            print(f"[Vault] ✅ ACL Policy '{policy_name}' erstellt.")

            # 4. Auth-Methode & User konfigurieren
            try:
                self.client.sys.enable_auth_method(method_type='userpass')
            except: pass
            
            if cfg.get('username') and cfg.get('password'):
                self.client.write(
                    f"auth/userpass/users/{cfg['username']}", 
                    password=cfg['password'], 
                    token_policies=policy_name
                )
                print(f"[Vault] ✅ User '{cfg['username']}' mit '{policy_name}' verknüpft.")

            self.client.token = None 
            print("[Vault] 🚀 Auto-Provisioning erfolgreich abgeschlossen.")

        except Exception as e:
            print(f"[Vault] 🛑 Provisioning Error: {e}")

    def connect(self):
        cfg = settings.get_settings()
        self.mount_point = cfg.get('mount_point', 'secret').strip('/')
        
        if not cfg.get('vault_url'):
            self.is_connected = False
            return
            
        try:
            self.client = hvac.Client(url=cfg['vault_url'])
            
            if not self.client.sys.is_initialized():
                self.auto_provision_vault(cfg)
            elif self.client.sys.is_sealed():
                if os.path.exists('vault_recovery_keys.json'):
                    with open('vault_recovery_keys.json', 'r') as f:
                        keys = json.load(f)
                    self.client.sys.submit_unseal_key(keys['keys'][0])
                    print("[Vault] 🔓 Auto-Unseal durchgeführt.")

            if cfg.get('username') and cfg.get('password'):
                try:
                    self.client.auth.userpass.login(username=cfg['username'], password=cfg['password'])
                    self.is_connected = self.client.is_authenticated()
                except (hvac.exceptions.InvalidRequest, hvac.exceptions.VaultError):
                    print("[Vault] Login fehlgeschlagen. Erzwinge User-Reparatur...")
                    self.auto_provision_vault(cfg)
                    self.client.auth.userpass.login(username=cfg['username'], password=cfg['password'])
                    self.is_connected = self.client.is_authenticated()

            print(f"[Vault] Connection status: {self.is_connected}")
        except Exception as e:
            self.is_connected = False
            print(f"[Vault] Connection failed: {e}")

    def get_secret(self, secret_path: str, key: str = 'value'):
        """Liest ein Secret und bereinigt Pfade automatisch."""
        if not self.is_connected: return None
        try:
            # 1. Leerzeichen entfernen & führende Slashes löschen
            path = secret_path.strip().lstrip('/')
            
            # 2. Wenn der Pfad mit dem Mount-Point beginnt (z.B.
            # schneiden wir den Mount-Point ab, da hvac ihn separat als Argument will.
            if path.startswith(f"{self.mount_point}/"):
                path = path[len(self.mount_point)+1:]
            
            # 3. Policy-Schutz: Wenn lyndrix/ fehlt, fügen wir es hinzu
            if not path.startswith('lyndrix/'):
                path = f"lyndrix/{path}"

            res = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.mount_point, 
                path=path
            )
            return res['data']['data'].get(key)
        except Exception as e:
            # Nur echte Fehler loggen, keine 404s (Secret existiert einfach nicht)
            if "404" not in str(e):
                print(f"[Vault] Read Error: {e}")
            return None

    def set_secret(self, secret_path: str, value: str, key: str = 'value'):
        """Schreibt ein Secret und bereinigt Pfade automatisch."""
        if not self.is_connected: raise Exception("Vault is not connected!")
        
        # Pfad-Säuberung (wie oben)
        path = secret_path.strip().lstrip('/')
        if path.startswith(f"{self.mount_point}/"):
            path = path[len(self.mount_point)+1:]
            
        if not path.startswith('lyndrix/'):
            path = f"lyndrix/{path}"

        try:
            self.client.secrets.kv.v2.create_or_update_secret(
                mount_point=self.mount_point,
                path=path,
                secret={key: value.strip()} # Token selbst auch säubern!
            )
            print(f"[Vault] ✅ Secret erfolgreich gespeichert unter: {self.mount_point}/{path}")
        except Exception as e:
            print(f"[Vault] 🛑 Write Error: {e}")
            raise e
def setup(app):
    app.state.vault = VaultService()
    app.state.vault.connect()

    app.state.nav_items.setdefault('System', [])
    if not any(item['target'] == '/secrets' for item in app.state.nav_items['System']):
        app.state.nav_items['System'].append({'icon': PLUGIN_ICON, 'label': 'Vault Secrets', 'target': '/secrets'})

    if not hasattr(app.state, 'settings_providers'): app.state.settings_providers = []
    app.state.settings_providers.append({
        'name': PLUGIN_NAME,
        'icon': PLUGIN_ICON,
        'render': lambda: settings.render_settings_ui(app)
    })

    plugin_ui.mount_ui(app, PLUGIN_NAME)
    print(f"Plugin geladen: {PLUGIN_NAME}")