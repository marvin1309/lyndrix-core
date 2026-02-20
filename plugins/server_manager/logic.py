from nicegui import ui
import yaml
import os
import copy
from core.database import SessionLocal, DynamicEntity, get_all_records

plugin_dir = os.path.dirname(os.path.abspath(__file__))
config_path = os.path.join(plugin_dir, 'config', 'entity.yml')

if os.path.exists(config_path):
    with open(config_path, 'r', encoding='utf-8') as f: config = yaml.safe_load(f)
else:
    config = {'entity': {'name': 'Server Node', 'plural': 'Servers', 'icon': 'dns'}, 'fields': []}

entity_def = config.get('entity', {})
fields_def = config.get('fields', [])

PLUGIN_NAME = "Server Manager"
PLUGIN_ICON = entity_def.get('icon', 'dns')
ENTITY_TYPE = entity_def.get('name', 'Server Node')

mock_relations_db = {
    'vendors': {1: 'Dell EMC', 2: 'Hewlett Packard Enterprise', 3: 'Cisco Systems', 4: 'Lenovo'},
    'chassis': {10: 'PowerEdge R740', 11: 'ProLiant DL380 Gen10', 12: 'UCS C220 M5'},
    'cpus': {100: 'Intel Xeon Gold 6248R', 101: 'AMD EPYC 7742', 102: 'Intel Xeon Platinum 8280'},
    'operating_systems': {200: 'Ubuntu 24.04 LTS', 201: 'Windows Server 2022', 202: 'Red Hat Enterprise Linux 9'},
    'locations': {300: 'Frankfurt HQ', 301: 'London Branch', 302: 'New York Office'},
    'datacenters': {400: 'FRA-01 (Equinix)', 401: 'FRA-02 (Interxion)', 402: 'LON-01', 403: 'NY-01'},
    'rooms': {500: 'Room A.12', 501: 'Room B.04', 502: 'Cage 42'}
}

ui_refresh_callbacks = []

def setup(app):
    if not hasattr(app.state, 'data_providers'): app.state.data_providers = {}
    app.state.data_providers['server_nodes'] = lambda: {r['id']: r.get('name', 'Unknown') for r in get_all_records(ENTITY_TYPE)}

    def provide_server_metrics():
        records = get_all_records(ENTITY_TYPE)
        offline_count = len([s for s in records if s.get('status') == 'OFFLINE'])
        return [
            {'id': 'sm_total', 'label': 'Total Server Nodes', 'color': 'text-emerald-500', 'icon': 'dns', 'get_val': lambda: str(len(records))},
            {'id': 'sm_offline', 'label': 'Offline Server', 'color': 'text-red-500' if offline_count > 0 else 'text-slate-400 dark:text-zinc-600', 'icon': 'error_outline', 'get_val': lambda: str(offline_count)}
        ]

    if hasattr(app.state, 'dashboard_providers'): app.state.dashboard_providers.append(provide_server_metrics)

    app.state.nav_items.setdefault('Data', [])
    if not any(item['target'] == '/servers' for item in app.state.nav_items['Data']):
        app.state.nav_items['Data'].append({'icon': PLUGIN_ICON, 'label': entity_def.get('plural', 'Servers'), 'target': '/servers'})

    main_layout = app.state.main_layout

    def on_change_approved(payload):
        if payload.get('entity_type') != ENTITY_TYPE: return
        action = payload['action']
        approved_data = payload['after']
        
        with SessionLocal() as db:
            if action == 'CREATE':
                clean_payload = {k: v for k, v in approved_data.items() if k != 'id'}
                db.add(DynamicEntity(entity_type=ENTITY_TYPE, payload=clean_payload))
                db.commit()
            elif action == 'UPDATE':
                entity_id = approved_data.get('id')
                if entity_id:
                    entity = db.query(DynamicEntity).filter(DynamicEntity.id == entity_id).first()
                    if entity:
                        clean_payload = {k: v for k, v in approved_data.items() if k != 'id'}
                        entity.payload = clean_payload
                        db.commit()
                        
        for cb in ui_refresh_callbacks: cb()

    if hasattr(app.state, 'event_bus'): app.state.event_bus.subscribe('change_approved', on_change_approved)

    def resolve_relation(field_def, value):
        if field_def.get('type') != 'relation' or value is None: return value
        target = field_def.get('target_entity')
        return mock_relations_db.get(target, {}).get(value, value)

    def get_display_rows():
        return [{**r, **{f['name']: resolve_relation(f, r.get(f['name'])) for f in fields_def}} for r in get_all_records(ENTITY_TYPE)]

    # --- SEITE 1: ÜBERSICHT ---
    @ui.page('/servers')
    @main_layout(entity_def.get('plural', 'Servers'))
    def overview_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label(f"Active {entity_def.get('plural')}").classes('text-2xl font-bold dark:text-zinc-100')
            with ui.row().classes('gap-4 items-center'):
                search = ui.input(placeholder='Search...').props('outlined dense clearable').classes('w-64')
                ui.button('Einstellungen', icon='settings', on_click=lambda: ui.navigate.to('/servers/settings')).props('unelevated outline rounded size=sm color=slate')

        with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl overflow-x-auto'):
            dynamic_columns = [{'name': f['name'], 'label': f['label'], 'field': f['name'], 'align': 'left', 'sortable': True} for f in fields_def if f.get('show_in_table', False)]
            
            table = ui.table(columns=dynamic_columns, rows=[], row_key='id').classes('w-full whitespace-nowrap no-shadow !bg-transparent')
            
            def update_table(e=None):
                query = search.value.lower() if search.value else ''
                rows = get_display_rows()
                table.rows = [r for r in rows if any(query in str(v).lower() for v in r.values() if v is not None)] if query else rows
                table.update()

            search.on('update:model-value', update_table)
            ui_refresh_callbacks.append(update_table)
            update_table()


    # --- SEITE 2: EINSTELLUNGEN ---
    @ui.page('/servers/settings')
    @main_layout(entity_def.get('plural', 'Servers'))
    def settings_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label(f"{entity_def.get('name')} Management").classes('text-2xl font-bold dark:text-zinc-100')
            ui.button('Zurück', icon='arrow_back', on_click=lambda: ui.navigate.to('/servers')).props('unelevated outline rounded size=sm color=slate')
        
        current_record = {'id': None}
        form_inputs = {} 

        with ui.dialog() as edit_dialog:
            with ui.card().classes('w-full max-w-3xl p-6 shadow-xl border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
                form_title = ui.label("").classes('text-2xl font-bold mb-4 dark:text-zinc-100')
                
                with ui.scroll_area().classes('w-full max-h-[60vh] pr-4'):
                    with ui.column().classes('w-full gap-3'):
                        for f in fields_def:
                            field_name = f['name']
                            field_label = f['label']
                            field_type = f.get('type', 'string')
                            default_val = f.get('default', None)
                            
                            if field_type == 'string': form_inputs[field_name] = ui.input(field_label, value=default_val or '').classes('w-full').props('outlined dense')
                            elif field_type == 'integer': form_inputs[field_name] = ui.number(field_label, value=default_val).classes('w-full').props('outlined dense')
                            elif field_type == 'select': 
                                is_multi = f.get('multiple', False)
                                opts = f.get('options', [])
                                data_source = f.get('data_source')
                                if data_source and hasattr(app.state, 'data_providers') and data_source in app.state.data_providers:
                                    opts = app.state.data_providers[data_source]() 
                                sel = ui.select(opts, label=field_label, multiple=is_multi).classes('w-full').props('outlined dense')
                                if is_multi: sel.props('use-chips')
                                form_inputs[field_name] = sel
                            elif field_type == 'textarea': form_inputs[field_name] = ui.textarea(field_label, value=default_val or '').classes('w-full').props('outlined dense autogrow')
                            elif field_type == 'relation':
                                target_entity = f.get('target_entity')
                                opts = mock_relations_db.get(target_entity, {})
                                safe_default = default_val if default_val in opts else None
                                form_inputs[field_name] = ui.select(opts, label=field_label, value=safe_default).classes('w-full').props('outlined dense')

                        ui.separator().classes('my-2 dark:bg-zinc-800')

                def order_record():
                    is_update = current_record['id'] is not None
                    order_type = "UPDATE" if is_update else "CREATE"
                    
                    after_state = {f['name']: form_inputs[f['name']].value for f in fields_def}
                    before_state = None
                    
                    if is_update: 
                        after_state['id'] = current_record['id']
                        records = get_all_records(ENTITY_TYPE)
                        original_record = next((r for r in records if r['id'] == current_record['id']), None)
                        if original_record: before_state = copy.deepcopy(original_record)

                    app.state.event_bus.emit('change_requested', {'entity_type': ENTITY_TYPE, 'action': order_type, 'before': before_state, 'after': after_state})
                    ui.notify("Änderungsantrag eingereicht!", type='info', icon='hourglass_empty')
                    edit_dialog.close()

                with ui.row().classes('w-full justify-end gap-2 mt-4'):
                    ui.button('Abbrechen', on_click=edit_dialog.close, color='slate').props('unelevated rounded')
                    ui.button('Beauftragen', on_click=order_record, icon='shopping_cart_checkout', color='primary').props('unelevated rounded')

        with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl overflow-x-auto'):
            def open_new_dialog():
                current_record['id'] = None
                form_title.set_text(f"Neuen {ENTITY_TYPE} anlegen")
                for f in fields_def:
                    is_multi = f.get('multiple', False)
                    form_inputs[f['name']].value = f.get('default', [] if is_multi else None)
                edit_dialog.open()

            def open_edit_dialog(row_id):
                records = get_all_records(ENTITY_TYPE)
                original = next((r for r in records if r['id'] == row_id), None)
                if original:
                    current_record['id'] = original['id']
                    form_title.set_text(f"Edit {ENTITY_TYPE}")
                    for f in fields_def:
                        if original.get(f['name']) is not None: 
                            form_inputs[f['name']].value = original.get(f['name'])
                    edit_dialog.open()

            with ui.row().classes('w-full justify-between items-center mb-4 min-w-[300px] gap-8'):
                ui.label(f"Configure {entity_def.get('plural')}").classes('text-lg font-bold dark:text-zinc-200')
                with ui.row().classes('gap-4 items-center'):
                    search = ui.input(placeholder='Search...').props('outlined dense clearable').classes('w-64')
                    ui.button('Neu beauftragen', icon='add', on_click=open_new_dialog, color='primary').props('unelevated rounded size=sm')

            dynamic_columns = [{'name': f['name'], 'label': f['label'], 'field': f['name'], 'align': 'left', 'sortable': True} for f in fields_def if f.get('show_in_table', False)]
            
            table = ui.table(columns=dynamic_columns, rows=[], row_key='id').classes('w-full whitespace-nowrap no-shadow border dark:border-zinc-800 cursor-pointer')
            table.on('rowClick', lambda e: open_edit_dialog(e.args[1]['id']))
            
            def update_table(e=None):
                query = search.value.lower() if search.value else ''
                rows = get_display_rows()
                table.rows = [r for r in rows if any(query in str(v).lower() for v in r.values() if v is not None)] if query else rows
                table.update()

            search.on('update:model-value', update_table)
            ui_refresh_callbacks.append(update_table)
            update_table()

    print(f"Plugin geladen: {PLUGIN_NAME}")