from nicegui import ui

def mount_ui(app, plugin_name):
    main_layout = app.state.main_layout

    @ui.page('/secrets')
    @main_layout('Vault Secrets')
    def secrets_page():
        with ui.row().classes('w-full justify-between items-center mb-6'):
            ui.label("Vault Secrets Management").classes('text-2xl font-bold dark:text-zinc-100')
            if app.state.vault.is_connected:
                ui.chip('Vault Connected', icon='check_circle', color='emerald', text_color='white').classes('font-bold')
            else:
                ui.chip('Vault Disconnected', icon='error', color='red', text_color='white').classes('font-bold')

        with ui.card().classes('w-full max-w-2xl p-6 shadow-sm border border-slate-200 dark:border-zinc-800 !bg-white dark:!bg-zinc-900 rounded-3xl'):
            ui.label('Secret Test-Konsole').classes('text-lg font-bold mb-4 dark:text-zinc-200')
            ui.label('Hier kannst du manuell Werte im Vault überprüfen oder überschreiben.').classes('text-sm text-slate-500 mb-4 block')
            
            path_input = ui.input('Secret Path (z.B. lyndrix/gitlab_pat)').classes('w-full mb-3').props('outlined dense')
            val_input = ui.input('Secret Value').classes('w-full mb-4').props('outlined dense')
            
            with ui.row().classes('w-full gap-4'):
                def read_sec():
                    val = app.state.vault.get_secret(path_input.value)
                    if val: 
                        val_input.value = val
                        ui.notify('Secret erfolgreich aus Vault geladen!', type='positive')
                    else: 
                        ui.notify('Nicht gefunden oder Fehler (siehe Konsole)', type='warning')
                
                def write_sec():
                    try:
                        app.state.vault.set_secret(path_input.value, val_input.value)
                        ui.notify('Gespeichert in Vault!', type='positive')
                    except Exception as e:
                        ui.notify(f"Fehler: {str(e)}", type='negative')

                ui.button('Read from Vault', on_click=read_sec, icon='download', color='slate').props('unelevated rounded outline')
                ui.button('Write to Vault', on_click=write_sec, icon='upload', color='primary').props('unelevated rounded')