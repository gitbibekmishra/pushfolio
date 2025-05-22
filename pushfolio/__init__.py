def load_config():
    CONFIG_FILE = ".pushfolio_config.json"

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                console.print("[red]❌ Config file is corrupted. Using default values.[/red]")
                return DEFAULT_CONFIG
    else:
        console.print("[yellow]⚠️ Config file not found. Run 'python main.py init' to create it.[/yellow]")
        return DEFAULT_CONFIG
