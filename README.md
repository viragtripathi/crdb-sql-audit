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
git clone https://github.com/viragtripathi/crdb-sql-audit.git
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

## 🧹 Preparing Your Log Files

To analyze PostgreSQL SQL logs effectively, we recommend the following preprocessing steps:

### 1. Extract SQL-related Lines
```bash
grep "execute" xxxxx_full_pglog.log > sql_only.log
# or to include pg_ built-in function usage:
grep -E "execute|pg_" xxxxx_full_pglog.log > sql_only.log
```

### 2. Split Into Manageable Chunks (Optional but Recommended)
```bash
split -b 50M sql_only.log chunks/sql_chunk_
```

### 3. Run the Audit
```bash
crdb-sql-audit --dir chunks --terms execute,pg_ --out output/report
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
