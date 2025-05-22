# pushfolio/config.py

import json
import os
from rich.prompt import Prompt
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from dotenv import set_key, load_dotenv

console = Console()
CONFIG_FILE = ".pushfolio_config.json"
ENV_PATH = ".env"

DEFAULT_CONFIG = {
    "show_about": True,
    "show_top_repo": True,
    "show_latest_commit": True,
    "show_languages": True,
    "use_ai": False,
    "include_socials": True,
    "theme": "emoji-fun",
    "template": "default.md",
    "socials": {
        "linkedin": "",
        "twitter": "",
        "email": "",
        "portfolio": ""
    }
}

def preview_markdown_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        console.print(Markdown(content))
    except:
        console.print("[red]⚠️ Failed to load template preview.[/red]")

def select_template_with_preview():
    templates_dir = "templates"
    try:
        files = [f for f in os.listdir(templates_dir) if f.endswith(".md")]
    except FileNotFoundError:
        console.print(f"[red]❌ 'templates' folder not found![/red]")
        return "default.md"

    numbered = {str(i + 1): f for i, f in enumerate(files)}

    while True:
        console.print("\n📂 [bold cyan]Available Templates in /templates:[/bold cyan]")
        for key, filename in numbered.items():
            console.print(f"[bold green]{key}.[/bold green] {filename}")
        console.print("[bold red]0.[/bold red] ❌ Cancel\n")

        choice = Prompt.ask("🧩✨ Select a template number to preview or 0 to cancel", default="1")

        if choice == "0":
            console.print("[bold red]🚪 Cancelled template selection.[/bold red]")
            return None

        if choice in numbered:
            filepath = os.path.join(templates_dir, numbered[choice])
            console.print(f"\n[bold cyan]🔍 Previewing: {numbered[choice]}[/bold cyan]\n")
            preview_markdown_file(filepath)

            next_action = Prompt.ask("\n[bold yellow]Press [C] to choose, [B] to go back[/bold yellow]", choices=["C", "B"], default="C")
            if next_action.upper() == "C":
                return numbered[choice]
            else:
                continue
        else:
            console.print("[red]Invalid input. Please try again.[/red]")

def init_config():
    # Only prompt for token if missing
    token = os.getenv("GITHUB_TOKEN", "").strip()
    console.print(Panel.fit(
        "👑✨ [bold magenta]Welcome to Pushfolio! ✨\n\n"
        "🚀 Let's make your GitHub shine with style and fun! 🚀\n"
        "We'll build your profile your way—no coding required, just your awesome self! 😎\n\n"
        "🖊️ [dim]Created by Bibek Mishra[/dim]",
        title="🦄👋 Pushfolio Quick Start 👋🦄",
        style="bold bright_cyan"
    ))

    if not token:
        console.print("🔑 Please paste your GitHub token.\n[dim]Need help? Type [yellow]python -m pushfolio help[/yellow]![/dim]")
        token = Prompt.ask("Paste your token (starts with ghp_) ✨")
        token = token.strip().replace('"', '').replace("'", '')
        try:
            set_key(ENV_PATH, "GITHUB_TOKEN", token)
            load_dotenv(override=True)
            os.environ["GITHUB_TOKEN"] = token
            console.print("[green]🔒 Token saved! You're ready to go![/green]")
        except Exception:
            console.print("[red]❌ Couldn't save token. Please add to .env manually as GITHUB_TOKEN=...[/red]")

    # Onboarding prompts (creative & friendly)
    console.print("🌟 [bold magenta]Let's personalize your portfolio![/bold magenta] 🌟")
    name = Prompt.ask("📝 What's your full name?")
    if not name.strip():
        name = "Your Name"

    bio = Prompt.ask("🌈 Your short bio (one line about you):", default="💻 Passionate developer on GitHub. 🚀")
    linkedin = Prompt.ask("🔗 LinkedIn username (after /in/)", default="")
    twitter = Prompt.ask("🐦 Twitter handle (no @)", default="")
    email = Prompt.ask("✉️ Email (optional)", default="")
    portfolio = Prompt.ask("🌐 Portfolio/website (optional)", default="")

    # Theme picker
    console.print("\n🎨 [bold cyan]Choose your profile theme![/bold cyan]\n(Preview before you pick!)")
    template = select_template_with_preview()
    if not template:
        template = "default.md"

    # AI About Me (optional, friendly)
    use_ai = Prompt.ask("🤖 Want Pushfolio to write your About Me with AI magic? (yes/no)", choices=["yes", "no"], default="no")
    ai_bio = ""
    if use_ai == "yes":
        openai_key = os.getenv("OPENAI_API_KEY", "").strip()
        if not openai_key:
            console.print("🤖🔑 Paste your OpenAI API key (or type [yellow]python -m pushfolio help[/yellow] for instructions)")
            key = Prompt.ask("OpenAI API key")
            set_key(ENV_PATH, "OPENAI_API_KEY", key)
            os.environ["OPENAI_API_KEY"] = key
        try:
            from .ai import generate_bio
            console.print("\n✨🤖 Generating your AI-powered bio...")
            context = {"username": name, "languages": {}, "top_repo": {}, "repos": []}
            ai_bio = generate_bio(context)
            bio = ai_bio or bio
        except Exception as e:
            console.print(f"[red]AI bio generation failed: {e}[/red]")
            ai_bio = ""

    # Save Config
    config = DEFAULT_CONFIG.copy()
    config["theme"] = template
    config["template"] = template
    config["name"] = name
    config["bio"] = bio
    config["socials"] = {
        "linkedin": linkedin,
        "twitter": twitter,
        "email": email,
        "portfolio": portfolio
    }
    config["show_about"] = True
    config["use_ai"] = use_ai == "yes"

    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f, indent=4)
        console.print(Panel.fit(
            f"🥳 [green]Setup complete![/green] 🥳\n[cyan]Your chosen theme:[/cyan] {template}\n"
            f"[bold]✨ Your story is ready to shine! ✨[/bold]",
            title="🎉🚀 All done! 🚀🎉", style="bold green"))
        console.print("[bold blue]Type [yellow]python -m pushfolio preview[/yellow] to see your profile! 🖼️[/bold blue]")
        console.print("[dim]Need token or AI help? Type [yellow]python -m pushfolio help[/yellow] 💡[/dim]\n")
    except Exception as e:
        console.print(f"[red]❌ Could not save config: {e}[/red]")
        console.print("Try running the program as administrator, or check file permissions.")

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                console.print("[red]❌ Config file is corrupted. Using default values.[/red]")
                return DEFAULT_CONFIG
    else:
        console.print("[yellow]⚠️ Config file not found. Run 'python -m pushfolio init' to create it.[/yellow]")
        return DEFAULT_CONFIG

def save_config(data):
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)
