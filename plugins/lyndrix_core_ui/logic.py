from functools import wraps
from nicegui import ui, app
import os
import asyncio
import psutil

PLUGIN_NAME = "Core System"
PLUGIN_ICON = "settings_applications"
PLUGIN_DESCRIPTION = "Stellt das Dashboard und die Plugin-Verwaltung bereit."

def setup(fastapi_app):
    ui.add_css('assets/theme.css', shared=True)

    # 1. Navigation aufräumen: Nur noch Dashboard ist im Hauptmenü.
    fastapi_app.state.nav_items['Menu'].extend([
        {'icon': 'dashboard', 'label': 'Overview', 'target': '/'},
    ])

    # Plugins und Settings wandern in die Kategorie "System"
    fastapi_app.state.nav_items.setdefault('System', [])
    fastapi_app.state.nav_items['System'].extend([
        {'icon': 'extension', 'label': 'Plugins', 'target': '/plugins'},
        {'icon': 'settings', 'label': 'Einstellungen', 'target': '/settings'},
    ])

    if not hasattr(fastapi_app.state, 'dashboard_providers'): fastapi_app.state.dashboard_providers = []
    if not hasattr(fastapi_app.state, 'settings_providers'): fastapi_app.state.settings_providers = []

    def get_cpu_color(): return 'text-red-500' if psutil.cpu_percent() > 85 else 'text-emerald-500'
    def get_ram_color(): return 'text-red-500' if psutil.virtual_memory().percent > 85 else 'text-indigo-500'

    def provide_core_metrics():
        return [
            {'id': 'core_cpu', 'group': 'System Metrics', 'label': 'Host CPU Usage', 'color_func': get_cpu_color, 'icon': 'memory', 'get_val': lambda: f"{psutil.cpu_percent():.1f}%"},
            {'id': 'core_ram', 'group': 'System Metrics', 'label': 'Host RAM Usage', 'color_func': get_ram_color, 'icon': 'memory_alt', 'get_val': lambda: f"{psutil.virtual_memory().percent:.1f}%"},
            {'id': 'core_disk', 'group': 'System Metrics', 'label': 'Host Disk (C:)', 'color_func': lambda: 'text-slate-600 dark:text-zinc-400', 'icon': 'save', 'get_val': lambda: f"{psutil.disk_usage('/').percent:.1f}%"},
            {'id': 'core_plugins', 'group': 'System Metrics', 'label': 'Active Plugins', 'color_func': lambda: 'text-blue-500', 'icon': 'extension', 'get_val': lambda: str(len([p for p in fastapi_app.state.plugins if p['status'] == 'Aktiv']))}
        ]

    fastapi_app.state.dashboard_providers.append(provide_core_metrics)

    # --- ZENTRALE SYSTEM-FUNKTIONEN ---
    async def force_exit():
        ui.notify('System wird heruntergefahren...', type='info')
        await asyncio.sleep(1)
        os._exit(0)
        
    def trigger_reload():
        ui.notify('System wird neu gestartet...', type='ongoing', spinner=True)
        def fire_event():
            if hasattr(fastapi_app.state, 'event_bus'): fastapi_app.state.event_bus.emit('system_reload_requested', {'action': 'reload_plugins'})
        ui.timer(0.5, fire_event, once=True)

    def main_layout(page_title: str):
        def decorator(fn):
            @wraps(fn)
            def wrapper(*args, **kwargs):
                dark = ui.dark_mode()
                try: dark.bind_value(app.storage.user, 'dark_mode')
                except RuntimeError: pass 

                def sync_tailwind():
                    if dark.value: ui.query('html').classes('dark')
                    else: ui.query('html').classes(remove='dark')

                ui.timer(0.01, sync_tailwind, once=True)
                ui.query('body').classes('bg-slate-50 dark:bg-zinc-950 text-slate-900 dark:text-zinc-100 transition-colors duration-300')

                header = ui.header(elevated=False).classes('!bg-white/80 dark:!bg-zinc-900/80 backdrop-blur-md border-b border-slate-200 dark:border-zinc-800 text-slate-900 dark:text-white')
                drawer = ui.left_drawer(value=False).classes('!bg-white dark:!bg-zinc-900 border-r border-slate-200 dark:border-zinc-800 !p-4')

                with header:
                    with ui.row().classes('items-center gap-3'):
                        ui.button(on_click=drawer.toggle, icon='menu').props('flat round color=zinc-500')
                        ui.label('LYNDRIX').classes('text-lg font-black tracking-tighter')
                    ui.space()
                    
                    # --- NEU: SYSTEM KONTROLL-BUTTONS IN DER TOP-BAR ---
                    with ui.row().classes('items-center gap-2'):
                        # Restart Button
                        ui.button(on_click=trigger_reload, icon='autorenew').props('flat round size=sm').classes('text-slate-600 hover:text-slate-900 dark:text-zinc-400 dark:hover:text-zinc-100').tooltip('System Neustart')
                        # Shutdown Button
                        ui.button(on_click=force_exit, icon='power_settings_new').props('flat round size=sm').classes('text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20').tooltip('System Herunterfahren')
                        
                        # Trennstrich zur visuellen Trennung
                        ui.separator().props('vertical').classes('mx-2 h-6 bg-slate-200 dark:bg-zinc-700')
                        
                        # Darkmode Switch (unverändert)
                        with ui.row().classes('items-center bg-slate-100 dark:bg-zinc-800 px-3 py-1 rounded-full border border-slate-200 dark:border-zinc-700'):
                            ui.icon('light_mode', size='14px').classes('text-orange-500')
                            ui.switch(on_change=sync_tailwind).bind_value(dark, 'value').props('dense color=zinc-500')
                            ui.icon('dark_mode', size='14px').classes('text-indigo-400')

                with drawer:
                    with ui.row().classes('w-full items-center px-3 py-2.5 mb-6 bg-slate-100 dark:bg-zinc-800/50 rounded-xl text-slate-400 dark:text-zinc-500 border border-transparent dark:border-zinc-700/50'):
                        ui.icon('search', size='18px')
                        ui.label('Search...').classes('text-sm ml-2')
                        ui.space()
                        ui.label('⌘ K').classes('text-[10px] font-mono bg-white dark:bg-zinc-900 px-1.5 py-0.5 rounded shadow-sm border border-slate-200 dark:border-zinc-700')

                    for category, items in fastapi_app.state.nav_items.items():
                        if not items: continue
                        ui.label(category).classes('px-3 mb-2 mt-4 text-[11px] font-bold text-slate-400 dark:text-zinc-500 uppercase tracking-widest')
                        with ui.column().classes('w-full gap-1'):
                            for item in items:
                                is_active = (page_title == item['label'])
                                if is_active:
                                    state_classes = 'bg-blue-50 dark:bg-blue-900/10 text-primary dark:text-blue-400 font-semibold border-l-2 border-primary rounded-r-xl'
                                    icon_color = 'text-primary dark:text-blue-400'
                                else:
                                    state_classes = 'text-slate-500 dark:text-zinc-400 hover:bg-slate-50 dark:hover:bg-zinc-800/50 hover:text-slate-900 dark:hover:text-zinc-100 font-medium border-l-2 border-transparent rounded-r-xl'
                                    icon_color = 'text-slate-400 dark:text-zinc-500'
                                with ui.link(target=item['target']).classes('w-full flex items-center px-3 py-2 transition-all duration-200 no-underline cursor-pointer ' + state_classes):
                                    ui.icon(item['icon'], size='20px').classes(icon_color)
                                    ui.label(item['label']).classes('text-sm ml-3')

                with ui.column().classes('p-6 md:p-12 w-full max-w-7xl mx-auto'):
                    fn(*args, **kwargs)
            return wrapper
        return decorator

    fastapi_app.state.main_layout = main_layout

    @ui.page('/')
    @main_layout('Overview')
    def index_page():
        with ui.card().classes('w-full p-8 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
            ui.label('Core Dashboard').classes('text-3xl font-bold tracking-tight mb-1')
            ui.label('Lyndrix-Core System-Monitor (Live)').classes('text-slate-500 dark:text-zinc-400')
            
            metric_labels = {}
            all_metrics = []

            for provider_func in fastapi_app.state.dashboard_providers:
                try: all_metrics.extend(provider_func())
                except: pass

            grouped_metrics = {}
            for m in all_metrics:
                group_name = m.get('group', 'Plugin Metrics')
                if group_name not in grouped_metrics: grouped_metrics[group_name] = []
                grouped_metrics[group_name].append(m)

            group_order = ['System Metrics', 'Plugin Metrics']
            sorted_groups = sorted(grouped_metrics.keys(), key=lambda x: group_order.index(x) if x in group_order else 99)

            for g_name in sorted_groups:
                ui.label(g_name).classes('text-sm font-bold mt-8 mb-4 text-slate-800 dark:text-zinc-200 uppercase tracking-widest border-b border-slate-200 dark:border-zinc-800 pb-2 w-full')
                with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 xl:grid-cols-5 gap-6'):
                    for m in grouped_metrics[g_name]:
                        with ui.card().classes('flex flex-col p-5 !bg-slate-50 dark:!bg-zinc-800/50 border border-slate-100 dark:border-zinc-800/50 rounded-2xl shadow-none'):
                            with ui.row().classes('items-center gap-2 mb-2'):
                                ui.icon(m.get('icon', 'widgets'), size='18px').classes('text-slate-400 dark:text-zinc-500')
                                ui.label(m['label']).classes('text-[10px] uppercase font-black text-slate-400 dark:text-zinc-500 tracking-widest')
                            initial_color = m.get('color_func')() if 'color_func' in m else m.get('color', 'text-slate-900 dark:text-white')
                            val_label = ui.label(m['get_val']()).classes(f"text-3xl font-bold transition-colors duration-300 {initial_color}")
                            metric_labels[m['id']] = (val_label, m['get_val'], m.get('color_func'))

            def refresh_data():
                for label_obj, get_val_func, color_func in metric_labels.values():
                    try:
                        label_obj.set_text(get_val_func())
                        if color_func: label_obj.classes(replace=color_func())
                    except: pass
            ui.timer(2.0, refresh_data)

    @ui.page('/plugins')
    @main_layout('Plugins')
    def plugins_page():
        ui.label('Installierte Plugins').classes('text-2xl font-bold mb-6 dark:text-zinc-100')
        with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'):
            for p in fastapi_app.state.plugins:
                with ui.card().classes('w-full flex flex-col justify-between p-5 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-2xl hover:shadow-md transition-shadow cursor-pointer'):
                    with ui.row().classes('items-start gap-4 no-wrap w-full'):
                        with ui.element('div').classes('p-3 bg-slate-100 dark:bg-zinc-800 rounded-xl shrink-0'):
                            ui.icon(p.get('icon'), size='28px').classes('text-primary dark:text-blue-400')
                        with ui.column().classes('gap-1'):
                            ui.label(p.get('name')).classes('font-bold text-lg dark:text-zinc-100 leading-tight')
                            ui.label(p.get('description')).classes('text-xs text-slate-500 dark:text-zinc-400 leading-relaxed')
                    ui.space()
                    with ui.row().classes('w-full justify-end mt-4'):
                        if p['status'] == 'Aktiv': ui.label('Aktiv').classes('text-[10px] font-bold uppercase tracking-widest px-3 py-1 bg-emerald-100 dark:bg-emerald-900/20 text-emerald-600 dark:text-emerald-400 rounded-full')
                        else: ui.label('Fehler').classes('text-[10px] font-bold uppercase tracking-widest px-3 py-1 bg-red-100 dark:bg-red-900/20 text-red-600 dark:text-red-400 rounded-full')

    @ui.page('/settings')
    @main_layout('Einstellungen')
    def settings_page():
        ui.label('Systemsteuerung Lyndrix').classes('text-2xl font-bold mb-6 dark:text-zinc-100')

        with ui.row().classes('w-full gap-6 flex-col xl:flex-row items-start'):
            
            with ui.column().classes('w-full xl:w-1/3 gap-6'):
                with ui.card().classes('w-full p-8 shadow-sm border border-red-200 dark:border-red-900/30 !bg-red-50/30 dark:!bg-red-900/10 rounded-3xl'):
                    ui.label('System Control').classes('text-xl font-bold text-red-600 dark:text-red-400')
                    ui.label('Globale Verwaltungsfunktionen.').classes('text-sm text-red-500/70 mb-4')
                    ui.separator().classes('mb-6 bg-red-200 dark:bg-red-900/30')

                    with ui.column().classes('w-full gap-3'):
                        ui.button('Plugins neu laden', on_click=trigger_reload, icon='autorenew', color='slate').classes('w-full').props('unelevated rounded outline')
                        ui.button('System Stoppen', on_click=force_exit, icon='power_settings_new', color='red').classes('w-full').props('unelevated rounded')

            with ui.column().classes('w-full xl:w-2/3 gap-4'):
                ui.label('Plugin Konfigurationen').classes('text-xl font-bold dark:text-zinc-200 px-2')
                
                if not fastapi_app.state.settings_providers:
                    ui.label('Keine Plugins mit Einstellungen gefunden.').classes('text-slate-500 italic px-2')
                else:
                    for provider in fastapi_app.state.settings_providers:
                        with ui.expansion(provider['name'], icon=provider.get('icon', 'settings')).classes('w-full shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-2xl p-2'):
                            try:
                                provider['render']()
                            except Exception as e:
                                ui.label(f"Fehler beim Laden der Einstellungen: {e}").classes('text-red-500')

    print("Lyndrix Core UI dynamisch geladen.")