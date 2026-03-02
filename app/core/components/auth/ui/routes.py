from nicegui import ui
from .login_ui import render_login_page

def register_auth_routes():
    @ui.page('/login')
    def login_page():
        render_login_page()