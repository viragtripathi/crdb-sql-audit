# crdb-sql-audit

A powerful CLI tool to extract, deduplicate, and analyze PostgreSQL SQL logs for CockroachDB compatibility.

## 🚀 Features
- Extract SQL and function calls using customizable search terms (e.g. `execute`, `pg_`)
- Deduplicate repeated SQL statements from logs
- Analyze for common incompatibilities with CockroachDB:
  - Unsupported PostgreSQL functions (e.g. `pg_size_pretty()`)
  - Malformed SQL
  - Invalid characters in table names (e.g. `#`)
- Export full reports in multiple formats:
  - `.sql`: Deduplicated queries
  - `.csv`: Raw compatibility issue list
  - `.md`: Developer-friendly Markdown report
  - `.html`: Interactive browser report with sorting/filtering
  - `.png`: Visual bar chart of issues

## 📦 Installation

### Option A: Local Dev Install
```bash
git clone https://github.com/your-org/crdb-sql-audit.git
cd crdb-sql-audit
python -m venv venv
source venv/bin/activate
pip install .
```

### Option B: Build via `pyproject.toml`
```bash
python -m build
pip install dist/crdb_sql_audit-0.1.0-py3-none-any.whl
```

## 🧪 Usage
```bash
crdb-sql-audit \
  --dir /path/to/logs \
  --terms execute,pg_ \
  --out output/report
```

## 📁 Output
```
output/
├── report.sql          # Deduplicated SQL
├── report.csv          # Compatibility issues
├── report.md           # Markdown summary
├── report.html         # Interactive dashboard
├── report_chart.png    # Visual chart of issues
```

## 🛠 Example
Analyze all logs in a folder:
```bash
crdb-sql-audit --dir ./pg_logs --terms execute,pg_ --out audit_run
```

## 🧩 To Do
- Optional: export to PDF
- Optional: flag more PostgreSQL-specific features (e.g. CTEs, subqueries, RETURNING)

## 👥 Contributing
Pull requests and feature ideas are welcome. See `TODO.md` or open an issue.
