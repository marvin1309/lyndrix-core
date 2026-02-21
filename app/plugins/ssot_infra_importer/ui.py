from nicegui import ui, run
import os
import yaml
from urllib.parse import urlparse
from git import Repo
from core.database import SessionLocal, DynamicEntity, get_all_records

# Importiert die Settings-Logik!
from plugins.ssot_infra_importer.settings import get_settings

LOCAL_CLONE_DIR = "./temp_ssot_infra/iac-controller"
CACHE_ENTITY_TYPE = "SSOT Infra Cache"

def get_cached_servers():
    return get_all_records(CACHE_ENTITY_TYPE)

def clear_and_save_cache(servers):
    with SessionLocal() as db:
        db.query(DynamicEntity).filter(DynamicEntity.entity_type == CACHE_ENTITY_TYPE).delete()
        for s in servers:
            db.add(DynamicEntity(entity_type=CACHE_ENTITY_TYPE, payload=s))
        db.commit()

def parse_inventory_yml(file_path):
    parsed_servers = []
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            yaml_data = yaml.safe_load(file)

        sites = yaml_data.get('sites', {})
        for site_name, site_data in sites.items():
            hw_hosts = site_data.get('hardware_hosts', {})
            for hw_name, hw_config in hw_hosts.items():
                if hw_config.get('is_cluster') and 'nodes' in hw_config:
                    for node_name, node_config in hw_config['nodes'].items():
                        parsed_servers.append({'name': node_name, 'ipAddress': node_config.get('ansible_host', node_config.get('ip', '0.0.0.0')), 'node_type': 'HW', 'environment': 'PROD', 'status': 'ONLINE', 'notes': f"[IaC] Site: {site_name} | Role: {', '.join(node_config.get('roles', []))}"})
                else:
                    parsed_servers.append({'name': hw_name, 'ipAddress': hw_config.get('ansible_host', '0.0.0.0'), 'node_type': 'HW', 'environment': 'PROD', 'status': 'ONLINE', 'notes': f"[IaC] Site: {site_name} | Role: {', '.join(hw_config.get('roles', []))}"})

            stages = site_data.get('stages', {})
            for stage_name, stage_data in stages.items():
                hosts = stage_data.get('hosts', {})
                if not hosts: continue 
                
                for host_key, host_config in hosts.items():
                    node_type = "VM"
                    tf_config = host_config.get('terraform', {})
                    if tf_config.get('is_managed', False) and tf_config.get('node_name'): pass 

                    parsed_servers.append({'name': host_config.get('hostname', host_key), 'ipAddress': host_config.get('ansible_host', '0.0.0.0'), 'node_type': node_type, 'environment': stage_name.upper(), 'status': 'ONLINE', 'notes': f"[IaC] Site: {site_name} | Stage: {stage_name}"})
        return parsed_servers
    except Exception as e:
        print(f"Fehler beim Parsen: {e}")
        return []

def mount_ui(app, plugin_name):
    """Wird von logic.py aufgerufen, um die Routen zu registrieren."""
    main_layout = app.state.main_layout

    @ui.page('/ssot-infra')
    @main_layout('SSOT Infra')
    def ssot_page():
        config = get_settings()

        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label("IaC Infrastructure Importer").classes('text-2xl font-bold dark:text-zinc-100')

        # --- SICHERER VAULT CHECK ---
        vault_token = None
        try:
            vault_token = app.state.vault.get_secret('lyndrix/gitlab_pat')
        except Exception:
            pass

        if not vault_token:
            ui.label('WARNUNG: Kein GitLab Token im Vault konfiguriert! Bitte in den Systemeinstellungen hinterlegen.').classes('text-red-500 text-sm font-bold mb-4 block p-4 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800')
        # --- DAS MODALE LOG-POPUP ---
        # .props('persistent') verhindert, dass man es aus Versehen durch Klick daneben schließt
        with ui.dialog().props('persistent') as log_dialog:
            with ui.card().classes('w-full max-w-2xl p-6 border border-slate-700 !bg-slate-900 rounded-3xl shadow-2xl'):
                ui.label('Sync Progress').classes('text-lg font-bold text-white mb-2')
                log_view = ui.log(max_lines=50).classes('w-full h-64 text-xs font-mono bg-black text-teal-400 p-3 rounded-xl border border-slate-800')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    btn_close_log = ui.button('Schließen', on_click=log_dialog.close).props('unelevated rounded outline color=white')

        # --- DIE HAUPT-TABELLE (JETZT W-FULL) ---
        with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl overflow-x-auto'):
            
            with ui.row().classes('w-full justify-between items-start md:items-center mb-6 flex-col md:flex-row gap-4'):
                with ui.column().classes('gap-1'):
                    ui.label('Discovered Server Nodes').classes('text-lg font-bold dark:text-zinc-200')
                    # Zeigt als kleine Info an, welches Repo gerade angebunden ist
                    ui.label(f"Target: {config['file_path']}").classes('text-xs text-slate-500 font-mono')
                
                with ui.row().classes('gap-3'):
                    btn_sync = ui.button('Pull & Parse Repo', icon='cloud_sync', color='teal').props('unelevated rounded size=sm')
                    btn_push = ui.button('Push to Change Manager', icon='publish', color='primary').props('unelevated rounded size=sm')

            columns = [
                {'name': 'name', 'label': 'Hostname', 'field': 'name', 'align': 'left', 'sortable': True, 'classes': 'font-bold'},
                {'name': 'ipAddress', 'label': 'IP Address', 'field': 'ipAddress', 'align': 'left', 'sortable': True, 'classes': 'font-mono'},
                {'name': 'node_type', 'label': 'Type', 'field': 'node_type', 'align': 'left', 'sortable': True},
                {'name': 'environment', 'label': 'Env', 'field': 'environment', 'align': 'left'},
            ]
            
            table = ui.table(columns=columns, rows=get_cached_servers(), row_key='name').classes('w-full whitespace-nowrap no-shadow border dark:border-zinc-800')
            
            table.add_slot('body-cell-node_type', '''
                <q-td :props="props">
                    <q-chip :color="props.value === 'VM' ? 'primary' : (props.value === 'LXC' ? 'orange' : 'teal')" text-color="white" dense size="sm" class="font-bold">
                        {{ props.value }}
                    </q-chip>
                </q-td>
            ''')

            def update_table():
                rows = get_cached_servers()
                table.rows = rows
                table.update()
                if not rows: btn_push.disable()
                else: btn_push.enable()

            update_table()

        async def run_sync():
            cfg = get_settings()
            
            # --- NEU: TOKEN AUS DEM VAULT HOLEN ---
            pat_token = None
            try:
                pat_token = app.state.vault.get_secret('lyndrix/gitlab_pat')
            except Exception as e:
                ui.notify("Fehler bei der Verbindung zum Vault!", type='negative')
                return

            if not pat_token:
                ui.notify("Kein GitLab Token im Vault gefunden! Bitte in den Einstellungen hinterlegen.", type='warning')
                return
            
            # (In der Auth-URL Variable unten dann `pat_token` statt `cfg['pat_token']` verwenden!)
            # auth_url = f"{parsed_url.scheme}://oauth2:{pat_token}@{parsed_url.netloc}{parsed_url.path}"

            btn_sync.disable()
            btn_push.disable()
            btn_close_log.disable() # Close Button blockieren, solange der Sync läuft
            
            log_dialog.open()
            log_view.clear()
            log_view.push("-> Clone/Pull Infrastructure Repository...")
            
            os.makedirs(os.path.dirname(LOCAL_CLONE_DIR), exist_ok=True)

            try:
                parsed_url = urlparse(cfg['repo_url'])
                # KORREKTUR: Nutze pat_token (aus Vault), nicht cfg['pat_token']
                auth_url = f"{parsed_url.scheme}://oauth2:{pat_token}@{parsed_url.netloc}{parsed_url.path}"
                
                def git_ops():
                    if not os.path.exists(LOCAL_CLONE_DIR):
                        Repo.clone_from(auth_url, LOCAL_CLONE_DIR)
                    else:
                        Repo(LOCAL_CLONE_DIR).remotes.origin.pull()
                
                await run.io_bound(git_ops)
                log_view.push("-> Repo synchronisiert.")

                target_file = os.path.join(LOCAL_CLONE_DIR, cfg['file_path'])
                log_view.push(f"-> Analysiere {cfg['file_path']} ...")
                
                if os.path.exists(target_file):
                    parsed_servers = parse_inventory_yml(target_file)
                    clear_and_save_cache(parsed_servers)
                    log_view.push(f"[OK] {len(parsed_servers)} Server Nodes gefunden.")
                else:
                    log_view.push(f"[ERROR] Datei {target_file} nicht gefunden!")

                update_table()
                log_view.push("=======================================")
                log_view.push("SYNC ABGESCHLOSSEN. Du kannst das Fenster nun schließen.")
                
            except Exception as e:
                log_view.push(f"[CRITICAL ERROR] {str(e)}")
            finally:
                btn_sync.enable()
                btn_close_log.enable() # Close Button wieder freigeben

        # --- PUSH LOGIK ---
        def push_to_change_manager():
            servers_to_push = get_cached_servers()
            if not servers_to_push: return
            
            existing_servers = []
            if hasattr(app.state, 'data_providers') and 'server_nodes' in app.state.data_providers:
                existing_servers = list(app.state.data_providers['server_nodes']().values()) 

            sent_count = 0
            for srv_data in servers_to_push:
                clean_payload = {k: v for k, v in srv_data.items() if k != 'id'}
                action = 'UPDATE' if clean_payload['name'] in existing_servers else 'CREATE'
                
                app.state.event_bus.emit('change_requested', {
                    'entity_type': 'Server Node',
                    'action': action,
                    'before': None,
                    'after': clean_payload
                })
                sent_count += 1
            
            ui.notify(f"{sent_count} Server-Anträge im Change Manager eingereicht!", type='positive')
            btn_push.disable()

        btn_sync.on_click(run_sync)
        btn_push.on_click(push_to_change_manager)