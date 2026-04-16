# Plugin Development Guide

Lyndrix Core is architected as a highly modular platform. Every custom tool you build – such as a Docker dashboard, infrastructure orchestrator, or team utility – is an isolated plugin that integrates seamlessly with the core system.

---

## Plugin Architecture

### Directory Structure

Plugins are located in the `app/plugins/` directory within their own subdirectory:

```
app/plugins/your_plugin_name/
├── entrypoint.py          # Main plugin logic & UI entry point
├── requirements.txt       # Plugin-specific dependencies (optional)
├── assets/               # Images, CSS, configurations (optional)
│   ├── logo.png
│   └── styles.css
└── README.md             # Plugin documentation
```

**Important**: Plugin directory names must be valid Python identifiers (no hyphens; use underscores instead).

---

## Module Manifest

Every plugin begins with a `ModuleManifest` object. This declares to the core system who your plugin is, what permissions it requires, and how it integrates.

### Manifest Definition

```python
from core.components.plugins.logic.models import ModuleManifest

manifest = ModuleManifest(
    id="lyndrix.plugin.unique_identifier",
    name="My Plugin Name",
    version="1.0.0",
    description="A brief description of what your plugin does.",
    author="Your Name or Organization",
    icon="rocket_launch",  # Material Design icon name
    type="PLUGIN",
    ui_route="/my-plugin",  # Automatically registers in navigation menu
    permissions={
        "subscribe": ["system:boot_complete", "vault:ready_for_data"],
        "emit": ["my_plugin:action_completed"]
    }
)
```

### Manifest Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | Yes | Unique plugin identifier (reverse domain notation recommended) |
| `name` | string | Yes | Human-readable plugin name |
| `version` | string | Yes | Semantic version (e.g., "1.0.0") |
| `description` | string | Yes | Brief description displayed in plugin marketplace |
| `author` | string | Yes | Plugin author or organization name |
| `icon` | string | No | Material Design icon (defaults to 'extension') |
| `type` | string | Yes | Must be "PLUGIN" or "CORE" |
| `ui_route` | string | No | HTTP route for plugin's main page (auto-registers in nav) |
| `permissions.subscribe` | string[] | No | Event types the plugin can subscribe to |
| `permissions.emit` | string[] | No | Event types the plugin can emit |

---

## Plugin Lifecycle: The `setup()` Function

When Lyndrix Core boots, it invokes the `setup(ctx)` function from your plugin's entrypoint. This is where you register UI routes, subscribe to events, and initialize plugin state.

```python
from nicegui import ui
from ui.layout import main_layout
from core.logger import get_logger

log = get_logger("Plugin:MyPlugin")

async def setup(ctx):
    """
    Main plugin initialization function.
    
    Args:
        ctx: ModuleContext - Provides access to logging, events, vault, and database
    """
    ctx.log.info("MyPlugin: Initializing...")
    
    # Register main UI page
    @ui.page('/my-plugin')
    @main_layout('My Plugin')
    async def plugin_page():
        ui.label('Welcome to My Plugin!').classes('text-2xl font-bold')
        ui.separator()
        
        # Your plugin UI logic here
        with ui.column().classes('gap-4'):
            ui.label('Plugin Content Goes Here')
    
    # Subscribe to system events
    @ctx.subscribe('system:boot_complete')
    async def on_boot_complete(payload):
        ctx.log.info("System boot completed, plugin ready for operations")
    
    # Subscribe to vault-ready event (required before accessing vault)
    @ctx.subscribe('vault:ready_for_data')
    async def on_vault_ready(payload):
        ctx.log.info("Vault is now accessible")
    
    ctx.log.info("MyPlugin: Setup complete")
```

### ModuleContext (`ctx`) API

The `ctx` parameter provides your plugin with safe access to system resources:

```python
# Logging
ctx.log.info("Message")
ctx.log.warning("Warning")
ctx.log.error("Error")

# Event subscription
@ctx.subscribe('event:name')
async def handler(payload):
    pass

# Event emission
ctx.emit('my_plugin:event', {"data": "value"})

# Vault access (secure secrets storage)
ctx.vault.kv_v2_write(path="my_plugin/secret", data={"key": "value"})
secret = ctx.vault.kv_v2_read(path="my_plugin/secret")

# Database access
ctx.db.query(MyModel).filter_by(name="example").first()

# Configuration
settings = ctx.settings  # Access plugin-specific settings from .env
```

---

## Plugin Integration Points

### 1. Main UI Page

Register your plugin's primary interface using the `main_layout` decorator:

```python
from ui.layout import main_layout

@ui.page('/my-plugin')
@main_layout('Plugin Title')
async def plugin_page():
    # Your UI code here
    ui.label('Content')
```

The `main_layout` decorator automatically:
- Creates a professional page layout
- Adds header and sidebar navigation
- Handles theme switching
- Provides logout functionality

### 2. Settings Modal

Plugins can expose configuration UI through a settings modal. Implement the `render_settings_ui()` function:

```python
def render_settings_ui(ctx):
    """
    Renders the plugin's settings interface.
    This is called when a user clicks the settings icon for your plugin.
    
    Args:
        ctx: ModuleContext - Plugin context
    """
    with ui.column().classes('gap-4'):
        ui.label('Plugin Settings').classes('text-lg font-bold')
        
        # Example: Settings toggle
        enable_feature = ui.checkbox('Enable Feature X')
        
        # Save callback
        def save_settings():
            ctx.vault.kv_v2_write(
                path="my_plugin/settings",
                data={"feature_x_enabled": enable_feature.value}
            )
            ui.notify('Settings saved', type='positive')
        
        ui.button('Save Settings', on_click=save_settings)
```

**Note**: The settings modal is automatically managed by Lyndrix Core. Your implementation is called within a styled dialog that handles presentation.

### 3. Dashboard Widget

Plugins can display a status/summary widget on the main dashboard. Implement `render_dashboard_widget()`:

```python
def render_dashboard_widget(ctx):
    """
    Renders a compact widget displayed on the system dashboard.
    Used for status indicators, quick actions, or metrics.
    
    Args:
        ctx: ModuleContext - Plugin context
    """
    from ui.theme import UIStyles
    
    # Get current status
    status = ctx.vault.kv_v2_read(path="my_plugin/status") or {"state": "idle"}
    
    with ui.card().classes(f'{UIStyles.CARD_GLASS} p-4 hover:border-blue-500/50'):
        with ui.row().classes('justify-between items-center'):
            with ui.column().classes('gap-1'):
                ui.label('My Plugin Status').classes('font-bold')
                ui.label(f"State: {status['state']}").classes('text-sm text-gray-400')
            
            # Status indicator color
            color = 'green-500' if status['state'] == 'active' else 'yellow-500'
            ui.icon('circle').classes(f'text-{color} text-xl')
```

**Widget Guidelines**:
- Keep widgets compact (single card recommended)
- Display only essential information
- Use the `UIStyles.CARD_GLASS` class for consistent theming
- Avoid blocking operations (use async if needed)

---

## Event System

Lyndrix Core uses a pub/sub event bus for decoupled communication. Plugins can subscribe to and emit events.

### Common System Events

| Event | Payload | Description |
|-------|---------|-------------|
| `system:boot_complete` | `{}` | Emitted when core system initialization is complete |
| `system:shutdown` | `{}` | Emitted before system shutdown |
| `vault:ready_for_data` | `{}` | Emitted when Vault is unsealed and ready |
| `vault:opened` | `{}` | Emitted when Vault connection established |
| `db:connected` | `{}` | Emitted when database connection is ready |
| `plugin:install_started` | `{"repo": "name"}` | Emitted when plugin installation begins |
| `plugin:install_completed` | `{"repo": "name"}` | Emitted when plugin installation succeeds |

### Publishing Events

```python
@ctx.subscribe('system:boot_complete')
async def handle_boot(payload):
    # Do something on boot
    ctx.emit('my_plugin:initialized', {"timestamp": time.time()})
```

---

## Working with Vault

Vault provides secure storage for sensitive data. Each plugin has an isolated Vault path.

### Reading Secrets

```python
# Read plugin-specific secret
secret_data = ctx.vault.kv_v2_read(path="my_plugin/api_key")
if secret_data:
    api_key = secret_data['data']['data']['key']
```

### Writing Secrets

```python
# Store sensitive configuration
ctx.vault.kv_v2_write(
    path="my_plugin/credentials",
    data={
        "username": "admin",
        "password": "secure_password"
    }
)
```

### Best Practices

- Always store secrets in Vault, never in environment variables
- Use plugin-specific paths: `my_plugin/secret_name`
- Never log sensitive data
- Encrypt plugin-to-plugin communication

---

## Example: Complete Plugin

Here's a complete example of a functional plugin:

```python
# entrypoint.py

from nicegui import ui
from ui.layout import main_layout
from ui.theme import UIStyles
from core.components.plugins.logic.models import ModuleManifest
from core.logger import get_logger
import asyncio

log = get_logger("Plugin:StatusMonitor")

manifest = ModuleManifest(
    id="lyndrix.plugin.status_monitor",
    name="Status Monitor",
    version="1.0.0",
    description="Real-time system status monitoring",
    author="Your Name",
    icon="monitoring",
    type="PLUGIN",
    ui_route="/monitor",
    permissions={
        "subscribe": ["system:boot_complete", "system:metrics_update"],
        "emit": ["monitor:alert"]
    }
)

# Plugin state
plugin_state = {"metrics": {}, "auto_refresh": True}

async def setup(ctx):
    log.info("StatusMonitor: Starting initialization...")
    
    # Main page
    @ui.page('/monitor')
    @main_layout('System Monitor')
    async def monitor_page():
        metrics_container = ui.column()
        
        @ctx.subscribe('system:metrics_update')
        async def update_display(payload):
            plugin_state["metrics"] = payload
            with metrics_container:
                metrics_container.clear()
                ui.label('CPU Usage').classes('font-bold')
                ui.linear_progress(value=payload.get('cpu', 0) / 100)
                ui.label(f"{payload.get('cpu', 0):.1f}%")
        
        with metrics_container:
            ui.label('Waiting for metrics...').classes('text-gray-400')
    
    def render_settings_ui(ctx):
        with ui.column().classes('gap-4'):
            ui.checkbox('Auto-refresh metrics', value=plugin_state["auto_refresh"])
            ui.button('Reset statistics', on_click=lambda: ui.notify('Reset'))
    
    def render_dashboard_widget(ctx):
        with ui.card().classes(f'{UIStyles.CARD_GLASS} p-4'):
            ui.label('System Health').classes('font-bold')
            metrics = plugin_state.get("metrics", {})
            ui.label(f"CPU: {metrics.get('cpu', 0):.1f}%").classes('text-sm')
            ui.label(f"Memory: {metrics.get('ram', 0):.1f}%").classes('text-sm')
    
    log.info("StatusMonitor: Initialization complete")
```

---

## Installing Plugin Dependencies

Plugins can declare Python dependencies in a `requirements.txt` file:

```
# app/plugins/my_plugin/requirements.txt
requests==2.31.0
python-dateutil==2.8.2
```

**Note**: Plugin dependencies are isolated and installed only for that plugin during initialization. This prevents dependency conflicts between plugins.

---

## Plugin Marketplace

Plugins can be distributed via GitHub repositories. To publish a plugin:

1. Create a GitHub repository with your plugin code
2. Ensure the repository contains `entrypoint.py` and `ModuleManifest`
3. Add the repository URL to the plugin marketplace
4. Users can install via the Lyndrix Core plugin manager

### Installing from Marketplace

```bash
# In Lyndrix Core UI: Plugins > Marketplace > Select Plugin > Install
# Or via API:
POST /api/plugins/install
{
    "github_url": "https://github.com/username/plugin-repo"
}
```

---

## Debugging Plugins

Enable debug logging to troubleshoot plugin issues:

```bash
# Set environment variable
export LOG_LEVEL=DEBUG

# Or in docker/.env
LOG_LEVEL=DEBUG
```

Check logs in the web UI or console output for plugin-specific messages.

---

## Best Practices

✅ **Do**:
- Use the provided `ModuleContext` for all system interactions
- Store sensitive data in Vault
- Keep UI responsive (avoid blocking operations)
- Implement proper error handling
- Document your plugin thoroughly
- Follow the naming convention: `lyndrix.plugin.name`

❌ **Don't**:
- Directly access the database without ORM
- Store secrets as environment variables
- Use synchronous I/O in setup functions
- Create global state outside the setup function
- Assume plugin load order
- Emit events core plugins might depend on

---

## Troubleshooting

### Plugin Not Appearing in Navigation

- Ensure `ui_route` is defined in manifest
- Verify plugin status is "active" in plugin manager
- Check logs for initialization errors

### Settings Modal Not Working

- Implement `render_settings_ui(ctx)` function
- Ensure function signature is correct
- Test Vault access inside the function

### Dashboard Widget Not Showing

- Implement `render_dashboard_widget(ctx)` function
- Verify function returns valid UI components
- Check plugin status is "active"

### Events Not Triggering

- Verify event name in permissions.subscribe
- Use full event namespace (e.g., `system:boot_complete`)
- Check async/await syntax in handler

---

## Resources

- **Example Plugins**: See `app/plugins/` for reference implementations
- **Event Bus**: [Event System Documentation](architecture.md#event-bus)
- **NiceGUI Docs**: https://nicegui.io/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
