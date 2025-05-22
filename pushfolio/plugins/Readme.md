# 🧩 Pushfolio Plugin Guide

Drop `.py` files in this folder. Each plugin must define:

```python
def run(context) -> str:
    return "# My Markdown Output"
