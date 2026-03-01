from nicegui import ui
from ui.theme import UIStyles

# Wir importieren unseren Service für den Download
from ..logic.plugin_service import plugin_service
# Wir importieren den Manager, um die Liste der installierten Module zu bekommen
from ..logic.manager import module_manager

def render_plugins_page():
    """Rendert die komplette Plugin-Verwaltungsseite (Installer + Liste)."""
    
    # --- BEREICH 1: Plugin installieren (Installer) ---
    with ui.column().classes('w-full max-w-7xl gap-6'):
        ui.label('🔌 Plugin Verwaltung').classes('text-2xl font-bold text-white')
        
        with ui.card().classes(UIStyles.CARD_GLASS + ' w-full p-6'):
            ui.label('Neues Plugin installieren').classes(UIStyles.TITLE_H3 + ' mb-2')
            ui.label('Gib die GitHub URL des Repositories ein.').classes(UIStyles.TEXT_MUTED + ' mb-4')
            
            with ui.row().classes('w-full items-center gap-4'):
                github_url_input = ui.input('GitHub URL (z.B. https://github.com/marvin1309/lyndrix-meeting-bingo)').classes('flex-grow').props('outlined dark')
                install_btn = ui.button('Installieren', icon='download').classes('bg-primary text-white')
                spinner = ui.spinner('dots', size='lg', color='primary').classes('hidden')

            async def on_install_click():
                url = github_url_input.value
                if not url or "github.com" not in url:
                    ui.notify("Bitte eine gültige GitHub URL eingeben!", type="warning")
                    return
                
                install_btn.disable()
                spinner.classes(remove='hidden')
                ui.notify("Installation gestartet...", type="info")
                
                # Service aufrufen
                success = await plugin_service.install_plugin(url)
                
                spinner.classes(add='hidden')
                install_btn.enable()
                github_url_input.value = '' 
                
                if success:
                    ui.notify("✅ Plugin erfolgreich installiert! Ein Neustart wird empfohlen.", type="positive")
                else:
                    ui.notify("❌ Installation fehlgeschlagen. Siehe Logs.", type="negative")

            install_btn.on('click', on_install_click)
            
        ui.separator().classes('my-4 border-zinc-800')

        # --- BEREICH 2: Installierte Module (Dein Grid) ---
        ui.label('Installierte Komponenten').classes(UIStyles.TITLE_H2)
        ui.label('Verwalte aktive Core-Module und User-Plugins.').classes(UIStyles.TEXT_MUTED + ' mb-4')
        
        # Echte Daten aus der Registry holen!
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
                        
                        with ui.button(icon='article').props('flat round size=sm').classes('text-zinc-500'):
                            ui.tooltip(f'Logs für {m.name} anzeigen')
                        
                        ui.switch().props('color=emerald dense').classes('scale-75').set_value(True)
                        
def render_plugin_manager():
    """Wird vom Settings-Tab aufgerufen, um nur den Installer-Teil anzuzeigen."""
    # Wir rufen hier einfach die Logik auf, die du oben für den Installer gebaut hast
    with ui.card().classes(UIStyles.CARD_GLASS + ' w-full p-6'):
        ui.label('Plugin Installer').classes(UIStyles.TITLE_H3 + ' mb-2')
        ui.label('Installiere neue Module direkt via GitHub URL.').classes(UIStyles.TEXT_MUTED + ' mb-4')
        
        with ui.row().classes('w-full items-center gap-4'):
            url_input = ui.input('GitHub Repository URL').classes('flex-grow').props('outlined dark')
            btn = ui.button('Installieren', icon='download').classes('bg-primary')
            
            async def quick_install():
                if not url_input.value: return
                btn.disable()
                success = await plugin_service.install_plugin(url_input.value)
                btn.enable()
                if success:
                    ui.notify("Plugin installiert!")
                    url_input.value = ""
            
            btn.on('click', quick_install)