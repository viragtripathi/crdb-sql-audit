import argparse
import logging
from crdb_sql_audit.audit import extract_sql, analyze_compatibility, generate_reports

__version__ = "0.2.0"

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler("crdb_sql_audit.log", mode='w'),
        logging.StreamHandler()
    ]
)


def main():
    parser = argparse.ArgumentParser(
        description="🔍 Analyze SQL logs for CockroachDB compatibility.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    parser.add_argument("--dir", required=True, help="Directory with SQL log files")
    parser.add_argument("--terms", default="execute,pg_", help="Comma-separated search keywords to extract SQL (default: 'execute,pg_')")
    parser.add_argument("--out", default="crdb_audit_output/report", help="Output prefix for reports")
    parser.add_argument("--rules", required=False, help="Path to YAML rules file (defaults to Postgres rules)")
    args = parser.parse_args()

    search_terms = [t.strip() for t in args.terms.split(",")]
    seen_sql = extract_sql(args.dir, search_terms)
    issues = analyze_compatibility(seen_sql, rules_path=args.rules)
    if args.rules:
        logging.info(f"🔍 Using rule file: {args.rules}")
        with open(args.rules, "r") as f:
            logging.info("🔍 Rule file contents:")
            logging.info(f.read())
    else:
        logging.warning("📦 No rule file provided. Falling back to built-in postgres_to_crdb.yaml.")
    logging.info(f"🧪 Total SQL statements analyzed: {len(seen_sql)}")
    logging.info(f"🚨 Total issues found: {len(issues)}")
    if not issues:
        logging.info("🕵️ Showing 5 sample SQL statements that didn't match:")
        for sql in list(seen_sql)[:5]:
            logging.info(f"   ▶ {sql}")

    generate_reports(seen_sql, issues, args.out)

if __name__ == "__main__":
    main()