# pushfolio/ai.py

import os
import json
from rich.console import Console
from rich.prompt import Prompt

console = Console()
CACHE_FILE = ".pushfolio_cache.json"

try:
    import openai
except ImportError:
    openai = None


def get_cached_bio(username):
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                data = json.load(f)
                return data.get(username)
        except:
            pass
    return None


def generate_bio(context):
    username = context.get("username", "developer")

    if not openai:
        console.print("[red]❌ OpenAI module is not installed. Install it with:[/red] [bold]pip install openai[/bold]")
        return fallback_bio(context)

    openai.api_key = os.getenv("OPENAI_API_KEY", "")
    if not openai.api_key.strip() or "your" in openai.api_key.lower():
        console.print("[red]❌ No valid OpenAI API key found[/red]")
        return handle_ai_failure("Missing API key", context)

    cached_bio = get_cached_bio(username)

    # ✨ Compose prompt from GitHub data
    languages = ", ".join(context.get("languages", {}).keys())
    top_repo = context.get("top_repo", {}).get("name", "a top project")
    stars = context.get("top_repo", {}).get("stars", 0)
    repos = context.get("repos", [])
    repo_names = ", ".join([r["name"] for r in repos[:5]])

    prompt = (
        f"Generate a short, friendly 'About Me' for a GitHub profile:\n\n"
        f"Username: {username}\n"
        f"Languages: {languages or 'N/A'}\n"
        f"Top repo: {top_repo} ({stars} stars)\n"
        f"Recent repos: {repo_names or 'None'}\n\n"
        f"Tone: Friendly, developer-focused, 2-3 sentences."
    )

    for attempt in range(2):
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=150
            )
            bio = response.choices[0].message.content.strip()

            # Cache it
            data = {}
            if os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r") as f:
                        data = json.load(f)
                except:
                    pass
            data[username] = bio
            with open(CACHE_FILE, "w") as f:
                json.dump(data, f, indent=2)

            console.print("[green]✅ Generated new About Me using OpenAI and cached it[/green]")
            return bio

        except Exception as e:
            console.print(f"[red]❌ OpenAI failed: {e}[/red]")
            return handle_ai_failure(str(e), context, cached_bio)

    return fallback_bio(context)


def fallback_bio(context):
    primary = (list(context.get("languages", {}).keys()) or ["developer"])[0]
    fallback = f"I'm a {primary} developer passionate about open-source and building cool stuff."
    console.print("[cyan]🧩 Using fallback About Me[/cyan]")
    return fallback


def handle_ai_failure(error, context, cached_bio=None):
    username = context.get("username", "developer")

    choice = Prompt.ask(
        "[yellow]What would you like to do?[/yellow]\n"
        "[1] Re-enter OpenAI key\n"
        "[2] Use cached About Me\n"
        "[3] Use fallback About Me\n"
        "[4] Skip About Me",
        choices=["1", "2", "3", "4"],
        default="3"
    )

    if choice == "1":
        new_key = Prompt.ask("🔑 Enter your OpenAI API key")
        os.environ["OPENAI_API_KEY"] = new_key
        if openai:
            openai.api_key = new_key
        return generate_bio(context)

    elif choice == "2":
        if cached_bio:
            console.print("[blue]📦 Using cached About Me[/blue]")
            return cached_bio
        else:
            console.print("[red]⚠️ No cached bio available. Using fallback...[/red]")
            return fallback_bio(context)

    elif choice == "3":
        return fallback_bio(context)

    elif choice == "4":
        console.print("[dim]ℹ️ Skipping About Me generation[/dim]")
        return ""
