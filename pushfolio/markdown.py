import os
import sys
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# ✅ Ensure pushfolio.plugins can be found even if run directly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pushfolio.plugins import discover_plugins

# 🔧 Custom filter: join socials as inline markdown links
def inline_links(socials_dict):
    return " • ".join(f"[{label}]({url})" for label, url in socials_dict.items())

def build_readme(user, repos, languages, top_repo, latest_commit, settings):
    env = Environment(loader=FileSystemLoader("templates"))
    env.filters["inline_links"] = inline_links

    template_file = settings.get("template", "default.md")

    try:
        template = env.get_template(template_file)
    except TemplateNotFound:
        return f"❌ Template '{template_file}' not found in /templates. Please check your config."

    context = {
        "name": user.get("name") or user.get("login", "GitHub User"),
        "bio": settings.get("bio") or user.get("bio") or "💻 Passionate developer on GitHub.",
        "followers": user.get("followers", 0),
        "public_repos": user.get("public_repos", 0),
        "languages": languages or {},
        "socials": {},
        "top_repo": None,
        "latest_commit": None,
        "plugin_blocks": []
    }

    if settings.get("include_socials", True):
        raw = settings.get("socials", {})
        label_map = {
            "linkedin": "LinkedIn",
            "twitter": "Twitter",
            "email": "Email",
            "portfolio": "Portfolio"
        }
        for key, label in label_map.items():
            value = raw.get(key, "").strip()
            if not value:
                continue
            if key == "linkedin":
                context["socials"][label] = f"https://linkedin.com/in/{value}"
            elif key == "twitter":
                context["socials"][label] = f"https://twitter.com/{value}"
            elif key == "email":
                context["socials"][label] = f"mailto:{value}"
            else:
                context["socials"][label] = value

    if settings.get("show_top_repo", True) and top_repo:
        context["top_repo"] = {
            "name": top_repo["name"],
            "url": top_repo["html_url"],
            "stars": top_repo.get("stargazers_count", 0),
            "description": top_repo.get("description", "No description.")
        }

    if settings.get("show_latest_commit", True) and latest_commit:
        commit = latest_commit["commit"]
        raw_date = commit["author"]["date"]
        formatted_date = datetime.strptime(raw_date, "%Y-%m-%dT%H:%M:%SZ").strftime("%d %b %Y")
        context["latest_commit"] = {
            "message": commit["message"],
            "date": formatted_date
        }

    for name, plugin_fn in discover_plugins():
        try:
            block = plugin_fn(user, repos, settings)
            context["plugin_blocks"].append(f"<!-- Plugin: {name} -->\n{block.strip()}")
        except Exception as e:
            context["plugin_blocks"].append(f"<!-- Plugin Error: {name} - {e} -->")

    try:
        rendered = template.render(**context)
        return rendered.strip()
    except Exception as e:
        return f"❌ Template rendering failed: {str(e)}"
