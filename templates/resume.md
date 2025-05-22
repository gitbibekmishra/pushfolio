# {{ name }} – GitHub Developer

> {{ bio }}

## Stats
- Repositories: {{ public_repos }}
- Followers: {{ followers }}

{% if top_repo %}
## Project Highlight
**[{{ top_repo.name }}]({{ top_repo.url }})**  
⭐ {{ top_repo.stars }} | {{ top_repo.description }}
{% endif %}

{% if languages %}
## Languages
{% for lang, count in languages.items() %}
- {{ lang }} ({{ count }} repos)
{% endfor %}
{% endif %}

{% if socials %}
## Contact
{% for label, url in socials.items() %}
[{{ label }}]({{ url }})
{% endfor %}
{% endif %}
