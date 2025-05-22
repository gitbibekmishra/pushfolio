# pushfolio/plugins/__init__.py

import os
import importlib
from rich.console import Console

console = Console()

def discover_plugins():
    plugin_folder = os.path.dirname(__file__)
    plugin_files = [
        f for f in os.listdir(plugin_folder)
        if f.endswith(".py") and f != "__init__.py"
    ]
    plugins = []
    for file in plugin_files:
        name = file[:-3]  # strip .py
        try:
            module = importlib.import_module(f"pushfolio.plugins.{name}")
            if hasattr(module, "register"):
                plugins.append((name, module.register))
            else:
                console.print(f"[yellow]⚠️ Plugin '{name}' skipped: missing register()[/yellow]")
        except Exception as e:
            console.print(f"[red]❌ Failed to load plugin '{name}': {e}[/red]")
    return plugins
