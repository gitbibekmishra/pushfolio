import os
from dotenv import load_dotenv
from rich.console import Console
from rich.prompt import Prompt
from . import fetch, markdown, config
from .ai import generate_bio
import importlib.util
import requests

console = Console()

def ensure_token(env_var, prompt_text, test_url=None):
    token = os.getenv(env_var)

    # Check if missing or placeholder
    invalid_token = (
        not token or
        "your" in token.lower() or
        "placeholder" in token.lower() or
        token.strip() == ""
    )

    if invalid_token:
        console.print(f"[yellow]⚠️ {env_var} not found or invalid in .env[/yellow]")
        token = Prompt.ask(prompt_text)

    # ✅ Validate token if test_url is provided
    if token and test_url:
        headers = {"Authorization": f"Bearer {token}"}
        try:
            response = requests.get(test_url, headers=headers)
            if response.status_code == 401:
                raise Exception("Unauthorized")
        except:
            console.print(f"[red]❌ {env_var} is invalid or unauthorized[/red]")
            token = Prompt.ask(prompt_text + " (re-enter)")

    # 💾 Ask to save or overwrite in .env
    if token:
        should_prompt_save = True

        if os.path.exists(".env"):
            with open(".env", "r") as f:
                for line in f:
                    if line.strip().startswith(f"{env_var}="):
                        if "your" in line.lower() or "placeholder" in line.lower() or len(line.strip()) < 20:
                            should_prompt_save = True
                        else:
                            should_prompt_save = False
                        break

        if should_prompt_save:
            save = Prompt.ask(
                f"💾 Do you want to save this {env_var} to .env for future use? (y/n)",
                choices=["y", "n"],
                default="y"
            )
            if save == "y":
                _write_token(env_var, token)
                console.print(f"[green]✅ Saved {env_var} to .env[/green]")

    if not token:
        console.print(f"[red]❌ {env_var} is required. Exiting...[/red]")
        exit()

    return token

def _write_token(env_var, value):
    if not os.path.exists(".env"):
        with open(".env", "w") as f:
            f.write(f"{env_var}={value}\n")
        return

    with open(".env", "r") as f:
        lines = f.readlines()

    updated = False
    with open(".env", "w") as f:
        for line in lines:
            if line.strip().startswith(f"{env_var}="):
                f.write(f"{env_var}={value}\n")
                updated = True
            else:
                f.write(line)
        if not updated:
            f.write(f"{env_var}={value}\n")

def load_plugins(context):
    plugin_dir = "plugins"
    plugin_outputs = []

    if not os.path.exists(plugin_dir):
        return []

    for filename in os.listdir(plugin_dir):
        if not filename.endswith(".py"):
            continue

        plugin_path = os.path.join(plugin_dir, filename)
        spec = importlib.util.spec_from_file_location(filename[:-3], plugin_path)
        plugin = importlib.util.module_from_spec(spec)
        try:
            spec.loader.exec_module(plugin)
            if hasattr(plugin, "run"):
                output = plugin.run(context)
                if output:
                    plugin_outputs.append(output.strip())
        except Exception as e:
            console.print(f"[red]⚠️ Failed to run plugin {filename}: {e}[/red]")

    return plugin_outputs

def generate_readme():
    load_dotenv()
    settings = config.load_config()

    username = settings.get("github_username") or Prompt.ask("👤 Enter your GitHub username")

    # ✅ GitHub token
    github_token = ensure_token(
        "GITHUB_TOKEN",
        "🔐 Enter your GitHub token",
        test_url="https://api.github.com/user"
    )

    console.print("\n📄 [bold]Generating your GitHub README...[/bold]")

    try:
        user_data = fetch.get_user_data(username, github_token)
        repos_data = fetch.get_repos_data(username, github_token)
        language_stats = fetch.get_language_stats(repos_data)
        top_repo = fetch.get_top_starred_repo(repos_data)
        latest_commit = fetch.get_latest_commit(username, repos_data, github_token)
    except Exception as e:
        console.print(f"[red]❌ Failed to fetch GitHub data: {e}[/red]")
        return

    plugin_context = {
        "username": username,
        "user": user_data,
        "repos": repos_data,
        "languages": language_stats,
        "top_repo": top_repo,
        "latest_commit": latest_commit,
        "settings": settings
    }

    # 🤖 AI-powered About Me (let generate_bio handle fallback logic)
    if settings.get("use_ai", False):
        console.print("[cyan]💡 Attempting to generate About Me using OpenAI...[/cyan]")
        os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY", "")
        bio = generate_bio(plugin_context)
        user_data["bio"] = bio

    plugin_sections = load_plugins(plugin_context)

    readme_content = markdown.build_readme(
        user_data,
        repos_data,
        language_stats,
        top_repo,
        latest_commit,
        settings
    )

    if plugin_sections:
        readme_content += "\n\n" + "\n\n".join(plugin_sections)

    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme_content)

    console.print("[bold green]✅ README.md generated successfully![/bold green]")
