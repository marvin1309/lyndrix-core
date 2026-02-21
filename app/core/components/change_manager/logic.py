from nicegui import ui
import uuid

# Metadaten für den Loader
PLUGIN_NAME = "Change Manager"
PLUGIN_ICON = "fact_check"
PLUGIN_DESCRIPTION = "Globales Approval-System für anstehende Systemänderungen."

# Globale Queue
pending_changes = []

# --- DIESE FUNKTION MUSS GENAU SO HEISSEN ---
def provide_metrics():
    """Wird vom plugin_loader automatisch aufgerufen."""
    count = len(pending_changes)
    return [{
        'id': 'cm_pending_changes',
        'label': 'Pending Approvals',
        'color': 'text-orange-500' if count > 0 else 'text-slate-400',
        'icon': 'fact_check',
        'get_val': lambda: str(len(pending_changes)) # Lambda sorgt für Live-Update
    }]

def setup(app):

    # Eigene Kategorie "System" in der Sidebar
    app.state.nav_items.setdefault('System', [])
    if not any(item['target'] == '/changes' for item in app.state.nav_items['System']):
        app.state.nav_items['System'].append({
            'icon': PLUGIN_ICON,
            'label': 'Pending Changes',
            'target': '/changes'
        })

    main_layout = app.state.main_layout

    # --- EVENT LISTENER ---
    def on_change_requested(payload):
        """Fängt neue Änderungsanträge aus dem gesamten System ab."""
        change_record = {
            'id': str(uuid.uuid4())[:8],
            'entity_type': payload.get('entity_type', 'Unknown'),
            'action': payload.get('action', 'UNKNOWN'),
            'before': payload.get('before'),
            'after': payload.get('after'),
            'status': 'PENDING'
        }
        pending_changes.append(change_record)
        print(f"[{PLUGIN_NAME}] Neuer Change Request registriert: {change_record['id']}")

    if hasattr(app.state, 'event_bus'):
        app.state.event_bus.subscribe('change_requested', on_change_requested)

    # --- DIE UI ---
    @ui.page('/changes')
    @main_layout('Pending Changes')
    def change_manager_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label('Approval Queue').classes('text-2xl font-bold dark:text-zinc-100')
            ui.button('Refresh', icon='sync', on_click=ui.navigate.reload).props('unelevated outline rounded size=sm color=slate')

        with ui.card().classes('w-full p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
            
            # Wenn keine Änderungen da sind
            if not pending_changes:
                with ui.column().classes('w-full items-center justify-center py-12 opacity-50'):
                    ui.icon('check_circle', size='48px').classes('mb-4')
                    ui.label('Keine ausstehenden Änderungen. Alles up to date!').classes('text-lg')
                return

            # Wir gruppieren die Änderungen dynamisch nach dem Plugin (z.B. "Server Node")
            entities = set([c['entity_type'] for c in pending_changes])
            
            for entity in entities:
                entity_changes = [c for c in pending_changes if c['entity_type'] == entity]
                
                with ui.expansion(f"{entity} ({len(entity_changes)} Pending)", icon='pending_actions', value=True).classes('w-full shadow-sm border border-slate-200 dark:border-zinc-800 rounded-2xl !bg-slate-50 dark:!bg-zinc-800/50 mb-4'):
                    
                    columns = [
                        {'name': 'id', 'label': 'Change ID', 'field': 'id', 'align': 'left', 'classes': 'w-24 font-mono text-xs'},
                        {'name': 'action', 'label': 'Action', 'field': 'action', 'align': 'left', 'classes': 'font-bold'},
                        {'name': 'diff', 'label': 'Changes (Before -> After)', 'field': 'diff', 'align': 'left'},
                        {'name': 'actions', 'label': 'Decision', 'field': 'actions', 'align': 'right'},
                    ]
                    
                    # Wir formatieren die Daten für die Tabelle vor
                    table_rows = []
                    for c in entity_changes:
                        # Ein simples Diff für die UI bauen
                        if c['action'] == 'CREATE':
                            diff_text = f"NEW: {c['after'].get('name', 'Unknown')}"
                        else:
                            # Vergleiche Before und After
                            changes = []
                            for k, v in c['after'].items():
                                before_v = c['before'].get(k) if c['before'] else None
                                if v != before_v:
                                    changes.append(f"{k}: '{before_v}' ➔ '{v}'")
                            diff_text = " | ".join(changes) if changes else "No changes detected."
                            
                        table_rows.append({
                            'id': c['id'],
                            'action': c['action'],
                            'diff': diff_text,
                            'raw_data': c # Wir speichern den originalen Record versteckt mit ab
                        })

                    table = ui.table(columns=columns, rows=table_rows, row_key='id').classes('w-full no-shadow bg-transparent')

                    # Eigene Buttons in die Tabelle patchen
                    table.add_slot('body-cell-actions', '''
                        <q-td :props="props" class="gap-2">
                            <q-btn flat round color="negative" icon="close" size="sm" @click="$parent.$emit('reject', props.row)" />
                            <q-btn unelevated rounded color="positive" icon="check" label="Approve" size="sm" @click="$parent.$emit('approve', props.row)" />
                        </q-td>
                    ''')

                    # --- LOGIK FÜR APPROVE / REJECT ---
                    def handle_decision(e, is_approved):
                        change_id = e.args['id']
                        record = next((c for c in pending_changes if c['id'] == change_id), None)
                        
                        if record:
                            pending_changes.remove(record)
                            if is_approved:
                                app.state.event_bus.emit('change_approved', record)
                                ui.notify(f"Change {change_id} genehmigt und ans System übermittelt.", type='positive')
                            else:
                                ui.notify(f"Change {change_id} abgelehnt.", type='negative')
                            
                            ui.navigate.reload()

                    table.on('approve', lambda e: handle_decision(e, True))
                    table.on('reject', lambda e: handle_decision(e, False))

    print(f"Plugin geladen: {PLUGIN_NAME}")