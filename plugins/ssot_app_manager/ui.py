from nicegui import ui, run
import os
import yaml
import requests
import copy
from urllib.parse import urlparse
from git import Repo
from core.database import SessionLocal, DynamicEntity, get_all_records

from plugins.ssot_app_manager.settings import get_settings

LOCAL_CLONE_BASE_DIR = "./temp_ssot_apps"
ENTITY_TYPE = "SSOT Application"

ui_refresh_callbacks = []

def parse_service_yml(repo_name, file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            yaml_data = yaml.safe_load(file)

        return {
            'repo_name': repo_name,
            'raw_yaml_data': yaml_data,
            'name': yaml_data.get('service', {}).get('name', repo_name),
            'stage': yaml_data.get('service', {}).get('stage', 'Unknown'),
        }
    except Exception as e:
        print(f"Fehler beim Parsen von {file_path}: {e}")
        return None


def mount_ui(app, plugin_name):
    main_layout = app.state.main_layout

    @ui.page('/ssot-apps')
    @main_layout('SSOT Apps')
    def ssot_page():
        config = get_settings()

        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label("GitOps SSOT Editor").classes('text-2xl font-bold dark:text-zinc-100')

        if not config['pat_token']:
            ui.label('WARNUNG: Kein GitLab Token konfiguriert! Bitte in den Systemeinstellungen hinterlegen.').classes('text-red-500 text-sm font-bold mb-4 block p-4 bg-red-50 dark:bg-red-900/20 rounded-xl border border-red-200 dark:border-red-800')

        # --- DAS MODALE LOG-POPUP FÜR DEN SYNC ---
        with ui.dialog().props('persistent') as log_dialog:
            with ui.card().classes('w-full max-w-2xl p-6 border border-slate-700 !bg-slate-900 rounded-3xl shadow-2xl'):
                ui.label('Sync Progress').classes('text-lg font-bold text-white mb-2')
                log_view = ui.log(max_lines=50).classes('w-full h-64 text-xs font-mono bg-black text-green-400 p-3 rounded-xl border border-slate-800')
                
                with ui.row().classes('w-full justify-end mt-4'):
                    btn_close_log = ui.button('Schließen', on_click=log_dialog.close).props('unelevated rounded outline color=white')

        # --- DIE HAUPT-TABELLE (W-FULL) ---
        with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl overflow-x-auto'):
            
            with ui.row().classes('w-full justify-between items-start md:items-center mb-6 flex-col md:flex-row gap-4'):
                with ui.row().classes('gap-4 items-center w-full md:w-auto'):
                    ui.label('Managed Applications').classes('text-lg font-bold dark:text-zinc-200')
                    search = ui.input(placeholder='Search...').props('outlined dense clearable').classes('w-48')
                
                with ui.row().classes('gap-3'):
                    btn_sync = ui.button('Pull & Parse Group', icon='cloud_sync', color='indigo').props('unelevated rounded size=sm')
                    btn_push = ui.button('Push to Change Manager', icon='publish', color='primary').props('unelevated rounded size=sm')

            columns = [
                {'name': 'repo_name', 'label': 'Git Repository', 'field': 'repo_name', 'align': 'left', 'sortable': True, 'classes': 'font-mono text-xs'},
                {'name': 'name', 'label': 'Service Name', 'field': 'name', 'align': 'left', 'sortable': True},
                {'name': 'stage', 'label': 'Stage', 'field': 'stage', 'align': 'left', 'sortable': True},
                {'name': 'actions', 'label': 'Actions', 'field': 'actions', 'align': 'right'},
            ]
            
            table = ui.table(columns=columns, rows=[], row_key='repo_name').classes('w-full whitespace-nowrap no-shadow border dark:border-zinc-800')
            
            table.add_slot('body-cell-actions', '''
                <q-td :props="props" class="gap-2">
                    <q-btn unelevated rounded color="primary" icon="edit" label="Edit YAML" size="sm" @click="$parent.$emit('edit_yaml', props.row)" />
                </q-td>
            ''')

            # --- DER GRAFISCHE HYBRID-EDITOR ---
            def open_editor(e):
                row_data = e.args
                repo_name = row_data['repo_name']
                yaml_dict = copy.deepcopy(row_data.get('raw_yaml_data', {}))
                
                srv = yaml_dict.setdefault('service', {})
                cfg = yaml_dict.setdefault('config', {})
                integrations = cfg.setdefault('integrations', {})

                with ui.dialog() as editor_dialog:
                    with ui.card().classes('w-full max-w-4xl p-6 shadow-xl border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
                        with ui.row().classes('w-full justify-between items-center mb-4'):
                            ui.label(f"Configure: {repo_name}").classes('text-2xl font-bold dark:text-zinc-100')
                            ui.label(f"service.yml").classes('text-xs font-mono bg-slate-100 dark:bg-zinc-800 px-2 py-1 rounded text-slate-500')

                        with ui.tabs().classes('w-full text-primary') as tabs:
                            tab_gen = ui.tab('General', icon='tune')
                            tab_int = ui.tab('Integrations', icon='extension')
                            tab_adv = ui.tab('Advanced (YAML)', icon='data_object')

                        ui.separator().classes('mb-4 dark:bg-zinc-800')

                        with ui.tab_panels(tabs, value=tab_gen).classes('w-full bg-transparent'):
                            
                            with ui.tab_panel(tab_gen).classes('p-0 gap-4 flex flex-col'):
                                with ui.row().classes('w-full gap-4 flex-nowrap'):
                                    inp_name = ui.input('Service Name', value=srv.get('name', '')).classes('w-1/3').props('outlined dense')
                                    inp_repo = ui.input('Image Repo', value=srv.get('image_repo', '')).classes('w-1/3').props('outlined dense')
                                    inp_tag = ui.input('Image Tag', value=srv.get('image_tag', 'latest')).classes('w-1/3').props('outlined dense')
                                
                                with ui.row().classes('w-full gap-4 flex-nowrap'):
                                    inp_cat = ui.input('Category', value=srv.get('category', 'Uncategorized')).classes('w-1/3').props('outlined dense')
                                    inp_stage = ui.select(['dev', 'test', 'prod'], label='Stage', value=srv.get('stage', 'dev')).classes('w-1/3').props('outlined dense')
                                    inp_host = ui.input('Hostname', value=srv.get('hostname', '{{ service.name }}')).classes('w-1/3').props('outlined dense')

                                inp_icon = ui.input('Icon URL', value=srv.get('icon', '')).classes('w-full').props('outlined dense')
                                inp_desc = ui.textarea('Description', value=srv.get('description', '')).classes('w-full').props('outlined dense autogrow')

                            with ui.tab_panel(tab_int).classes('p-0 gap-4 flex flex-col'):
                                ui.label('Domain Configuration').classes('font-bold text-slate-700 dark:text-zinc-300')
                                with ui.row().classes('w-full gap-4 items-center'):
                                    inp_domain = ui.input('Domain Name', value=cfg.get('domain_name', 'local')).classes('w-1/2').props('outlined dense')
                                    sw_genhost = ui.switch('Generate Hostname Automatically', value=cfg.get('generate_hostname', True)).props('color=primary')

                                ui.separator().classes('my-2 dark:bg-zinc-800')
                                
                                ui.label('Features').classes('font-bold text-slate-700 dark:text-zinc-300')
                                with ui.row().classes('w-full gap-8 p-4 bg-slate-50 dark:bg-zinc-800/50 rounded-xl border border-slate-100 dark:border-zinc-700'):
                                    sw_home = ui.switch('Homepage Widget', value=integrations.get('homepage', {}).get('enabled', False)).props('color=indigo')
                                    sw_dns = ui.switch('AutoDNS (Wildcard)', value=integrations.get('autodns', {}).get('enabled', False)).props('color=emerald')
                                    sw_traefik = ui.switch('Traefik Routing', value=integrations.get('traefik', {}).get('enabled', False)).props('color=orange')

                            with ui.tab_panel(tab_adv).classes('p-0'):
                                ui.label('Edit deep structures like Ports, Volumes and Envs directly.').classes('text-xs text-slate-500 mb-2')
                                json_editor = ui.json_editor({'content': {'json': yaml_dict}}).classes('w-full h-96')

                        def save_changes():
                            # 1. Hole den aktuellen Stand aus dem Advanced Editor
                            content = json_editor.properties.get('content', {})
                            current_dict = content.get('json')
                            
                            # SICHERHEITSNETZ: Wenn der Editor leer ist (weil Tab nicht geöffnet), 
                            # nehmen wir das originale yaml_dict als Basis!
                            if not current_dict:
                                current_dict = copy.deepcopy(yaml_dict)
                            
                            # 2. Überschreibe ihn mit den Werten aus den grafischen Feldern
                            s = current_dict.setdefault('service', {})
                            c = current_dict.setdefault('config', {})
                            i = c.setdefault('integrations', {})

                            s['name'] = inp_name.value
                            s['image_repo'] = inp_repo.value
                            s['image_tag'] = inp_tag.value
                            s['category'] = inp_cat.value
                            s['stage'] = inp_stage.value
                            s['hostname'] = inp_host.value
                            s['description'] = inp_desc.value
                            s['icon'] = inp_icon.value

                            c['domain_name'] = inp_domain.value
                            c['generate_hostname'] = sw_genhost.value
                            
                            i.setdefault('homepage', {})['enabled'] = sw_home.value
                            i.setdefault('autodns', {})['enabled'] = sw_dns.value
                            i.setdefault('traefik', {})['enabled'] = sw_traefik.value

                            # 3. Baue den Datenbank-Payload
                            new_payload = {
                                'repo_name': repo_name,
                                'raw_yaml_data': current_dict,
                                'name': s['name'],
                                'stage': s['stage'],
                            }
                            
                            # 4. Schicke es an den Change Manager
                            app.state.event_bus.emit('change_requested', {
                                'entity_type': ENTITY_TYPE,
                                'action': 'UPDATE',
                                'before': row_data,
                                'after': new_payload
                            })
                            
                            ui.notify("SSOT Update zur Freigabe eingereicht!", type='info')
                            editor_dialog.close()

                        with ui.row().classes('w-full justify-end gap-2 mt-6 pt-4 border-t border-slate-200 dark:border-zinc-800'):
                            ui.button('Cancel', on_click=editor_dialog.close, color='slate').props('unelevated rounded outline')
                            ui.button('Save & Commit', on_click=save_changes, icon='save', color='primary').props('unelevated rounded')
                
                editor_dialog.open()

            table.on('edit_yaml', open_editor)

            def update_table(e=None):
                query = search.value.lower() if search.value else ''
                rows = get_all_records(ENTITY_TYPE)
                table.rows = [r for r in rows if any(query in str(v).lower() for v in r.values() if v is not None)] if query else rows
                table.update()
                if not rows: btn_push.disable()
                else: btn_push.enable()

            search.on('update:model-value', update_table)
            ui_refresh_callbacks.append(update_table)
            update_table()


        # --- SYNC LOGIK (ASYNC) ---
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
            btn_close_log.disable()
            
            log_dialog.open()
            log_view.clear()
            log_view.push("-> Starte GitLab API Abfrage...")
            
            os.makedirs(LOCAL_CLONE_BASE_DIR, exist_ok=True)
            found_apps = []

            try:
                headers = {"PRIVATE-TOKEN": cfg['pat_token']}
                group_encoded = cfg['group_path'].replace('/', '%2F')
                api_url = f"{cfg['gitlab_url'].rstrip('/')}/api/v4/groups/{group_encoded}/projects?include_subgroups=true&per_page=100"
                
                response = await run.io_bound(requests.get, api_url, headers=headers)
                if response.status_code != 200:
                    log_view.push(f"[ERROR] API Fehler {response.status_code}: {response.text}")
                    return
                
                projects = response.json()
                log_view.push(f"-> {len(projects)} Repositories in Gruppe gefunden.")

                for proj in projects:
                    repo_name = proj['name']
                    http_url = proj['http_url_to_repo']
                    
                    parsed_url = urlparse(http_url)
                    auth_url = f"{parsed_url.scheme}://oauth2:{cfg['pat_token']}@{parsed_url.netloc}{parsed_url.path}"
                    clone_path = os.path.join(LOCAL_CLONE_BASE_DIR, repo_name)
                    
                    def git_ops():
                        if not os.path.exists(clone_path):
                            Repo.clone_from(auth_url, clone_path)
                        else:
                            Repo(clone_path).remotes.origin.pull()
                    
                    await run.io_bound(git_ops)

                    service_path = os.path.join(clone_path, 'service.yml')
                    if os.path.exists(service_path):
                        app_data = parse_service_yml(repo_name, service_path)
                        if app_data:
                            found_apps.append(app_data)
                            log_view.push(f"   [OK] {repo_name} geparst.")
                    else:
                        log_view.push(f"   [SKIP] {repo_name} hat keine service.yml")

                log_view.push("-> Aktualisiere lokale Datenbank...")
                with SessionLocal() as db:
                    for app_data in found_apps:
                        existing = db.query(DynamicEntity).filter(
                            DynamicEntity.entity_type == ENTITY_TYPE,
                            DynamicEntity.payload['repo_name'].as_string() == app_data['repo_name']
                        ).first()
                        
                        if existing:
                            existing.payload = app_data
                        else:
                            db.add(DynamicEntity(entity_type=ENTITY_TYPE, payload=app_data))
                    db.commit()

                log_view.push("=======================================")
                log_view.push(f"SYNC ABGESCHLOSSEN. {len(found_apps)} Apps bereit.")
                update_table()
                
            except Exception as e:
                log_view.push(f"[CRITICAL ERROR] {str(e)}")
            finally:
                btn_sync.enable()
                btn_close_log.enable()

        # --- PUSH LOGIK FÜR DEN APPLICATION MANAGER (CMDB) ---
        def push_to_change_manager():
            apps_in_db = get_all_records(ENTITY_TYPE)
            if not apps_in_db: return
            
            existing_app_names = []
            if hasattr(app.state, 'data_providers') and 'applications' in app.state.data_providers:
                existing_app_names = list(app.state.data_providers['applications']().values())

            sent_count = 0
            for app_data in apps_in_db:
                action = 'UPDATE' if app_data.get('name') in existing_app_names else 'CREATE'
                
                # Wir holen uns sicher die Daten aus dem rohen YAML
                raw = app_data.get('raw_yaml_data', {})
                srv = raw.get('service', {})
                cfg = raw.get('config', {})
                
                # Robuster Hostname Fallback
                hname = srv.get('hostname', app_data.get('name', 'unknown'))
                if '{{' in hname: hname = app_data.get('name', 'unknown')
                url = f"https://{hname}.{cfg.get('domain_name', 'local')}"
                
                # Robuste Description Suche
                desc_text = srv.get('description', '')
                category = srv.get('category', 'Uncategorized')
                full_desc = f"[{category}] {desc_text}" if desc_text else f"[{category}] No description provided"
                
                app.state.event_bus.emit('change_requested', {
                    'entity_type': 'Application', # Ziel: Application Manager
                    'action': action,
                    'before': None,
                    'after': {
                        'name': app_data.get('name', 'Unknown App'),
                        'url': url,
                        'desc': full_desc, # Hier lag der Fehler!
                        'linked_servers': [],
                        'assigned_rules': []
                    }
                })
                sent_count += 1
            
            ui.notify(f"{sent_count} Anträge im Change Manager eingereicht!", type='positive')
        btn_sync.on_click(run_sync)
        btn_push.on_click(push_to_change_manager)