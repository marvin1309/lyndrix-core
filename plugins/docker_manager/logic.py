from nicegui import ui, run
import requests
import concurrent.futures

# --- METADATA ---
PLUGIN_NAME = "Docker Manager"
PLUGIN_ICON = "view_in_ar"
PLUGIN_DESCRIPTION = "Überwacht Live-Docker-Container im Swarm/Cluster."

# --- DEINE ECHTEN HOSTS ---
configured_hosts = [
    {'id': 1, 'name': 'docker-cerberus', 'ip': '10.1.130.61', 'port': 2375},
    {'id': 2, 'name': 'docker-hydra', 'ip': '10.1.130.62', 'port': 2375},
    {'id': 3, 'name': 'docker-gpu', 'ip': '10.1.130.70', 'port': 2375},
    {'id': 4, 'name': 'docker-truenas', 'ip': '10.1.130.90', 'port': 2375},
    {'id': 5, 'name': 'docker-atlas', 'ip': '10.100.1.50', 'port': 2375},
    {'id': 6, 'name': 'netm-titan', 'ip': '10.100.1.10', 'port': 2375},
    {'id': 7, 'name': 'netm-olympus', 'ip': '10.1.130.10', 'port': 2375},
    {'id': 8, 'name': 'cicd-core', 'ip': '10.100.1.5', 'port': 2375},
    {'id': 9, 'name': 'docker-dev', 'ip': '10.1.130.52', 'port': 2375},
    {'id': 10, 'name': 'docker-test', 'ip': '10.1.130.51', 'port': 2375},
    {'id': 11, 'name': 'docker-dmz', 'ip': '10.50.1.50', 'port': 2375},
]

def fetch_single_host(host):
    host_conts = []
    url = f"http://{host['ip']}:{host['port']}/containers/json?all=1"
    try:
        response = requests.get(url, timeout=1.5)
        if response.status_code == 200:
            for c in response.json():
                name = c.get('Names', ['/unknown'])[0].lstrip('/')
                host_conts.append({
                    'id': c.get('Id')[:12],
                    'name': name,
                    'image': c.get('Image'),
                    'state': c.get('State'),
                    'status': c.get('Status'),
                })
        else:
            host_conts.append({'id': 'ERROR', 'name': f'HTTP {response.status_code}', 'image': '-', 'state': 'error', 'status': 'Unreachable'})
    except Exception as e:
        host_conts.append({'id': 'ERROR', 'name': 'NODE OFFLINE', 'image': '-', 'state': 'error', 'status': 'Connection Timeout'})
    
    return host['name'], host_conts

def fetch_all_containers_parallel():
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
        futures = [executor.submit(fetch_single_host, h) for h in configured_hosts]
        for future in concurrent.futures.as_completed(futures):
            host_name, conts = future.result()
            results[host_name] = conts
    return dict(sorted(results.items()))


def setup(app):
    # --- DASHBOARD PROVIDER REGISTRIEREN ---
    def provide_docker_metrics():
        return [
            {
                'id': 'docker_nodes',
                'label': 'Docker Nodes',
                'color': 'text-cyan-500',
                'icon': 'dns',
                'get_val': lambda: str(len(configured_hosts))
            }
        ]

    if hasattr(app.state, 'dashboard_providers'):
        app.state.dashboard_providers.append(provide_docker_metrics)

    app.state.nav_items.setdefault('Infrastructure', [])
    if not any(item['target'] == '/docker' for item in app.state.nav_items['Infrastructure']):
        app.state.nav_items['Infrastructure'].append({
            'icon': PLUGIN_ICON,
            'label': 'Docker Nodes',
            'target': '/docker'
        })

    main_layout = app.state.main_layout

    # ==========================================
    # SEITE 1: HAUPTANSICHT (Live Container)
    # ==========================================
    @ui.page('/docker')
    @main_layout('Docker Nodes')
    def docker_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('Docker Swarm / Live Status').classes('text-2xl font-bold dark:text-zinc-100')
            
            with ui.row().classes('gap-4'):
                ui.button('Einstellungen', icon='settings', on_click=lambda: ui.navigate.to('/docker/settings')).props('unelevated outline rounded size=sm color=slate')
                refresh_btn = ui.button('Refresh All', icon='sync', color='primary').props('unelevated outline rounded size=sm')

        container_wrapper = ui.column().classes('w-full gap-4')

        async def refresh_containers():
            refresh_btn.props('loading')
            live_data_dict = await run.io_bound(fetch_all_containers_parallel)
            container_wrapper.clear()
            
            with container_wrapper:
                for host_name, conts in live_data_dict.items():
                    total = len(conts)
                    
                    if total > 0 and conts[0].get('state') == 'error':
                        header_text = f"{host_name} (OFFLINE)"
                        header_color = '!bg-red-50 dark:!bg-red-900/10 text-red-600 dark:text-red-400'
                    else:
                        running = sum(1 for c in conts if c['state'] == 'running')
                        header_text = f"{host_name} ({running}/{total} Running)"
                        header_color = '!bg-white dark:!bg-zinc-900 text-slate-800 dark:text-zinc-200'

                    with ui.expansion(header_text, icon='dns').classes(f'w-full shadow-sm border border-slate-200 dark:border-zinc-800 rounded-2xl {header_color} overflow-hidden'):
                        cont_columns = [
                            {'name': 'name', 'label': 'Container Name', 'field': 'name', 'align': 'left', 'sortable': True},
                            {'name': 'image', 'label': 'Image', 'field': 'image', 'align': 'left'},
                            {'name': 'state', 'label': 'State', 'field': 'state', 'align': 'left'},
                            {'name': 'status', 'label': 'Status Info', 'field': 'status', 'align': 'left'},
                        ]
                        
                        inner_table = ui.table(columns=cont_columns, rows=conts, row_key='id').classes('w-full no-shadow !bg-transparent')
                        inner_table.add_slot('body-cell-state', '''
                            <q-td :props="props">
                                <q-chip :color="props.value === 'running' ? 'positive' : (props.value === 'error' ? 'orange' : 'negative')" text-color="white" dense size="sm" class="font-bold uppercase tracking-wider">
                                    {{ props.value }}
                                </q-chip>
                            </q-td>
                        ''')

            refresh_btn.props(remove='loading')
            ui.notify(f'Update abgeschlossen: {sum(len(c) for c in live_data_dict.values())} Container gefunden.', type='positive')

        refresh_btn.on_click(refresh_containers)
        ui.timer(0.1, refresh_containers, once=True)


    # ==========================================
    # SEITE 2: EINSTELLUNGEN (Host Management)
    # ==========================================
    @ui.page('/docker/settings')
    @main_layout('Docker Nodes') 
    def docker_settings_page():
        
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('Host Management').classes('text-2xl font-bold dark:text-zinc-100')
            ui.button('Zurück zur Übersicht', icon='arrow_back', on_click=lambda: ui.navigate.to('/docker')).props('unelevated outline rounded size=sm color=slate')

        current_host = {'id': None}

        with ui.row().classes('w-full gap-6 flex-col lg:flex-row flex-nowrap items-start mb-6'):
            
            with ui.card().classes('w-full lg:w-2/3 p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
                ui.label('Registered Endpoints').classes('text-lg font-bold mb-4 dark:text-zinc-200')
                host_columns = [
                    {'name': 'name', 'label': 'Host Name', 'field': 'name', 'align': 'left', 'sortable': True},
                    {'name': 'ip', 'label': 'IP Address', 'field': 'ip', 'align': 'left'},
                    {'name': 'port', 'label': 'Port', 'field': 'port', 'align': 'left'},
                ]
                host_table = ui.table(columns=host_columns, rows=configured_hosts, row_key='id', selection='single', pagination=15).classes('w-full no-shadow border dark:border-zinc-800')

            with ui.card().classes('w-full lg:w-1/3 p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
                form_title = ui.label('Add Docker Host').classes('text-lg font-bold mb-4 dark:text-zinc-200')
                
                with ui.column().classes('w-full gap-3'):
                    name_input = ui.input('Host Name').classes('w-full').props('outlined dense')
                    with ui.row().classes('w-full gap-3 flex-nowrap'):
                        ip_input = ui.input('IP Address').classes('w-2/3').props('outlined dense')
                        port_input = ui.number('Port', value=2375).classes('w-1/3').props('outlined dense')
                    ui.separator().classes('my-2 dark:bg-zinc-800')
                    
                    def clear_form():
                        current_host['id'] = None
                        form_title.set_text('Add Docker Host')
                        name_input.value = ''
                        ip_input.value = ''
                        port_input.value = 2375
                        btn_delete.set_visibility(False)
                        host_table.selected.clear()
                        host_table.update()

                    def handle_selection(e):
                        if not host_table.selected:
                            clear_form()
                            return
                        selected = host_table.selected[0]
                        current_host['id'] = selected['id']
                        form_title.set_text('Edit Docker Host')
                        name_input.value = selected.get('name', '')
                        ip_input.value = selected.get('ip', '')
                        port_input.value = selected.get('port', 2375)
                        btn_delete.set_visibility(True)

                    def save_host():
                        if not name_input.value or not ip_input.value:
                            ui.notify('Name und IP sind Pflichtfelder!', type='negative')
                            return
                        
                        if current_host['id'] is not None:
                            for h in configured_hosts:
                                if h['id'] == current_host['id']:
                                    h.update({'name': name_input.value, 'ip': ip_input.value, 'port': port_input.value})
                                    break
                            ui.notify('Host aktualisiert!', type='positive', color='emerald')
                        else:
                            new_id = max([h['id'] for h in configured_hosts] + [0]) + 1
                            configured_hosts.append({'id': new_id, 'name': name_input.value, 'ip': ip_input.value, 'port': port_input.value})
                            ui.notify('Host hinzugefügt!', type='positive', color='emerald')
                        
                        host_table.rows = configured_hosts
                        host_table.update()
                        clear_form()

                    def delete_host():
                        if current_host['id'] is not None:
                            host_to_delete = next((h for h in configured_hosts if h['id'] == current_host['id']), None)
                            if host_to_delete:
                                configured_hosts.remove(host_to_delete)
                                ui.notify(f"Host {host_to_delete['name']} entfernt.", type='info')
                                host_table.rows = configured_hosts
                                host_table.update()
                                clear_form()

                    host_table.on('selection', handle_selection)
                    
                    with ui.row().classes('w-full justify-between items-center'):
                        btn_delete = ui.button(icon='delete', on_click=delete_host, color='red').props('unelevated rounded flat').classes('px-2')
                        btn_delete.set_visibility(False) 
                        with ui.row().classes('gap-2'):
                            ui.button('Cancel', on_click=clear_form, color='slate').props('unelevated rounded')
                            ui.button('Save', on_click=save_host, color='primary').props('unelevated rounded')

    print(f"Plugin geladen: {PLUGIN_NAME}")