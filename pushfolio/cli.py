import sys
from rich.panel import Panel
import os
import requests
from dotenv import load_dotenv, set_key
from rich.console import Console
from rich.markdown import Markdown
from rich.prompt import Prompt, Confirm

from . import config, core, fetch, markdown as port_markdown
from .language import get_language_stats
from .plugins import discover_plugins

console = Console()

def print_usage():
    console.print(
        "[green]Usage:[/green] pushfolio [init|generate|preview|languages|plugins|gallery|reset-token|config|plugin|theme|openai|help]"
    )
    console.print(
        "[yellow]Smart commands:[/yellow] config show/reset, plugin enable/disable <name>, theme switch, openai reset"
    )

def validate_github_token(token):
    """Live check against GitHub API to ensure the token is valid."""
    if not token:
        console.print("[red]❌ No token found for validation.[/red]")
        return False
    headers = {"Authorization": f"token {token}", "User-Agent": "Pushfolio CLI"}
    try:
        response = requests.get("https://api.github.com/user", headers=headers)
        console.print(f"[cyan][debug] Token status: {response.status_code}[/cyan]")
        if response.status_code == 200:
            console.print(f"[green][debug] Token is valid for: {response.json().get('login')}[/green]")
            return True
        else:
            console.print(f"[red][debug] Invalid token or bad scopes: {response.json().get('message')}[/red]")
            return False
    except Exception as e:
        console.print(f"[red][debug] Token validation exception: {e}[/red]")
        return False

def get_and_save_token():
    """Prompt user for token, clean it, save to .env, and reload environment."""
    token = Prompt.ask("🔐 Enter your GitHub token")
    token = token.strip().replace('"', '').replace("'", '')
    save = Prompt.ask("💾 Save this token to .env for future use?", choices=["yes", "no"], default="yes")
    if save == "yes":
        set_key(".env", "GITHUB_TOKEN", token)
        load_dotenv(override=True)  # Reload so the CLI always uses latest .env
    os.environ["GITHUB_TOKEN"] = token
    return token

def run():
    load_dotenv(override=True)

    if len(sys.argv) < 2:
        console.print("[red]❌ No command provided.[/red]")
        print_usage()
        return

    cmd = sys.argv[1].lower()

    if cmd == "init":
        config.init_config()

    elif cmd in ("generate", "gen"):
        core.generate_readme()

    elif cmd == "preview":
        from argparse import ArgumentParser

        parser = ArgumentParser(prog="pushfolio preview")
        parser.add_argument("--save", action="store_true", help="Save preview to 'preview.md'")
        parser.add_argument("--theme", type=str, help="Use a specific template")
        args = parser.parse_args(sys.argv[2:])

        settings = config.load_config()

        if args.theme:
            settings["template"] = args.theme
            console.print(f"[cyan]🎨 Using template override: {args.theme}[/cyan]")

        username = settings.get("github_username")
        if not username:
            username = Prompt.ask("👤 Enter your GitHub username")
            settings["github_username"] = username
            config.save_config(settings)

        token = os.getenv("GITHUB_TOKEN", "").strip()
        console.print(f"[cyan][debug] Token loaded: {token[:6]}...{token[-4:] if token else ''}[/cyan]")

        if not token or not validate_github_token(token):
            console.print("[yellow]⚠️ GITHUB_TOKEN not found, invalid, or failed validation.[/yellow]")
            token = get_and_save_token()
            if not validate_github_token(token):
                console.print("[red]❌ Provided token is still invalid. Exiting preview.[/red]")
                return

        console.print("\n📄 [bold]Generating preview...[/bold]")

        try:
            user_data = fetch.get_user_data(username, token)
            repos_data = fetch.get_repos_data(username, token)
            language_stats = fetch.get_language_stats(repos_data)
            top_repo = fetch.get_top_starred_repo(repos_data)
            latest_commit = fetch.get_latest_commit(username, repos_data, token)

            if settings.get("use_ai", False) and not settings.get("bio"):
                from .ai import generate_bio
                context = {
                    "username": username,
                    "languages": language_stats,
                    "top_repo": top_repo,
                    "repos": repos_data
                }
                settings["bio"] = generate_bio(context)
                config.save_config(settings)

            content = port_markdown.build_readme(
                user_data,
                repos_data,
                language_stats,
                top_repo,
                latest_commit,
                settings
            )

            if args.save:
                with open("preview.md", "w", encoding="utf-8") as f:
                    f.write(content)
                console.print("[green]✅ Preview saved to [bold]preview.md[/bold][/green]")
            else:
                console.print(Markdown(content))

        except Exception as e:
            console.print(f"[red]❌ Preview failed: {e}[/red]")

    elif cmd == "help":
        console.print(Panel.fit(
            "🔑 [bold]How to get a GitHub token:[/bold]\n"
            "1. Go to: [cyan underline]https://github.com/settings/tokens/new?scopes=read:user,public_repo[/cyan underline]\n"
            "2. Name it (e.g., Pushfolio), set an expiry (30+ days is fine)\n"
            "3. Check [bold]read:user[/bold] and [bold]public_repo[/bold] scopes\n"
            "4. Click [bold]'Generate token'[/bold] and copy it (starts with ghp_...)\n"
            "5. Paste it when Pushfolio asks!\n\n"
            "🤖 [bold]How to get an OpenAI API key (for AI About Me):[/bold]\n"
            "1. Go to: [cyan underline]https://platform.openai.com/api-keys[/cyan underline]\n"
            "2. Click [bold]'Create new secret key'[/bold]\n"
            "3. Paste it when Pushfolio asks!\n",
            title="Pushfolio Help", style="bold blue"
        ))

    elif cmd == "languages":
        settings = config.load_config()

        username = settings.get("github_username")
        if not username:
            username = Prompt.ask("👤 Enter your GitHub username")
            settings["github_username"] = username
            config.save_config(settings)

        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token or not validate_github_token(token):
            console.print("[yellow]⚠️ GITHUB_TOKEN not found or invalid in .env[/yellow]")
            token = get_and_save_token()
            if not validate_github_token(token):
                console.print("[red]❌ Provided token is still invalid. Exiting.[/red]")
                return

        try:
            languages = get_language_stats(username, token)
            if not languages:
                console.print("[yellow]⚠️ No languages found. Check your GitHub username or repo visibility.[/yellow]")
                return

            console.print(f"\n🧠 [bold cyan]Top Languages Used by {username}[/bold cyan]")
            for lang, byte_count in languages[:10]:
                console.print(f"  • [green]{lang}[/green]: {byte_count:,} bytes")
        except Exception as e:
            console.print(f"[red]❌ Error:[/red] {e}")

    elif cmd == "plugins":
        console.print("\n🧩 [bold cyan]Available Plugins[/bold cyan]")
        plugins = discover_plugins()
        if not plugins:
            console.print("No plugins found.")
        for name, _ in plugins:
            console.print(f"  • [green]{name}[/green]")

    elif cmd == "gallery":
        from os import listdir
        from . import markdown

        settings = config.load_config()

        username = settings.get("github_username")
        if not username:
            username = Prompt.ask("👤 Enter your GitHub username")
            settings["github_username"] = username
            config.save_config(settings)

        token = os.getenv("GITHUB_TOKEN", "").strip()
        if not token or not validate_github_token(token):
            console.print("[yellow]⚠️ GITHUB_TOKEN not found or invalid in .env[/yellow]")
            token = get_and_save_token()
            if not validate_github_token(token):
                console.print("[red]❌ Provided token is still invalid. Exiting gallery.[/red]")
                return

        user_data = fetch.get_user_data(username, token)
        repos_data = fetch.get_repos_data(username, token)
        language_stats = fetch.get_language_stats(repos_data)
        top_repo = fetch.get_top_starred_repo(repos_data)
        latest_commit = fetch.get_latest_commit(username, repos_data, token)

        templates = [f for f in listdir("templates") if f.endswith(".md")]
        for template in templates:
            console.rule(f"🧩 {template}")
            dummy_settings = {
                **settings,
                "template": template
            }
            preview = port_markdown.build_readme(
                user_data,
                repos_data,
                language_stats,
                top_repo,
                latest_commit,
                dummy_settings
            )
            console.print(Markdown(preview))

    elif cmd == "reset-token":
        if Confirm.ask("🔐 Do you want to reset your GitHub token?", default=True):
            token = get_and_save_token()
            if not validate_github_token(token):
                console.print("[red]❌ Provided token is still invalid.[/red]")
                return
            console.print("[green]✅ GitHub token updated successfully![/green]")
        else:
            console.print("[dim]ℹ️ No changes made.[/dim]")

    # --- SMART COMMANDS ---
    elif cmd == "config":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else None
        if subcmd == "show":
            settings = config.load_config()
            console.print("[bold cyan]Current Pushfolio Config:[/bold cyan]")
            for k, v in settings.items():
                console.print(f"[yellow]{k}[/yellow]: {v}")
        elif subcmd == "reset":
            if Confirm.ask("[red]Are you sure you want to reset Pushfolio config?[/red]", default=False):
                config.save_config(config.DEFAULT_CONFIG)
                console.print("[green]✅ Config reset to defaults.[/green]")
        else:
            console.print("[yellow]Usage: pushfolio config show|reset[/yellow]")

    elif cmd == "plugin":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else None
        plugin_name = sys.argv[3] if len(sys.argv) > 3 else None
        plugins_cfg = config.load_config().get("plugins", {})
        if subcmd == "enable" and plugin_name:
            plugins_cfg[plugin_name] = True
            settings = config.load_config()
            settings["plugins"] = plugins_cfg
            config.save_config(settings)
            console.print(f"[green]Enabled plugin: {plugin_name}[/green]")
        elif subcmd == "disable" and plugin_name:
            plugins_cfg[plugin_name] = False
            settings = config.load_config()
            settings["plugins"] = plugins_cfg
            config.save_config(settings)
            console.print(f"[red]Disabled plugin: {plugin_name}[/red]")
        else:
            console.print("[yellow]Usage: pushfolio plugin enable <name> | disable <name>[/yellow]")

    elif cmd == "theme":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else None
        if subcmd == "switch":
            from os import listdir
            templates = [f for f in listdir("templates") if f.endswith(".md")]
            console.print("[bold cyan]Available templates:[/bold cyan]")
            for idx, name in enumerate(templates, 1):
                console.print(f"{idx}. {name}")
            choice = Prompt.ask("Choose a template number", choices=[str(i) for i in range(1, len(templates)+1)])
            chosen = templates[int(choice)-1]
            settings = config.load_config()
            settings["template"] = chosen
            config.save_config(settings)
            console.print(f"[green]Theme switched to: {chosen}[/green]")
        else:
            console.print("[yellow]Usage: pushfolio theme switch[/yellow]")

    elif cmd == "openai":
        subcmd = sys.argv[2] if len(sys.argv) > 2 else None
        if subcmd == "reset":
            new_key = Prompt.ask("🔑 Enter new OpenAI API key")
            set_key(".env", "OPENAI_API_KEY", new_key)
            load_dotenv(override=True)
            os.environ["OPENAI_API_KEY"] = new_key
            console.print("[green]✅ OpenAI API key updated successfully![/green]")
        else:
            console.print("[yellow]Usage: pushfolio openai reset[/yellow]")

    else:
        console.print(f"[red]❌ Unknown command: {cmd}[/red]")
        print_usage()
