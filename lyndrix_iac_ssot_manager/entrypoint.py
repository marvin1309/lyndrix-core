import yaml
import os
import json
from nicegui import ui
from ui.layout import main_layout
from ui.theme import UIStyles
from core.components.plugins.logic.models import ModuleManifest
from core.bus import bus

manifest = ModuleManifest(
    id="lyndrix.plugin.iac",
    name="IaC SSOT Manager",
    version="3.1.0",
    icon="account_tree",
    type="PLUGIN",
    min_core_version="1.0.0",
    auto_enable_on_install=False,
    ui_route="/iac",
    dependencies=[{"id": "lyndrix.service.git", "version_constraint": ">=0.1.1"}],
    permissions={"subscribe": ["git:status_update", "vault:ready_for_data"], "emit": ["git:sync", "git:commit_push"]}
)

# ==========================================
# GLOBALER STATE
# ==========================================
state = {
    "repo_id": "iac_env_main",
    "config_meta": {
        "mode": "remote", 
        "url": "",
        "token": "",
        "managed_files": [] 
    },
    "yaml_data": {},        
    "raw_strings": {},      
    "active_file": None,    
    "is_syncing": False,
    "_async_status_msg": None
}

def get_repo_dir():
    return f"/data/storage/git_repos/{state['repo_id']}"

def scan_repo_for_yaml():
    repo_dir = get_repo_dir()
    if not os.path.exists(repo_dir): return []
    files = []
    for root, dirs, filenames in os.walk(repo_dir):
        if '.git' in dirs: dirs.remove('.git')
        for f in filenames:
            if f.endswith(('.yml', '.yaml')):
                rel = os.path.relpath(root, repo_dir)
                files.append(f if rel == "." else f"{rel}/{f}")
    return sorted(files)

def load_from_disk(ctx):
    state["yaml_data"].clear()
    state["raw_strings"].clear()
    repo_dir = get_repo_dir()
    
    for f in state["config_meta"].get("managed_files", []):
        path = os.path.join(repo_dir, f)
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as file:
                    content = file.read()
                    state["raw_strings"][f] = content
                    state["yaml_data"][f] = yaml.safe_load(content) or {}
            except Exception as e:
                ctx.log.error(f"Failed to parse {f}: {e}")
                state["raw_strings"][f] = f"# Parse Error: {e}"
                state["yaml_data"][f] = {}
    return True

def save_to_disk():
    repo_dir = get_repo_dir()
    for f in state["config_meta"].get("managed_files", []):
        path = os.path.join(repo_dir, f)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as file:
            d_vars = state["yaml_data"].get(f, {})
            if "toplevel_vars" in d_vars or "sites" in d_vars:
                yaml.dump(d_vars, file, default_flow_style=False, sort_keys=False)
            else:
                file.write(state["raw_strings"].get(f, ""))

# ==========================================
# EINSTELLUNGEN (SETTINGS UI)
# ==========================================
def render_settings_ui(ctx):
    temp_meta = state["config_meta"].copy()
    if "managed_files" not in temp_meta: temp_meta["managed_files"] = []

    def save_config():
        state["config_meta"] = temp_meta.copy()
        ctx.set_secret("iac_configuration", json.dumps(state["config_meta"]))
        ui.notify("IaC Konfiguration gespeichert!", type="positive")
        load_from_disk(ctx)

    with ui.column().classes('w-full gap-4 pt-2'):
        ui.label('Repository Konfiguration').classes('text-sm text-slate-500 font-bold uppercase tracking-widest')
        ui.select({'remote': 'Remote Repository (GitLab/GitHub)', 'local': 'Local Only (Kein Push)'}, label='Modus', value=temp_meta['mode']).bind_value(temp_meta, 'mode').classes('w-full').props('outlined dense')
        ui.input('Repository URL (leer lassen bei local)').bind_value(temp_meta, 'url').classes('w-full').props('outlined dense')
        current_token = {"value": ctx.get_secret("iac_git_token") or ""}
        ui.input('Access Token').bind_value(current_token, 'value').props('type=password outlined dense').classes('w-full').on('change', lambda e: ctx.set_secret("iac_git_token", e.value))
        ui.separator().classes('my-2 dark:bg-zinc-800')
        
        ui.label('Verwaltete SSOT-Dateien').classes('text-sm text-slate-500 font-bold uppercase tracking-widest')
        available_files = scan_repo_for_yaml()
        
        if available_files:
            ui.select(available_files, multiple=True, label='Dateien auswählen').bind_value(temp_meta, 'managed_files').classes('w-full').props('outlined use-chips')
        else:
            with ui.card().classes(f'w-full {UIStyles.CARD_BASE} bg-slate-50 dark:bg-zinc-900/50'):
                ui.label("Keine YAML-Dateien gefunden. Bitte im Dashboard 'Sync Git' klicken.").classes(UIStyles.TEXT_MUTED)
        
        with ui.row().classes('w-full justify-end mt-4'):
            ui.button('Speichern', on_click=save_config, icon='save', color='primary').props('unelevated rounded size=sm')

# ==========================================
# HAUPT LOGIK & UI (IaC DASHBOARD)
# ==========================================
def setup(ctx):
    
    @ctx.subscribe("vault:ready_for_data")
    async def load_vault_config(payload=None):
        stored = ctx.get_secret("iac_configuration")
        if stored:
            try:
                state["config_meta"] = json.loads(stored)
                if "managed_files" not in state["config_meta"]: state["config_meta"]["managed_files"] = []
            except: pass

    @ui.page('/iac')
    @main_layout('IaC SSOT Manager')
    async def iac_page():
        client = ui.context.client
        if not state["yaml_data"]: load_from_disk(ctx)

        def trigger_refresh():
            form_container.refresh()

        def open_add_key_dialog(target_dict):
            with ui.dialog() as d, ui.card().classes(f'{UIStyles.CARD_BASE} min-w-[350px]'):
                ui.label('Neues Feld hinzufügen').classes(UIStyles.TITLE_H3)
                k = ui.input('Schlüssel (Key)').classes('w-full mb-2').props('outlined dense autofocus')
                t = ui.select({
                    'str': 'Text (String)',
                    'int': 'Zahl (Integer)',
                    'bool': 'Ja/Nein (Boolean)',
                    'list': 'Liste',
                    'dict': 'Gruppe (Verschachtelt)'
                }, value='str', label='Datentyp').classes('w-full').props('outlined dense')
                
                def save():
                    if not k.value:
                        ui.notify('Schlüsselname darf nicht leer sein', type='warning')
                        return
                    
                    val = ""
                    if t.value == 'int': val = 0
                    elif t.value == 'bool': val = False
                    elif t.value == 'list': val = []
                    elif t.value == 'dict': val = {}
                    
                    target_dict[k.value] = val
                    ui.notify(f'Feld {k.value} hinzugefügt', type='positive')
                    d.close()
                    trigger_refresh()
                    
                with ui.row().classes('w-full justify-end mt-4'):
                    ui.button('Abbrechen', on_click=d.close).props('flat text-color=slate')
                    ui.button('Hinzufügen', on_click=save).props('color=primary rounded')
            d.open()

        def render_dict_editor(data_dict, exclude_keys=None):
            """Rendert ein Dictionary und unterstützt nun auch komplexe Listen (Objekte/Dicts)."""
            if exclude_keys is None: exclude_keys = []
            
            for key, val in list(data_dict.items()):
                if key in exclude_keys: continue
                
                with ui.row().classes('w-full items-start gap-2 mb-2 no-wrap'):
                    
                    def del_key(k=key):
                        del data_dict[k]
                        trigger_refresh()

                    # STRING, INT, BOOL
                    if isinstance(val, (str, int, float, bool)) or val is None:
                        is_secret = "token" in key or "password" in key
                        is_key = "key" in key and isinstance(val, str) and "ssh-rsa" in val
                        
                        if is_key:
                            ui.textarea(key).bind_value(data_dict, key).classes('flex-grow font-mono text-xs').props('outlined')
                        else:
                            input_props = 'outlined dense'
                            if is_secret: input_props += ' type=password'
                            ui.input(key).bind_value(data_dict, key).classes('flex-grow').props(input_props)
                            
                        ui.button(icon='delete', on_click=del_key).props('flat round size=sm color=red').classes('mt-1').tooltip('Feld löschen')
                            
                    # LISTEN (KÖNNEN JETZT AUCH DICTS ENTHALTEN)
                    elif isinstance(val, list):
                        # Wir verpacken die Liste in eine kleine Karte
                        with ui.card().classes(f'flex-grow {UIStyles.CARD_BASE} !p-4 border-l-4 border-l-blue-500 bg-slate-50/50 dark:bg-zinc-900/30 shadow-none'):
                            with ui.row().classes('w-full justify-between items-center mb-4 border-b border-slate-200 dark:border-zinc-800 pb-2'):
                                ui.label(key).classes('text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-widest')
                                ui.button(icon='delete', on_click=del_key).props('flat round size=sm color=red').tooltip('Ganze Liste löschen')

                            # Fall 1: Einfache Liste (nur Strings/Ints)
                            if val and all(isinstance(i, (str, int, float)) for i in val):
                                temp_state = {"val": ", ".join(map(str, val))}
                                def update_simple_list(e, td=data_dict, tk=key):
                                    td[tk] = [x.strip() for x in e.value.split(',') if x.strip()]
                                ui.input("Komma getrennt").bind_value(temp_state, 'val').on('change', update_simple_list).classes('w-full').props('outlined dense')
                            
                            # Fall 2: Komplexe Liste (enthält Objekte/Dicts oder ist leer)
                            else:
                                for idx, list_item in enumerate(val):
                                    with ui.row().classes('w-full items-start gap-4 border-b border-slate-200 dark:border-zinc-800 pb-4 mb-4 no-wrap'):
                                        ui.label(f"#{idx+1}").classes('font-bold text-slate-400 mt-2 w-6')
                                        
                                        with ui.column().classes('flex-grow gap-2'):
                                            if isinstance(list_item, dict):
                                                render_dict_editor(list_item)
                                            elif isinstance(list_item, str):
                                                def update_str(e, l=val, i=idx): l[i] = e.value
                                                ui.input(value=list_item, on_change=update_str).classes('w-full').props('outlined dense')
                                                
                                        def delete_list_item(l=val, i=list_item):
                                            l.remove(i)
                                            trigger_refresh()
                                        ui.button(icon='delete', on_click=delete_list_item).props('flat round color=red size=sm mt-1')

                                # Actions zum Hinzufügen in Listen
                                with ui.row().classes('gap-2 mt-2'):
                                    def add_dict_item(l=val):
                                        # Versuche, die Struktur des ersten Elements zu kopieren
                                        new_item = {k: "" for k in l[0].keys()} if l and isinstance(l[0], dict) else {}
                                        l.append(new_item)
                                        trigger_refresh()
                                    def add_string_item(l=val):
                                        l.append("")
                                        trigger_refresh()
                                    
                                    ui.button('+ Objekt', icon='data_object', on_click=add_dict_item).props('outline size=sm color=primary rounded')
                                    ui.button('+ Text', icon='text_fields', on_click=add_string_item).props('outline size=sm color=slate rounded')

                    # VERSCHACHTELTE DICTS (GRUPPEN)
                    elif isinstance(val, dict):
                        with ui.card().classes(f'flex-grow {UIStyles.CARD_BASE} border-dashed border-2 p-4 bg-slate-50/50 dark:bg-zinc-900/30 shadow-none'):
                            with ui.row().classes('w-full justify-between items-center mb-4 border-b border-slate-200 dark:border-zinc-800 pb-2'):
                                ui.label(key).classes('text-sm font-bold text-slate-500 dark:text-zinc-400 uppercase tracking-widest')
                                ui.button(icon='delete', on_click=del_key).props('flat round size=sm color=red').tooltip('Ganze Gruppe löschen')
                            render_dict_editor(val)
                    else:
                        ui.label(f"Unsupported type for {key}").classes('text-red-500 text-xs')

            ui.button('Feld/Gruppe hinzufügen', icon='add_circle_outline', on_click=lambda d=data_dict: open_add_key_dialog(d)).props('flat size=sm color=primary').classes('mt-2')

        def render_services_ui(host_cfg):
            """UI Bereich zur Verwaltung der Docker/Ansible Services eines Hosts."""
            if 'services' not in host_cfg or host_cfg['services'] is None:
                host_cfg['services'] = []
            services = host_cfg['services']
            
            with ui.row().classes('w-full items-center justify-between mt-6 mb-2 border-t border-slate-200 dark:border-zinc-800 pt-4'):
                ui.label('Deployed Services').classes('text-sm font-bold uppercase tracking-widest text-slate-500')
                
                def add_service():
                    services.append({
                        "name": "new-service",
                        "state": "present",
                        "git_repo": "https://gitlab.int.fam-feser.de/aac-application-definitions/",
                        "git_version": "main",
                        "deploy_type": "docker_compose"
                    })
                    trigger_refresh()
                ui.button('Service hinzufügen', icon='add', on_click=add_service).props('outline size=sm color=primary rounded')

            if not services:
                ui.label('Keine Services konfiguriert.').classes('italic text-xs text-slate-500')
            else:
                for svc in services:
                    # THEME.PY INTEGRATION FÜR SERVICES
                    with ui.card().classes(f'w-full p-4 mb-2 border-l-4 border-l-indigo-500 {UIStyles.CARD_BASE} shadow-none'):
                        with ui.row().classes('w-full justify-between items-start gap-4 no-wrap'):
                            with ui.column().classes('flex-grow gap-2'):
                                with ui.row().classes('w-full gap-2 no-wrap'):
                                    ui.input('Service Name').bind_value(svc, 'name').classes('flex-grow').props('outlined dense')
                                    ui.select(['present', 'absent'], label='State').bind_value(svc, 'state').classes('w-32').props('outlined dense')
                                    ui.input('Deploy Type').bind_value(svc, 'deploy_type').classes('w-40').props('outlined dense')
                                
                                with ui.row().classes('w-full gap-2 no-wrap'):
                                    ui.input('Git Repository URL').bind_value(svc, 'git_repo').classes('flex-grow').props('outlined dense')
                                    ui.input('Branch/Tag').bind_value(svc, 'git_version').classes('w-32').props('outlined dense')
                            
                            def del_svc(s=svc):
                                services.remove(s)
                                trigger_refresh()
                            ui.button(icon='delete', on_click=del_svc).props('flat round color=red size=sm').classes('mt-1')

        # ----------------------------------------------------
        # START DER HAUPT-UI
        # ----------------------------------------------------
        with ui.column().classes('w-full gap-4'):
            
            with ui.row().classes(f'w-full justify-between items-center {UIStyles.CARD_BASE}'):
                with ui.column().classes('gap-0'):
                    ui.label('IaC SSOT Manager').classes('text-2xl font-bold')
                    mode_text = "Remote GitLab" if state["config_meta"]["mode"] == "remote" else "Lokaler Modus"
                    ui.label(f"{mode_text} | {len(state['config_meta'].get('managed_files', []))} SSOT-Files").classes('text-xs text-slate-500')
                
                with ui.row().classes('gap-3'):
                    def do_sync():
                        state["is_syncing"] = True
                        meta = state["config_meta"]
                        payload = {"repo_id": state["repo_id"]}
                        if meta["mode"] == "remote":
                            payload["url"] = meta["url"]
                            payload["token"] = ctx.get_secret("iac_git_token")
                        bus.emit("git:sync", payload)
                        ui.notify("Starte Git Sync...", type="info")

                    def do_push():
                        save_to_disk() 
                        is_local = state["config_meta"]["mode"] == "local"
                        bus.emit("git:commit_push", {"repo_id": state["repo_id"], "is_local": is_local})
                        ui.notify("Speichere Konfiguration...", type="info")

                    ui.button('Sync Git', icon='sync', on_click=do_sync).props('outline rounded color=primary')
                    ui.button('Save & Build', icon='build', on_click=do_push).props('rounded color=primary')

            @ui.refreshable
            def form_container():
                managed = state["config_meta"].get("managed_files", [])
                
                if not managed:
                    with ui.card().classes(f'w-full {UIStyles.CARD_BASE} items-center justify-center text-center p-12 mt-4'):
                        ui.icon('folder_off', size='48px').classes('text-slate-400 mb-4')
                        ui.label("Keine SSOT Dateien verknüpft.").classes(UIStyles.TITLE_H3)
                        ui.label("Bitte nutze das Zahnrad-Symbol oben, um Dateien aus dem Repo auszuwählen.").classes(UIStyles.TEXT_MUTED)
                    return

                if not state["active_file"] or state["active_file"] not in managed:
                    state["active_file"] = managed[0]

                with ui.row().classes('w-full items-center justify-between mt-2'):
                    with ui.row().classes('items-center gap-4'):
                        ui.label("Aktives SSOT-File:").classes('font-bold text-slate-600 dark:text-slate-300')
                        ui.select(managed).bind_value(state, 'active_file').classes('w-64').props('outlined dense').on('change', trigger_refresh)

                af = state["active_file"]
                if af not in state["yaml_data"]: return
                d_vars = state["yaml_data"][af]

                if "toplevel_vars" in d_vars:
                    with ui.tabs().classes('w-full border-b border-slate-200 dark:border-zinc-800') as tabs:
                        t1 = ui.tab('Global Config')
                        t2 = ui.tab('Vault & Secrets')
                        t3 = ui.tab('Infrastruktur (Sites)')
                        t4 = ui.tab('Raw YAML')

                    with ui.tab_panels(tabs, value=t1).classes('w-full bg-transparent p-0 mt-4'):
                        
                        with ui.tab_panel(t1):
                            with ui.card().classes(f'w-full {UIStyles.CARD_BASE}'):
                                if "toplevel_vars" not in d_vars: d_vars["toplevel_vars"] = {}
                                render_dict_editor(d_vars["toplevel_vars"], exclude_keys=["vault_vars", "common_users", "common_packages"])

                        with ui.tab_panel(t2):
                            with ui.card().classes(f'w-full {UIStyles.CARD_BASE}'):
                                if "vault_vars" not in d_vars.get("toplevel_vars", {}): 
                                    d_vars.setdefault("toplevel_vars", {})["vault_vars"] = {}
                                render_dict_editor(d_vars["toplevel_vars"]["vault_vars"])

                        # --- SITES MIT THEME.PY ---
                        with ui.tab_panel(t3):
                            sites = d_vars.get("sites", {})
                            if not sites: ui.label("Keine Sites konfiguriert.").classes(UIStyles.TEXT_MUTED)
                                
                            for site_name, site_config in sites.items():
                                with ui.expansion(f'🏢 Site: {site_name.upper()}', icon='domain').classes(f'w-full mb-4 {UIStyles.CARD_BASE} !p-2'):
                                    
                                    with ui.tabs().classes('w-full text-sm') as site_tabs:
                                        t_svars = ui.tab('Site Vars')
                                        t_stages = ui.tab('Stages & Hosts')
                                        
                                    with ui.tab_panels(site_tabs, value=t_stages).classes('w-full bg-transparent p-0 mt-4'):
                                        with ui.tab_panel(t_svars):
                                            if "site_vars" not in site_config: site_config["site_vars"] = {}
                                            render_dict_editor(site_config["site_vars"])
                                        
                                        with ui.tab_panel(t_stages):
                                            stages = site_config.get('stages', {})
                                            for stage_name, stage_cfg in stages.items():
                                                with ui.expansion(f'📦 Stage: {stage_name.upper()}', icon='layers').classes(f'w-full mb-4 {UIStyles.CARD_BASE} bg-slate-50/50 dark:bg-zinc-900/30 !p-2'):
                                                    hosts = stage_cfg.get('hosts') or {}
                                                    for hostname, host_cfg in hosts.items():
                                                        with ui.expansion(f'💻 Host: {hostname}', icon='dns').classes(f'w-full mb-2 {UIStyles.CARD_BASE} !p-2'):
                                                            with ui.row().classes('w-full gap-4 mt-2'):
                                                                ui.input('Hostname').bind_value(host_cfg, 'hostname').classes('flex-grow').props('outlined dense')
                                                                ui.input('Ansible IP').bind_value(host_cfg, 'ansible_host').classes('flex-grow').props('outlined dense')
                                                            render_services_ui(host_cfg)

                        with ui.tab_panel(t4):
                            with ui.card().classes(f'w-full p-0 overflow-hidden border border-slate-200 dark:border-zinc-800 rounded-2xl'):
                                ui.textarea('Raw YAML Content').bind_value(state["raw_strings"], af).classes('w-full font-mono text-xs h-[70vh]').props('autogrow outlined dark borderless')
                else:
                    with ui.card().classes(f'w-full {UIStyles.CARD_BASE} mt-4'):
                        ui.label(f"Generic File: {af}").classes('text-lg font-bold mb-2')
                        ui.textarea('Raw File Content').bind_value(state["raw_strings"], af).classes('w-full font-mono text-xs h-[70vh]').props('autogrow outlined dark')

            form_container()

            last_status = [None]
            def check_git_status():
                current = state.get("_async_status_msg")
                if current and current != last_status[0]:
                    last_status[0] = current
                    if "Fehler" in current: ui.notify(current, type="negative")
                    elif "lokal" in current or "no_changes" in current: ui.notify(current, type="info")
                    else: ui.notify(current, type="positive")
                        
                    if "abgeschlossen" in current:
                        load_from_disk(ctx)
                        form_container.refresh()
            ui.timer(1.0, check_git_status)

    @ctx.subscribe("git:status_update")
    async def on_git_update(payload):
        if payload.get("repo_id") != state["repo_id"]: return
        status = payload.get("status")
        if status == "synced": state["_async_status_msg"] = "Git Sync abgeschlossen."
        elif status == "pushed": state["_async_status_msg"] = "Erfolgreich zu GitLab gepusht!"
        elif status == "committed_locally": state["_async_status_msg"] = "Änderungen lokal committed (nicht gepusht)."
        elif status == "no_changes": state["_async_status_msg"] = "Keine Änderungen (no_changes)."
        elif status == "error": state["_async_status_msg"] = f"Git Fehler: {payload.get('error')}"