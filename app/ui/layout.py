from functools import wraps
from nicegui import ui, app
from ui.theme import apply_theme, UIStyles
from ui.maintenance import attach_maintenance_overlay
from core.bus import bus

def main_layout(page_title: str):
    def decorator(fn):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            apply_theme()
            dark = ui.dark_mode()

            # Darkmode Präferenz
            theme_pref = app.storage.user.get('theme_pref', 'auto')
            if theme_pref == 'dark': dark.enable()
            elif theme_pref == 'light': dark.disable()
            else: dark.auto()

            def set_theme(mode: str):
                app.storage.user['theme_pref'] = mode
                if mode == 'dark': dark.enable()
                elif mode == 'light': dark.disable()
                else: dark.auto()
                ui.timer(0.5, lambda: ui.navigate.to(app.request.url.path), once=True)

            # --- WARTUNGS-LOGIK ---
            attach_maintenance_overlay()

            # --- HEADER ---
            with ui.header(elevated=False).classes(UIStyles.HEADER):
                with ui.row().classes('items-center gap-3 w-full'):
                    ui.button(icon='menu').props('flat round text-color=current').on('click', lambda: left_drawer.toggle())
                    ui.label('LYNDRIX').classes('text-lg font-black tracking-tighter text-primary')
                    ui.space() 
                    with ui.row().classes('items-center gap-2'):
                        ui.label(page_title).classes(UIStyles.LABEL_MINI)
                        with ui.button(icon='account_circle').props('flat round text-color=current'):
                            with ui.menu().classes(UIStyles.MENU_CONTAINER):
                                with ui.menu_item('Darstellung').classes(UIStyles.MENU_ITEM):
                                    with ui.menu().classes(UIStyles.MENU_CONTAINER):
                                        ui.menu_item('Auto', on_click=lambda: set_theme('auto'))
                                        ui.menu_item('Hell', on_click=lambda: set_theme('light'))
                                        ui.menu_item('Dunkel', on_click=lambda: set_theme('dark'))
                                ui.separator()
                                ui.menu_item('Einstellungen', on_click=lambda: ui.navigate.to('/settings'))
                                ui.menu_item('Abmelden', on_click=lambda: [app.storage.user.clear(), ui.navigate.to('/')])

            with ui.left_drawer(value=False).classes(UIStyles.SIDEBAR) as left_drawer:
                # Deine Sidebar Navigation...
                pass

            with ui.column().classes('p-6 md:p-12 w-full max-w-7xl mx-auto flex-grow'):
                return await fn(*args, **kwargs)
                
        return wrapper
    return decorator