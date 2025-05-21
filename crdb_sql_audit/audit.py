import os
import re
import shutil
import logging
import gzip
import lzma
import importlib.resources as pkg_resources
import pandas as pd
import matplotlib.pyplot as plt

from .rules_engine import load_rules, apply_rules
from collections import Counter


def open_log_file(path):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="ignore")
    elif path.endswith(".xz"):
        return lzma.open(path, "rt", encoding="utf-8", errors="ignore")
    else:
        return open(path, "r", encoding="utf-8", errors="ignore")


def extract_sql(logs_path, line_filters=None, raw_mode=False):
    if line_filters is None:
        line_filters = ["LOG:  execute", "pg_", "LOG:  statement:"]
        logging.info("🔍 No line filters provided. Using default: ['LOG:  execute', 'pg_', 'LOG:  statement:']")
    else:
        logging.info(f"🔍 Line filters used: {line_filters}")

    seen_sql = set()
    structured_hits = 0
    raw_hits = 0

    if os.path.isfile(logs_path):
        paths = [logs_path]
    elif os.path.isdir(logs_path):
        paths = [os.path.join(logs_path, f) for f in os.listdir(logs_path)]
    else:
        raise ValueError(f"The path '{logs_path}' is not a valid file or directory.")

    for path in paths:
        if os.path.isfile(path):
            with open_log_file(path) as f:
                for line in f:
                    if any(term in line for term in line_filters):
                        logging.debug(f"🧲 Line matched filter: {line.strip()}")
                        sql = extract_raw_sql(line) if raw_mode else extract_structured_sql(line, line_filters=line_filters)
                        if sql:
                            seen_sql.add(sql)
                            if raw_mode:
                                raw_hits += 1
                            else:
                                structured_hits += 1
    logging.info(f"✅ Total SQL statements extracted: {len(seen_sql)}")
    logging.info(f"📊 Raw mode matches: {raw_hits}")
    logging.info(f"📊 Structured matches: {structured_hits}")

    sql_type_counts = Counter(issue['SQL_Type'] for issue in analyze_compatibility(seen_sql))
    for sql_type, count in sql_type_counts.items():
        logging.info(f"📈 SQL Type: {sql_type} — {count} matches")

    sql_type_counts = Counter(issue['SQL_Type'] for issue in analyze_compatibility(seen_sql))
    for sql_type, count in sql_type_counts.items():
        logging.info(f"📈 SQL Type: {sql_type} — {count} matches")

    return seen_sql


def extract_raw_sql(line):
    logging.debug(f"📝 Checking raw line: {line.strip()}")
    sql = line.strip()
    return sql if len(sql) > 5 else None


def extract_structured_sql(line, line_filters=None):
    logging.debug(f"🔍 Checking structured line: {line.strip()}")

    # If user provided custom filters, use those to extract SQL
    if line_filters:
        for filter_term in line_filters:
            if filter_term in line:
                sql = line.split(filter_term, 1)[-1].strip()
                logging.debug(f"📤 Extracted via user filter '{filter_term}': {sql}")
                return sql

    # Fallback to default patterns
    match = re.search(r'execute [^:]+: (.+)', line)
    if not match:
        match = re.search(r'LOG:\s*statement:\s*(.+)', line)
    if match:
        return match.group(1).strip()

    # Fallback for pg_ built-ins
    func_match = re.findall(r'\b(pg_\w+\s*\(.*?\))', line)
    if func_match:
        logging.debug(f"✅ Matched pg_ function: {func_match[0].strip()}")
        return func_match[0].strip()

    return None


def analyze_compatibility(seen_sql, rules_path=None):
    rules = load_rules(rules_path)
    logging.info(f"📊 Loaded {len(rules)} rules")

    all_issues = []
    for sql in seen_sql:
        matches = apply_rules(sql, rules)
        if matches:
            logging.info(f"⚠️ MATCHED: {sql}")
            for m in matches:
                logging.info(f"   🔸 Rule: {m['Rule_ID']} — {m['Issue']}")
        all_issues.extend(matches)

    return all_issues


def generate_reports(seen_sql, issues, output_prefix):
    os.makedirs(os.path.dirname(output_prefix), exist_ok=True)

    with open(f"{output_prefix}.sql", "w", encoding="utf-8") as out:
        for sql in sorted(seen_sql):
            out.write(sql + "\n")

    df = pd.DataFrame(issues)

    # Rule-level summary
    rule_summary = df.groupby("Rule_ID").size().reset_index(name="Matches")
    rule_summary["% of Total"] = (rule_summary["Matches"] / len(seen_sql)) * 100

    if df.empty or not {'SQL_Type', 'Issue'}.issubset(df.columns):
        logging.warning("⚠️ No compatibility issues found or rules failed to match.")
        return

    pd.DataFrame(issues).to_csv(f"{output_prefix}.csv", index=False)
    summary = pd.DataFrame(issues).groupby(['SQL_Type', 'Issue']).size().reset_index(name='Count')

    # Copy logo to the output directory (only needed for HTML to find it)
    logo_src = str(pkg_resources.files("crdb_sql_audit").joinpath("roach-logo.svg"))
    logo_dst = os.path.join(os.path.dirname(output_prefix), "roach-logo.svg")
    shutil.copyfile(logo_src, logo_dst)

    # Markdown
    issue_pct = (len(issues) / len(seen_sql)) * 100 if seen_sql else 0
    with open(f"{output_prefix}.md", "w", encoding="utf-8") as f:
        f.write("# CockroachDB SQL Compatibility Report\n\n")
        f.write(f"**Total unique SQL/function statements analyzed:** {len(seen_sql)}  \n")
        f.write(f"**Total compatibility issues detected:** {len(issues)}\n")
        f.write(f"**Issue rate:** {issue_pct:.2f}%\n\n")
        f.write("## Rule Match Summary\n\n")
        f.write("| Rule ID | Matches | % of Total |\n|---------|---------|-------------|\n")
        for _, row in rule_summary.iterrows():
            f.write(f"| {row['Rule_ID']} | {row['Matches']} | {row['% of Total']:.2f}% |\n")
        f.write("\n## Compatibility Issues Summary\n\n")
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
                f"<p><strong>Total SQL/function statements:</strong> {len(seen_sql)}<br><strong>Total issues:</strong> {len(issues)}<br><strong>Issue rate:</strong> {issue_pct:.2f}%</p>"
                )
        f.write(summary.to_html(index=False))
        f.write("<h2>Rule Match Summary</h2>")
        f.write(rule_summary.to_html(index=False))
        f.write("<h2>Sample Issues</h2>")
        for i, row in enumerate(issues[:10]):
            f.write(f"<h3>{i+1}. {row['SQL_Type']}: {row['Issue']}</h3><pre>{row['Example']}</pre>")
        f.write("<h2>All Compatibility Issues</h2><table id='issues' class='display'><thead><tr><th>SQL Type</th><th>Issue</th><th>Example</th></tr></thead><tbody>")
        for row in issues[:5000]:
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
