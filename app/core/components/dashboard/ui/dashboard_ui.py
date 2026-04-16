import asyncio
from nicegui import ui
from ui.theme import UIStyles
from core.components.plugins.logic.manager import module_manager
from core.services import monitor_service, vault_instance, db_instance

async def render_dashboard_page():
    """Renders the main dashboard in a modern vertical stack."""

    with ui.column().classes('w-full max-w-7xl mx-auto gap-8 py-4'):
        # --- HEADER ---
        with ui.row().classes('w-full items-center justify-between'):
            with ui.column().classes('gap-1'):
                ui.label('System Overview').classes(UIStyles.TITLE_H1)
                ui.label('Real-time metrics and subsystem status.').classes(UIStyles.TEXT_MUTED)
            ui.button(icon='refresh', on_click=lambda: ui.run_javascript('window.location.reload()')).props('flat round color=zinc-500').tooltip('Refresh Dashboard')

        # --- STACK 1: CORE SUBSYSTEMS ---
        ui.label('Core Infrastructure').classes(UIStyles.TITLE_H3 + ' mb-[-1rem]')
        with ui.grid(columns='repeat(auto-fit, minmax(250px, 1fr))').classes('w-full gap-4'):
            # Vault Status
            with ui.card().classes(f'{UIStyles.CARD_GLASS} flex flex-row items-center gap-4 p-4 hover:border-indigo-500/50 transition-all'):
                ui.icon('lock', size='32px').classes('text-indigo-400 bg-indigo-500/10 p-3 rounded-xl')
                with ui.column().classes('gap-0'):
                    ui.label('Vault Service').classes('font-bold text-slate-200')
                    if vault_instance.is_connected:
                        ui.label('Online & Unsealed').classes('text-xs text-emerald-400 font-mono')
                    else:
                        ui.label(vault_instance.ui_state.replace('_', ' ').title()).classes('text-xs text-amber-400 font-mono')

            # Database Status
            with ui.card().classes(f'{UIStyles.CARD_GLASS} flex flex-row items-center gap-4 p-4 hover:border-blue-500/50 transition-all'):
                ui.icon('storage', size='32px').classes('text-blue-400 bg-blue-500/10 p-3 rounded-xl')
                with ui.column().classes('gap-0'):
                    ui.label('MariaDB Engine').classes('font-bold text-slate-200')
                    if db_instance.is_connected:
                        ui.label('Connected').classes('text-xs text-emerald-400 font-mono')
                    else:
                        ui.label('Disconnected').classes('text-xs text-red-400 font-mono')

            # Plugin Manager Status
            active_plugins = sum(1 for p in module_manager.registry.values() if p.get("status") == "active" and p["manifest"].type == "PLUGIN")
            total_plugins = sum(1 for p in module_manager.registry.values() if p["manifest"].type == "PLUGIN")
            
            with ui.card().classes(f'{UIStyles.CARD_GLASS} flex flex-row items-center gap-4 p-4 hover:border-emerald-500/50 transition-all'):
                ui.icon('extension', size='32px').classes('text-emerald-400 bg-emerald-500/10 p-3 rounded-xl')
                with ui.column().classes('gap-0'):
                    ui.label('Plugin Subsystem').classes('font-bold text-slate-200')
                    ui.label(f'{active_plugins} / {total_plugins} Active').classes('text-xs text-emerald-400 font-mono')

        # --- STACK 2: HARDWARE METRICS ---
        ui.label('Hardware Utilization').classes(UIStyles.TITLE_H3 + ' mb-[-1rem] mt-4')
        with ui.grid(columns='repeat(auto-fit, minmax(300px, 1fr))').classes('w-full gap-4'):
            # CPU
            with ui.card().classes(f'{UIStyles.CARD_GLASS} p-5'):
                with ui.row().classes('w-full justify-between items-center mb-2'):
                    ui.label('CPU Usage').classes('font-bold text-slate-300')
                    ui.icon('memory', size='20px').classes('text-slate-500')
                cpu_prog = ui.linear_progress(value=0, show_value=False).props('color=indigo rounded size=8px')
                ui.label().classes('text-2xl font-black font-mono mt-1 text-indigo-400').bind_text_from(monitor_service.stats, 'cpu', lambda v: f"{v:.1f}%")
                cpu_prog.bind_value_from(monitor_service.stats, 'cpu', lambda v: v / 100.0)

            # RAM
            with ui.card().classes(f'{UIStyles.CARD_GLASS} p-5'):
                with ui.row().classes('w-full justify-between items-center mb-2'):
                    ui.label('Memory (RAM)').classes('font-bold text-slate-300')
                    ui.icon('dns', size='20px').classes('text-slate-500')
                ram_prog = ui.linear_progress(value=0, show_value=False).props('color=emerald rounded size=8px')
                ui.label().classes('text-2xl font-black font-mono mt-1 text-emerald-400').bind_text_from(monitor_service.stats, 'ram', lambda v: f"{v:.1f}%")
                ram_prog.bind_value_from(monitor_service.stats, 'ram', lambda v: v / 100.0)

            # DISK
            with ui.card().classes(f'{UIStyles.CARD_GLASS} p-5'):
                with ui.row().classes('w-full justify-between items-center mb-2'):
                    ui.label('Disk IO').classes('font-bold text-slate-300')
                    ui.icon('save', size='20px').classes('text-slate-500')
                disk_prog = ui.linear_progress(value=0, show_value=False).props('color=amber rounded size=8px')
                ui.label().classes('text-2xl font-black font-mono mt-1 text-amber-400').bind_text_from(monitor_service.stats, 'disk', lambda v: f"{v:.1f}%")
                disk_prog.bind_value_from(monitor_service.stats, 'disk', lambda v: v / 100.0)

        # --- STACK 3: PLUGIN WIDGETS ---
        ui.label('Module Integrations').classes(UIStyles.TITLE_H3 + ' mb-[-1rem] mt-4')
        with ui.grid(columns='repeat(auto-fit, minmax(350px, 1fr))').classes('w-full gap-6'):
            widget_rendered = False
            for entry in module_manager.registry.values():
                if entry.get("status") == "active" and hasattr(entry["module"], 'render_dashboard_widget'):
                    widget_rendered = True
                    try:
                        with ui.card().classes(f'{UIStyles.CARD_GLASS} p-5 flex flex-col gap-2 hover:border-slate-500/30 transition-all') as widget_card:
                            widget_render_func = entry["module"].render_dashboard_widget
                            if asyncio.iscoroutinefunction(widget_render_func):
                                await widget_render_func(entry["context"])
                            else:
                                widget_render_func(entry["context"])
                    except Exception as e:
                        with ui.card().classes(f'{UIStyles.CARD_BASE} border-red-500/50 p-5'):
                            ui.label(f"Widget Error: {entry['manifest'].name}").classes('text-red-500 font-bold')
                            ui.label(str(e)).classes('text-red-500 text-xs')
            
            if not widget_rendered:
                ui.label('No active plugins provide dashboard widgets.').classes(f'{UIStyles.TEXT_MUTED} italic col-span-full mt-2')