# 👋 Welcome to My GitHub

## About Me
Hi! I'm **{{ name }}**  
{{ bio }}

👥 Followers: `{{ followers }}`  
📂 Public Repos: `{{ public_repos }}`

{% if top_repo %}
## 🚀 Top Repo
[{{ top_repo.name }}]({{ top_repo.url }})  
⭐ Stars: `{{ top_repo.stars }}`  
📄 {{ top_repo.description }}
{% endif %}

{% if latest_commit %}
## 📌 Latest Commit
📝 _"{{ latest_commit.message }}"_  
📅 `{{ latest_commit.date }}`
{% endif %}

{% if languages %}
## 📊 Languages
{% for lang, count in languages.items() %}
- **{{ lang }}**: {{ "🟩" * (count if count < 10 else 10) }} ({{ count }} repos)
{% endfor %}
{% endif %}

{% if socials %}
## 🌐 Connect
{% for label, url in socials.items() %}
[{{ label }}]({{ url }}) • 
{% endfor %}
{% endif %}

---

_🛠️ Generated with [Pushfolio](https://github.com/gitbibekmishra/pushfolio)_
