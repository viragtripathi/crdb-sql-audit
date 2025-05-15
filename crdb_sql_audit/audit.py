import os
import re
import shutil
import importlib.resources as pkg_resources
import pandas as pd
import matplotlib.pyplot as plt

def extract_sql(logs_dir, search_terms):
    seen_sql = set()
    for filename in os.listdir(logs_dir):
        path = os.path.join(logs_dir, filename)
        if os.path.isfile(path):
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f:
                    if any(term in line for term in search_terms):
                        match = re.search(r'execute [^:]+: (.+)', line)
                        if match:
                            sql = match.group(1).strip()
                            seen_sql.add(sql)
                        else:
                            func_match = re.findall(r'\b(pg_\w+\s*\(.*?\))', line)
                            for func in func_match:
                                seen_sql.add(func.strip())
    return seen_sql

def analyze_compatibility(seen_sql):
    issues = []
    for sql in seen_sql:
        if re.search(r'\bpg_\w+\s*\(', sql):
            issues.append({
                "SQL_Type": "FUNCTION",
                "Issue": "PostgreSQL pg_* function not supported in CockroachDB",
                "Example": sql
            })
            continue

        stmt_type_match = re.match(r'^\b(SELECT|INSERT|UPDATE|DELETE|BEGIN|COMMIT|ROLLBACK|SAVEPOINT)\b', sql, re.IGNORECASE)
        if not stmt_type_match:
            continue
        sql_type = stmt_type_match.group(1).upper()
        issue = ""

        match = re.search(r'FROM\s+"?([\w#]+)"?', sql, re.IGNORECASE) or \
                re.search(r'INTO\s+"?([\w#]+)"?', sql, re.IGNORECASE) or \
                re.search(r'UPDATE\s+"?([\w#]+)"?', sql, re.IGNORECASE)

        if match and "#" in match.group(1):
            issue = "Table name contains unsupported special character (#)"
        elif sql_type in ["DELETE", "SELECT", "INSERT", "UPDATE"] and len(sql.split()) <= 2:
            issue = "Possibly malformed or incomplete SQL statement"

        if issue:
            issues.append({"SQL_Type": sql_type, "Issue": issue, "Example": sql})

    return issues

def generate_reports(seen_sql, issues, output_prefix):
    os.makedirs(os.path.dirname(output_prefix), exist_ok=True)

    with open(f"{output_prefix}.sql", "w", encoding="utf-8") as out:
        for sql in sorted(seen_sql):
            out.write(sql + "\n")

    pd.DataFrame(issues).to_csv(f"{output_prefix}.csv", index=False)
    summary = pd.DataFrame(issues).groupby(['SQL_Type', 'Issue']).size().reset_index(name='Count')

    # Copy logo to the output directory (only needed for HTML to find it)
    logo_src = str(pkg_resources.files("crdb_sql_audit").joinpath("roach-logo.svg"))
    logo_dst = os.path.join(os.path.dirname(output_prefix), "roach-logo.svg")
    shutil.copyfile(logo_src, logo_dst)

    # Markdown
    with open(f"{output_prefix}.md", "w", encoding="utf-8") as f:
        f.write("# CockroachDB SQL Compatibility Report\n\n")
        f.write(f"**Total unique SQL/function statements analyzed:** {len(seen_sql)}  \n")
        f.write(f"**Total compatibility issues detected:** {len(issues)}\n\n")
        f.write("## Compatibility Issues Summary\n\n")
        f.write("| SQL Type | Issue | Count |\n|----------|-------|-------|\n")
        for _, row in summary.iterrows():
            f.write(f"| {row['SQL_Type']} | {row['Issue']} | {row['Count']} |\n")
        f.write("\n## Sample Issues (first 10)\n")
        for i, row in enumerate(issues[:10]):
            f.write(f"### {i+1}. {row['SQL_Type']}: {row['Issue']}\n")
            f.write("```sql\n" + row['Example'] + "\n```\n\n")

    # HTML Report
    html_path = f"{output_prefix}.html"
    with open(html_path, "w", encoding="utf-8") as f:
        f.write("""
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<title>CockroachDB SQL Compatibility Report</title>
<link rel='stylesheet' href='https://cdn.datatables.net/1.13.6/css/jquery.dataTables.min.css'>
<script src='https://code.jquery.com/jquery-3.7.0.min.js'></script>
<script src='https://cdn.datatables.net/1.13.6/js/jquery.dataTables.min.js'></script>
<style>
body {
  font-family: "Inter", system-ui, sans-serif;
  background: #f8f9fb;
  color: #1e1e2f;
  margin: 20px;
}
header {
  display: flex;
  align-items: center;
  border-bottom: 2px solid #ccc;
  padding-bottom: 10px;
  margin-bottom: 20px;
}
header img {
  height: 40px;
  margin-right: 15px;
}
h1 {
  color: #3c2c90;
  font-size: 1.8em;
}
table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}
th {
  background-color: #eae6f8;
  color: #3c2c90;
  padding: 8px;
}
td {
  padding: 6px;
  border: 1px solid #ccc;
  font-size: 0.95em;
}
pre {
  background: #f1f3f7;
  padding: 10px;
  border-radius: 6px;
  border: 1px solid #ddd;
  overflow-x: auto;
}
</style>
</head>
<body>
<header>
  <img src="roach-logo.svg" alt="CockroachDB Logo">
  <h1>CockroachDB SQL Compatibility Report</h1>
</header>
""" +
                f"<p><strong>Total SQL/function statements:</strong> {len(seen_sql)}<br><strong>Total issues:</strong> {len(issues)}</p>"
                )
        f.write(summary.to_html(index=False))
        f.write("<h2>Sample Issues</h2>")
        for i, row in enumerate(issues[:10]):
            f.write(f"<h3>{i+1}. {row['SQL_Type']}: {row['Issue']}</h3><pre>{row['Example']}</pre>")
        f.write("<h2>All Compatibility Issues</h2><table id='issues' class='display'><thead><tr><th>SQL Type</th><th>Issue</th><th>Example</th></tr></thead><tbody>")
        for row in issues:
            f.write(f"<tr><td>{row['SQL_Type']}</td><td>{row['Issue']}</td><td><code>{row['Example']}</code></td></tr>")
        f.write("</tbody></table><script>$(document).ready(()=>$('#issues').DataTable());</script></body></html>")

    chart_data = summary.groupby("SQL_Type")['Count'].sum().sort_values(ascending=False)
    plt.figure(figsize=(10,6))
    chart_data.plot(kind='bar', color='#3c2c90')
    plt.title("CockroachDB Compatibility Issues by SQL Type")
    plt.ylabel("Issue Count")
    plt.xlabel("SQL Type")
    plt.tight_layout()
    plt.savefig(f"{output_prefix}_chart.png")
