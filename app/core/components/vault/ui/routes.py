from nicegui import ui
from .setup_ui import render_setup_wizard
from .unseal_ui import render_unseal_page

def register_vault_routes():
    @ui.page('/setup')
    def setup_page():
        render_setup_wizard()

    @ui.page('/unseal')
    def unseal_page():
        render_unseal_page()