import argparse
from crdb_sql_audit.audit import extract_sql, analyze_compatibility, generate_reports

def main():
    parser = argparse.ArgumentParser(description="Analyze SQL logs for CockroachDB compatibility.")
    parser.add_argument("--dir", required=True, help="Directory with SQL log files")
    parser.add_argument("--terms", required=True, help="Comma-separated search keywords (e.g. execute,pg_)")
    parser.add_argument("--out", default="crdb_audit_output/report", help="Output prefix for reports")
    args = parser.parse_args()

    search_terms = [t.strip() for t in args.terms.split(",")]
    seen_sql = extract_sql(args.dir, search_terms)
    issues = analyze_compatibility(seen_sql)
    generate_reports(seen_sql, issues, args.out)

if __name__ == "__main__":
    main()