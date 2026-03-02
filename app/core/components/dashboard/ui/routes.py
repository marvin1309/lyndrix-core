from nicegui import ui
from ui.layout import main_layout
from .dashboard_ui import render_dashboard_page

def register_dashboard_routes():
    @ui.page('/dashboard')
    @main_layout('Dashboard') # Der Rahmen
    async def dashboard_page(): # MUSS async sein
        await render_dashboard_page() # MUSS awaited werden