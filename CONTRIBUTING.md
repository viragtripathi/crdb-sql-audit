# Contributing to crdb-sql-audit

Thanks for your interest in improving this project! You can contribute by:

## ✅ Adding New Rules

- All rules are defined in YAML inside the `rules/` folder.
- Each rule must include:

```yaml
- id: rule_name
  match: 'regex_here'
  message: "Short explanation"
  level: [error|warning|info]
  tags: [list, of, tags]
````

You can test them using [regex101.com](https://regex101.com/?flavor=python) or in Python:

```python
import re
pattern = re.compile(r'^DELETE FROM\s*$', re.IGNORECASE)
print(bool(pattern.search("DELETE FROM")))
```

Submit your rule set via pull request or open an issue for discussion.

## 🧪 Running Locally

```bash
python -m venv venv
source venv/bin/activate
pip install .
crdb-sql-audit --help
```

## 🧼 Code Style

* Follows [PEP8](https://peps.python.org/pep-0008/)
* Run `flake8` before committing

