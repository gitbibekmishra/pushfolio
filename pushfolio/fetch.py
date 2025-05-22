import requests
from collections import defaultdict

def github_request(url, token):
    # Detect token type for Authorization header
    if token.startswith("github_pat_") or token.startswith("gho_"):
        auth_type = "Bearer"
    else:
        auth_type = "token"

    headers = {
        "Authorization": f"{auth_type} {token}",
        "User-Agent": "Pushfolio CLI"
    }

    # Debugging - safe token display
    print(f"🔎 [DEBUG] Requesting: {url}")
    print(f"🧠 [DEBUG] Auth header: {auth_type} {token[:4]}...{token[-4:]}")

    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()

def get_user_data(username, token):
    url = f"https://api.github.com/users/{username}"
    return github_request(url, token)

def get_repos_data(username, token):
    url = f"https://api.github.com/users/{username}/repos?per_page=100&sort=updated"
    return github_request(url, token)

def get_language_stats(repos):
    stats = defaultdict(int)
    for repo in repos:
        lang = repo.get("language")
        if lang:
            stats[lang] += 1
    return dict(stats)

def get_top_starred_repo(repos):
    if not repos:
        return None
    return max(repos, key=lambda r: r.get("stargazers_count", 0))

def get_latest_commit(username, repos, token):
    for repo in repos:
        if repo.get("fork"):
            continue
        repo_name = repo["name"]
        url = f"https://api.github.com/repos/{username}/{repo_name}/commits"
        try:
            commits = github_request(url, token)
            if commits:
                return commits[0]
        except Exception:
            continue
    return None
