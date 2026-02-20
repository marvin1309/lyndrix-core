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
    config = {'entity': {'name': 'Firewall Rule', 'plural': 'Firewall Rules', 'icon': 'security'}, 'fields': []}

entity_def = config.get('entity', {})
fields_def = config.get('fields', [])

PLUGIN_NAME = "Firewall Manager"
PLUGIN_ICON = entity_def.get('icon', 'security')
ENTITY_TYPE = entity_def.get('name', 'Firewall Rule')

ui_refresh_callbacks = []

def setup(app):
    if not hasattr(app.state, 'data_providers'): app.state.data_providers = {}
    app.state.data_providers['firewall_rules'] = lambda: {r['id']: r.get('name', 'Unknown') for r in get_all_records(ENTITY_TYPE)}
    
    def provide_firewall_metrics():
        return [{
            'id': 'fw_active_rules',
            'label': 'Active Firewall Rules',
            'color': 'text-red-500',
            'icon': PLUGIN_ICON,
            'get_val': lambda: str(len(get_all_records(ENTITY_TYPE)))
        }]

    if hasattr(app.state, 'dashboard_providers'): app.state.dashboard_providers.append(provide_firewall_metrics)

    app.state.nav_items.setdefault('Data', [])
    if not any(item['target'] == '/firewall' for item in app.state.nav_items['Data']):
        app.state.nav_items['Data'].append({'icon': PLUGIN_ICON, 'label': entity_def.get('plural', 'Firewall'), 'target': '/firewall'})

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

    def get_display_rows():
        display_rows = []
        for row in get_all_records(ENTITY_TYPE):
            d_row = copy.deepcopy(row)
            for f in fields_def:
                if f.get('type') == 'select' and f.get('data_source'):
                    source_key = f.get('data_source')
                    if hasattr(app.state, 'data_providers') and source_key in app.state.data_providers:
                        live_options = app.state.data_providers[source_key]()
                        val = d_row.get(f['name'])
                        if isinstance(val, list):
                            d_row[f['name']] = ", ".join([live_options.get(v, str(v)) for v in val])
                        else:
                            d_row[f['name']] = live_options.get(val, str(val))
            display_rows.append(d_row)
        return display_rows

    # --- SEITE 1: ÜBERSICHT ---
    @ui.page('/firewall')
    @main_layout(entity_def.get('plural', 'Firewall'))
    def overview_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label(f"Active {entity_def.get('plural')}").classes('text-2xl font-bold dark:text-zinc-100')
            with ui.row().classes('gap-4 items-center'):
                search = ui.input(placeholder='Search...').props('outlined dense clearable').classes('w-64')
                ui.button('Einstellungen', icon='settings', on_click=lambda: ui.navigate.to('/firewall/settings')).props('unelevated outline rounded size=sm color=slate')

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
    @ui.page('/firewall/settings')
    @main_layout(entity_def.get('plural', 'Firewall'))
    def settings_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label(f"{entity_def.get('name')} Management").classes('text-2xl font-bold dark:text-zinc-100')
            ui.button('Zurück', icon='arrow_back', on_click=lambda: ui.navigate.to('/firewall')).props('unelevated outline rounded size=sm color=slate')

        current_record = {'id': None}
        form_inputs = {} 

        with ui.dialog() as edit_dialog:
            with ui.card().classes('w-full max-w-3xl p-6 shadow-xl border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
                form_title = ui.label("").classes('text-2xl font-bold mb-4 dark:text-zinc-100')
                
                with ui.scroll_area().classes('w-full max-h-[60vh] pr-4'):
                    with ui.column().classes('w-full gap-3'):
                        for f in fields_def:
                            field_name, field_label, field_type, default_val = f['name'], f['label'], f.get('type', 'string'), f.get('default', None)
                            
                            if field_type == 'string': form_inputs[field_name] = ui.input(field_label, value=default_val or '').classes('w-full').props('outlined dense')
                            elif field_type == 'integer': form_inputs[field_name] = ui.number(field_label, value=default_val).classes('w-full').props('outlined dense')
                            elif field_type == 'textarea': form_inputs[field_name] = ui.textarea(field_label, value=default_val or '').classes('w-full').props('outlined dense autogrow')
                            elif field_type == 'select': 
                                is_multi = f.get('multiple', False)
                                options_list = f.get('options', [])
                                safe_default = default_val if default_val is not None else ([] if is_multi else None)
                                sel = ui.select(options_list, label=field_label, value=safe_default, multiple=is_multi).classes('w-full').props('outlined dense')
                                if is_multi: sel.props('use-chips')
                                form_inputs[field_name] = sel

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
                    ui.button('Beauftragen', on_click=order_record, icon='shopping_cart_checkout', color='negative').props('unelevated rounded')

        with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl overflow-x-auto'):
            
            def open_new_dialog():
                current_record['id'] = None
                form_title.set_text(f"Neue {ENTITY_TYPE} anlegen")
                for f in fields_def:
                    is_multi = f.get('multiple', False)
                    form_inputs[f['name']].value = f.get('default', [] if is_multi else None)
                edit_dialog.open()

            def open_edit_dialog(row_id):
                records = get_all_records(ENTITY_TYPE)
                original_record = next((r for r in records if r['id'] == row_id), None)
                if original_record:
                    current_record['id'] = original_record['id']
                    form_title.set_text(f"Edit {ENTITY_TYPE}")
                    for f in fields_def:
                        if original_record.get(f['name']) is not None: 
                            form_inputs[f['name']].value = original_record.get(f['name'])
                    edit_dialog.open()

            with ui.row().classes('w-full justify-between items-center mb-4 min-w-[300px] gap-8'):
                ui.label(f"Configure {entity_def.get('plural')}").classes('text-lg font-bold dark:text-zinc-200')
                with ui.row().classes('gap-4 items-center'):
                    search = ui.input(placeholder='Search...').props('outlined dense clearable').classes('w-64')
                    ui.button('Neu beauftragen', icon='add', on_click=open_new_dialog, color='negative').props('unelevated rounded size=sm')

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