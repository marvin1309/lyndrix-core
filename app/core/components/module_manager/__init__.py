from nicegui import ui
from core.modules.models import ModuleManifest
from core.modules.manager import module_manager
from ui.theme import UIStyles
from ui.layout import main_layout

manifest = ModuleManifest(
    id="lyndrix.core.modules",
    name="Module Management",
    version="1.0.0",
    description="Zentrale Verwaltung aller Core-Komponenten und Plugins.",
    author="Lyndrix",
    icon="settings_input_component",
    type="CORE",
    ui_route="/plugins",
    permissions={"subscribe": ["*"], "emit": ["system:reload"]}
)

def setup(ctx):
    @ui.page('/plugins')
    @main_layout('Plugins')
    async def render_plugins_page():
        ui.label('Modul Management').classes(UIStyles.TITLE_H1)
        ui.label('Verwalte installierte Komponenten und erweitere dein System.').classes(UIStyles.TEXT_MUTED + ' mb-8')
        
        # Echte Daten aus der Registry
        manifests = module_manager.get_manifests()

        with ui.row().classes('w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6'):
            for m in manifests:
                with ui.card().classes(UIStyles.CARD_GLASS + ' flex flex-col justify-between'):
                    with ui.column().classes('w-full gap-2'):
                        with ui.row().classes('w-full items-center justify-between mb-2'):
                            ui.icon(m.icon, size='32px').classes('text-primary')
                            
                            badge_color = 'bg-amber-500/20 text-amber-500' if m.type == "CORE" else 'bg-emerald-500/20 text-emerald-500'
                            ui.label(m.type).classes(f'text-[10px] font-bold px-2 py-1 rounded-full {badge_color}')

                        ui.label(m.name).classes(UIStyles.TITLE_H3)
                        ui.label(m.description).classes('text-xs text-zinc-400 leading-relaxed line-clamp-2')
                    
                    with ui.row().classes('w-full items-center justify-between mt-6 pt-4 border-t border-zinc-800/50'):
                        ui.label(f'v{m.version}').classes('text-[10px] font-mono opacity-50')
                        # Log-Button als Vorbereitung für Phase 4.3
                        with ui.button(icon='article').props('flat round size=sm').classes('text-zinc-500'):
                            ui.tooltip(f'Logs für {m.name} anzeigen')
                        
                        # Switch (In Phase 4 binden wir den an die DB)
                        ui.switch().props('color=emerald dense').classes('scale-75').set_value(True)