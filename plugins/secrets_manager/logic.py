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
        """Führt ein komplettes Auto-Setup des Vaults durch, falls er frisch ist."""
        try:
            print("[Vault] ⚠️ Vault ist noch nicht initialisiert. Starte Auto-Provisioning...")
            
            # 1. Vault initialisieren (1 Share, 1 Threshold für einfache lokale Nutzung)
            init_res = self.client.sys.initialize(secret_shares=1, secret_threshold=1)
            root_token = init_res['root_token']
            unseal_key = init_res['keys'][0]
            
            # 2. Keys sichern (Sehr wichtig für Notfälle und Reboots!)
            with open('vault_recovery_keys.json', 'w') as f:
                json.dump(init_res, f, indent=4)
            print("[Vault] ✅ Master-Keys in 'vault_recovery_keys.json' gesichert!")

            # 3. Vault entsperren
            self.client.sys.submit_unseal_key(unseal_key)
            print("[Vault] 🔓 Vault erfolgreich entsperrt.")

            # Temporär als Root anmelden für das Setup
            self.client.token = root_token

            # 4. KV Engine V2 aktivieren
            try:
                self.client.sys.enable_secrets_engine(backend_type='kv', path=self.mount_point, options={'version': '2'})
                print("[Vault] ✅ Secret Engine (KV v2) aktiviert.")
            except Exception as e:
                print(f"[Vault] Info: Secret Engine Setup - {e}")

            # 5. Policy anlegen
            policy = f"""
            path "{self.mount_point}/data/lyndrix/*" {{ capabilities = ["create", "read", "update", "delete", "list"] }}
            path "{self.mount_point}/metadata/lyndrix/*" {{ capabilities = ["create", "read", "update", "delete", "list"] }}
            """
            self.client.sys.create_or_update_policy(name='lyndrix-policy', policy=policy)
            print("[Vault] ✅ Policy 'lyndrix-policy' erstellt.")

            # 6. Userpass Auth aktivieren und User anlegen
            try:
                self.client.sys.enable_auth_method(method_type='userpass')
            except: pass
            
            if cfg.get('username') and cfg.get('password'):
                self.client.write(f"auth/userpass/users/{cfg['username']}", password=cfg['password'], policies='lyndrix-policy')
                print(f"[Vault] ✅ Vault User '{cfg['username']}' erfolgreich angelegt!")

            # Root Token wieder verwerfen (Zero Trust!)
            self.client.token = None
            print("[Vault] 🚀 AUTO-PROVISIONING ABGESCHLOSSEN!")

        except Exception as e:
            print(f"[Vault] 🛑 Fehler beim Auto-Provisioning: {e}")

    def connect(self):
        cfg = settings.get_settings()
        self.mount_point = cfg.get('mount_point', 'secret')
        
        if not cfg.get('vault_url'):
            self.is_connected = False
            return
            
        try:
            self.client = hvac.Client(url=cfg['vault_url'])
            
            # --- AUTO INIT LOGIK ---
            if not self.client.sys.is_initialized():
                self.auto_provision_vault(cfg)
                
            # --- AUTO UNSEAL LOGIK (Nach einem Container-Neustart) ---
            if self.client.sys.is_sealed():
                if os.path.exists('vault_recovery_keys.json'):
                    print("[Vault] Vault ist versiegelt. Führe Auto-Unseal aus...")
                    with open('vault_recovery_keys.json', 'r') as f:
                        keys = json.load(f)
                        self.client.sys.submit_unseal_key(keys['keys'][0])
                else:
                    print("[Vault] 🛑 Vault ist versiegelt und keine 'vault_recovery_keys.json' gefunden!")

            # --- NORMALE ANMELDUNG ---
            if cfg['auth_method'] == 'userpass' and cfg.get('username') and cfg.get('password'):
                self.client.auth.userpass.login(username=cfg['username'], password=cfg['password'])
            self.is_connected = self.client.is_authenticated()
            print(f"[Vault] Connection status: {self.is_connected}")
        except Exception as e:
            self.is_connected = False
            print(f"[Vault] Connection failed: {e}")

    def get_secret(self, secret_path: str, key: str = 'value'):
        """Zieht ein Secret aus Vault KV v2."""
        if not self.is_connected: return None
        try:
            res = self.client.secrets.kv.v2.read_secret_version(mount_point=self.mount_point, path=secret_path)
            return res['data']['data'].get(key)
        except Exception as e:
            print(f"[Vault] Error reading {secret_path}: {e}")
            return None

    def set_secret(self, secret_path: str, value: str, key: str = 'value'):
        """Schreibt ein Secret in Vault KV v2."""
        if not self.is_connected: raise Exception("Vault is not connected!")
        self.client.secrets.kv.v2.create_or_update_secret(
            mount_point=self.mount_point,
            path=secret_path,
            secret={key: value}
        )

def setup(app):
    # 1. Den Tresor hochfahren und global im State verankern!
    app.state.vault = VaultService()
    app.state.vault.connect()

    # 2. Navigation
    app.state.nav_items.setdefault('System', [])
    if not any(item['target'] == '/secrets' for item in app.state.nav_items['System']):
        app.state.nav_items['System'].append({'icon': PLUGIN_ICON, 'label': 'Vault Secrets', 'target': '/secrets'})

    # 3. In die Core-Settings injizieren
    if not hasattr(app.state, 'settings_providers'): app.state.settings_providers = []
    app.state.settings_providers.append({
        'name': PLUGIN_NAME,
        'icon': PLUGIN_ICON,
        'render': lambda: settings.render_settings_ui(app)
    })

    # 4. Frontend laden
    plugin_ui.mount_ui(app, PLUGIN_NAME)

    print(f"Plugin geladen: {PLUGIN_NAME}")