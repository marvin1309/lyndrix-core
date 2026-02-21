import psutil
from nicegui import ui
from .auth_ui import render_user_settings_card

def render_dashboard_page(fastapi_app):
    # Header Card
    with ui.card().classes('w-full p-8 shadow-sm border border-slate-200 dark:border-zinc-800 rounded-3xl mb-6 !bg-white dark:!bg-zinc-900'):
        ui.label('Core Dashboard').classes('text-3xl font-bold mb-1 dark:text-white')
        ui.label('System Monitoring & Status').classes('text-slate-500 dark:text-zinc-400')

    # Tabs für Dashboard-Inhalte
    with ui.tabs().classes('w-full dark:text-white') as tabs:
        t_sys = ui.tab('System Status', icon='analytics')
        t_plugins = ui.tab('Plugin Widgets', icon='widgets')

    with ui.tab_panels(tabs, value=t_sys).classes('w-full bg-transparent mt-4'):
        # PANEL 1: SYSTEM & METRIKEN
        with ui.tab_panel(t_sys):
            with ui.row().classes('w-full gap-4 mb-8'):
                cpu_label, cpu_bar = create_stat_card('CPU Load', 'blue')
                ram_label, ram_bar = create_stat_card('RAM Usage', 'indigo')
                disk_label, disk_bar = create_stat_card('Disk Usage', 'green')

            ui.label('Plugin Metriken').classes('text-xs font-bold uppercase text-slate-400 mb-4 px-2')
            plugin_stat_container = ui.row().classes('w-full gap-4')

            def update_dashboard():
                # Host Stats
                c, r, d = psutil.cpu_percent(), psutil.virtual_memory().percent, psutil.disk_usage('/').percent
                cpu_label.set_text(f"{c}%"); cpu_bar.set_value(c/100)
                ram_label.set_text(f"{r}%"); ram_bar.set_value(r/100)
                disk_label.set_text(f"{d}%"); disk_bar.set_value(d/100)

                # Plugin Metriken befüllen
                plugin_stat_container.clear()
                with plugin_stat_container:
                    m_providers = getattr(fastapi_app.state, 'metrics_providers', [])
                    d_providers = [p for p in getattr(fastapi_app.state, 'dashboard_providers', []) if callable(p)]
                    
                    for p_func in (m_providers + d_providers):
                        try:
                            for m in p_func():
                                with ui.card().classes('p-4 border border-slate-200 dark:border-zinc-800 rounded-2xl min-w-[200px] !bg-white dark:!bg-zinc-900'):
                                    ui.label(m['label']).classes('text-[10px] font-bold text-slate-400 uppercase')
                                    ui.label(str(m['get_val']())).classes(f'text-2xl font-black {m.get("color", "text-primary")}')
                        except: pass

            ui.timer(2.0, update_dashboard)

        # PANEL 2: WIDGETS
        with ui.tab_panel(t_plugins):
            with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 gap-6'):
                d_providers = getattr(fastapi_app.state, 'dashboard_providers', [])
                has_widgets = False
                for p in d_providers:
                    if isinstance(p, dict) and 'render' in p:
                        has_widgets = True
                        with ui.card().classes('p-6 border border-slate-200 dark:border-zinc-800 rounded-3xl !bg-white dark:!bg-zinc-900'):
                            ui.label(p.get('name', 'Widget')).classes('font-bold mb-4 dark:text-white')
                            p['render']()
                if not has_widgets:
                    ui.label('Keine speziellen Widgets vorhanden.').classes('text-slate-500 italic p-4')

def create_stat_card(title, color):
    with ui.card().classes('flex-1 p-6 border border-slate-200 dark:border-zinc-800 rounded-2xl min-w-[250px] !bg-white dark:!bg-zinc-900'):
        ui.label(title).classes('text-[10px] font-bold text-slate-400 uppercase tracking-widest')
        lbl = ui.label('0%').classes(f'text-4xl font-black text-{color}-500 mt-2')
        bar = ui.linear_progress(0).props(f'color={color} rounded').classes('mt-4')
        return lbl, bar

# --- DIESE FUNKTION HAT GEFEHLT ---
def render_settings_page(fastapi_app):
    ui.label('Einstellungen').classes('text-3xl font-bold mb-8 dark:text-white')

    with ui.tabs().classes('w-full border-b border-slate-200 dark:border-zinc-800 dark:text-white') as stabs:
        ts_user = ui.tab('Mein Profil', icon='person')
        ts_core = ui.tab('System-Core', icon='settings_input_component')
        ts_plugins = ui.tab('Plugin-Configs', icon='extension')

    with ui.tab_panels(stabs, value=ts_user).classes('w-full bg-transparent mt-6'):
        with ui.tab_panel(ts_user):
            render_user_settings_card()

        with ui.tab_panel(ts_core):
            providers = [x for x in fastapi_app.state.settings_providers if x.get('type') == 'CORE']
            if not providers:
                ui.label('Keine Core-Einstellungen verfügbar.').classes('text-slate-500 italic')
            for p in providers:
                render_expansion(p)

        with ui.tab_panel(ts_plugins):
            providers = [x for x in fastapi_app.state.settings_providers if x.get('type') != 'CORE']
            if not providers:
                ui.label('Keine Plugin-Einstellungen verfügbar.').classes('text-slate-500 italic')
            for p in providers:
                render_expansion(p)

# --- DIESE FUNKTION HAT AUCH GEFEHLT ---
def render_expansion(provider):
    with ui.expansion(provider['name'], icon=provider.get('icon', 'settings')) \
        .classes('w-full mb-2 border border-slate-200 dark:border-zinc-800 rounded-xl overflow-hidden !bg-white dark:!bg-zinc-900') \
        .props('header-class="dark:text-zinc-100"'):
        
        with ui.column().classes('w-full p-4 !bg-slate-50/50 dark:!bg-zinc-950/30'):
            try:
                provider['render']()
            except Exception as e:
                ui.label(f"Fehler beim Rendern: {e}").classes('text-red-500')
                
def render_plugins_page(fastapi_app):
    ui.label('Plugin Management').classes('text-3xl font-bold mb-2 dark:text-white tracking-tight')
    ui.label('Verwalte hier deine installierten Erweiterungen und Module.').classes('text-slate-500 mb-8')

    # WICHTIG: Wir nutzen jetzt die Liste, die dein Auto-Loader befüllt!
    all_plugins = getattr(fastapi_app.state, 'plugins', [])
    plugin_providers = [p for p in all_plugins if p.get('type') == 'PLUGIN']

    if not plugin_providers:
        with ui.card().classes('w-full p-16 items-center justify-center bg-slate-50 dark:bg-zinc-900/50 border-dashed border-2 border-slate-200 dark:border-zinc-800 rounded-3xl'):
            ui.icon('extension_off', size='64px').classes('text-slate-300 dark:text-zinc-700 mb-4')
            ui.label('Keine Plugins gefunden').classes('text-xl font-bold text-slate-400 dark:text-zinc-500')
            ui.label('Installiere Module im /plugins Verzeichnis, um sie hier zu verwalten.').classes('text-sm text-slate-400 mt-2')
        return

    with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'):
        for plugin in plugin_providers:
            # Fallback falls is_active nicht im Plugin-Dictionary existiert
            if 'is_active' not in plugin:
                plugin['is_active'] = True

            with ui.card().classes('p-6 border border-slate-200 dark:border-zinc-800 rounded-3xl flex flex-col justify-between shadow-sm hover:shadow-md transition-shadow !bg-white dark:!bg-zinc-900'):
                with ui.row().classes('items-start justify-between w-full mb-4 flex-nowrap'):
                    with ui.row().classes('items-center gap-3 flex-nowrap overflow-hidden'):
                        ui.icon(plugin.get('icon', 'extension'), size='24px').classes('text-indigo-500 bg-indigo-50 dark:bg-indigo-900/30 p-2 rounded-xl shrink-0')
                        ui.label(plugin.get('name', plugin.get('id', 'Unknown'))).classes('font-bold text-lg dark:text-zinc-100 truncate')
                    
                    ui.switch().props('color=emerald dense').bind_value(plugin, 'is_active')

                desc = plugin.get('description', 'Keine Beschreibung vorhanden.')
                ui.label(desc).classes('text-sm text-slate-500 dark:text-zinc-400 mb-6 flex-grow line-clamp-3')
                
                ui.separator().classes('mb-4 bg-slate-100 dark:bg-zinc-800')
                
                with ui.row().classes('w-full justify-between items-center'):
                    # Wir zeigen die Plugin-ID (Ordnername) als kleine Info unten an
                    ui.label(f"id: {plugin.get('id', 'unknown')}").classes('text-[10px] font-mono font-bold text-slate-400 bg-slate-100 dark:bg-zinc-800 px-2 py-1 rounded-md')
                    ui.button('Config', icon='tune', on_click=lambda: ui.navigate.to('/settings')).props('flat size=sm color=slate').classes('dark:text-zinc-300')