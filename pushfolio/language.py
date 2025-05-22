import requests

def get_language_stats(username, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"token {token}"

    repos_url = f"https://api.github.com/users/{username}/repos?per_page=100"
    response = requests.get(repos_url, headers=headers)
    repos = response.json()

    if not isinstance(repos, list):
        raise Exception(f"GitHub API Error: {repos.get('message', 'Unknown error')}")

    language_totals = {}

    for repo in repos:
        if repo.get("fork"):
            continue
        lang_url = repo["languages_url"]
        lang_response = requests.get(lang_url, headers=headers)
        repo_langs = lang_response.json()
        for lang, bytes in repo_langs.items():
            language_totals[lang] = language_totals.get(lang, 0) + bytes

    # Sort by most-used
    sorted_langs = sorted(language_totals.items(), key=lambda x: x[1], reverse=True)
    return sorted_langs
