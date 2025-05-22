# {{ name }}

{{ bio }}

📂 {{ public_repos }} repos  
👥 {{ followers }} followers

{% if top_repo %}
**Top Repo:** [{{ top_repo.name }}]({{ top_repo.url }}) — ⭐ {{ top_repo.stars }}
{% endif %}

{% if socials %}
{% for label, url in socials.items() %}
[{{ label }}]({{ url }})
{% endfor %}
{% endif %}
