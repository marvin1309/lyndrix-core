from nicegui import ui
from ui.layout import main_layout
from .dashboard_ui import render_dashboard_page

def register_dashboard_routes():
    @ui.page('/dashboard')
    @main_layout('Dashboard')
    async def dashboard_page():
        await render_dashboard_page()