import hvac
import json
import os
import sys
from core.components.secrets_manager import settings
from core.components.secrets_manager import ui as plugin_ui
from core.security import bootstrap  # Dein Argon2/AES Modul


# core/components/secrets_manager/logic.py
PLUGIN_NAME = "Secrets Manager"
PLUGIN_ICON = "key"
NAV_LABEL = "Vault Secrets"
PLUGIN_DESCRIPTION = "Zentrale Verwaltung von Credentials via HashiCorp Vault / OpenBao."
NAV_TARGET = "/secrets"
NAV_ICON = PLUGIN_ICON

# Optional: Metriken für das Dashboard (Tab 1)
def provide_metrics():
    # Beispiel: Status der Vault-Verbindung
    # Angenommen, du hast Zugriff auf das Vault-Objekt
    from nicegui import app
    is_connected = getattr(app.state.vault, 'is_connected', False)
    return [{
        'label': 'Vault Status',
        'get_val': lambda: 'Online' if is_connected else 'Locked',
        'color': 'text-emerald-500' if is_connected else 'text-red-500'
    }]

# Optional: Ein Widget für das Dashboard (Tab 2)
def widget_render():
    from nicegui import ui, app
    ui.label("Vault Schnellzugriff").classes('font-bold')
    ui.button('Init Vault', on_click=lambda: ui.notify("Initialisiere..."))


class VaultService:
    def __init__(self):
        self.client = None
        self.mount_point = "secret"
        self.is_connected = False

    def initial_vault_setup(self):
        """Initialisiert den Vault-Server zum ersten Mal."""
        cfg = settings.get_settings()
        # WICHTIG: Nutze die URL aus den Settings (meist http://vault:8200)
        client = hvac.Client(url=cfg.get('vault_url', 'http://vault:8200'))
        
        try:
            # Prüfen ob er überhaupt erreichbar ist
            if not client.sys.is_initialized():
                print("[Vault] 🚀 Starte Initialisierung...")
                # Wir erstellen 1 Share / 1 Threshold (perfekt für Homelab)
                init_res = client.sys.initialize(secret_shares=1, secret_threshold=1)
                
                print("[Vault] ✅ Initialisierung erfolgreich.")
                return {
                    "root_token": init_res['root_token'],
                    "unseal_keys": init_res['keys']
                }
            else:
                print("[Vault] ℹ️ Vault ist bereits initialisiert.")
                return None
        except Exception as e:
            print(f"[Vault] 🛑 Fehler bei Erst-Initialisierung: {e}")
            raise e

    def unseal_and_connect(self, master_key: str):
        """
        Entschlüsselt die .enc Datei mit dem Master-Key,
        öffnet den Vault (unseal) und loggt sich ein. Alles nur im RAM.
        """
        cfg = settings.get_settings()
        self.mount_point = cfg.get('mount_point', 'secret').strip('/')
        
        try:
            # 1. Verschlüsselte Datei lesen
            if not os.path.exists(bootstrap.KEY_FILE):
                return False
                
            with open(bootstrap.KEY_FILE, 'rb') as f:
                encrypted_blob = f.read()
            
            # 2. Entschlüsseln via Argon2/AES (aus deiner bootstrap.py)
            vault_creds = bootstrap.decrypt_vault_data(master_key, encrypted_blob)
            
            # 3. Verbindung aufbauen
            self.client = hvac.Client(url=cfg['vault_url'])
            
            # 4. Vault aufschließen (Unseal)
            self.client.sys.submit_unseal_key(vault_creds['unseal_keys'][0])
            
            # 5. Mit Root-Token authentifizieren
            self.client.token = vault_creds['root_token']
            
            if self.client.is_authenticated():
                print("[Vault] 🔓 Tresor erfolgreich geöffnet und verbunden.")
                self.is_connected = True
                
                # OPTIONAL: Hier können wir direkt die KV-Engine prüfen/aktivieren
                self._ensure_kv_engine()
                return True
                
        except Exception as e:
            print(f"[Vault] 🛑 Unseal fehlgeschlagen: {e}")
            self.is_connected = False
            return False

    def _ensure_kv_engine(self):
        """Stellt sicher, dass die KV-Engine aktiviert ist."""
        try:
            self.client.sys.enable_secrets_engine(
                backend_type='kv', 
                path=self.mount_point, 
                options={'version': '2'}
            )
        except:
            pass # Bereits aktiviert

    def get_secret(self, secret_path: str, key: str = 'value'):
        """Liest ein Secret und bereinigt Pfade (verhindert Dopplung von 'secret/')"""
        if not self.is_connected: return None
        try:
            # Pfad-Bereinigung: 'secret/lyndrix/test' -> 'lyndrix/test'
            path = secret_path.strip().lstrip('/')
            if path.startswith(f"{self.mount_point}/"):
                path = path[len(self.mount_point)+1:]
            
            # Prefix sicherstellen
            if not path.startswith('lyndrix/'):
                path = f"lyndrix/{path}"

            res = self.client.secrets.kv.v2.read_secret_version(
                mount_point=self.mount_point, 
                path=path
            )
            return res['data']['data'].get(key)
        except Exception:
            return None

    def set_secret(self, secret_path: str, value: str, key: str = 'value'):
        """Schreibt ein Secret sicher in den Vault."""
        if not self.is_connected: raise Exception("Vault nicht verbunden!")
        
        path = secret_path.strip().lstrip('/')
        if path.startswith(f"{self.mount_point}/"):
            path = path[len(self.mount_point)+1:]
            
        if not path.startswith('lyndrix/'):
            path = f"lyndrix/{path}"

        self.client.secrets.kv.v2.create_or_update_secret(
            mount_point=self.mount_point,
            path=path,
            secret={key: value.strip()}
        )
        print(f"[Vault] ✅ Secret gespeichert: {self.mount_point}/{path}")

def setup(app):
    # Vault Service initialisieren, falls noch nicht geschehen
    if not hasattr(app.state, 'vault'):
        app.state.vault = VaultService()
        
    # UI Seiten (wie /secrets) mounten
    plugin_ui.mount_ui(app, PLUGIN_NAME)

    # --- NEU: Einstellungen in das System-Core Tab einspeisen ---
    # Sicherstellen, dass die Liste existiert
    if not hasattr(app.state, 'settings_providers'):
        app.state.settings_providers = []

    # Wir fügen die UI aus deiner settings.py hinzu
    app.state.settings_providers.append({
        'name': 'Vault Secrets Manager',
        'icon': 'security', # Passendes Icon
        'type': 'CORE',     # WICHTIG: Das packt es in den System-Core Tab!
        # Deine render_settings_ui erwartet 'app' als Parameter, 
        # unsere UI-Engine ruft es aber ohne Parameter auf. 
        # Daher nutzen wir lambda, um app durchzureichen:
        'render': lambda: settings.render_settings_ui(app) 
    })