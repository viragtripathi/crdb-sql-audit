import argparse
import logging
import os
import sys
from crdb_sql_audit.audit import extract_sql, analyze_compatibility, generate_reports

__version__ = "0.2.6"

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
    parser.add_argument("--dir", help="Directory containing SQL log files")
    parser.add_argument("--file", help="Single SQL log file")
    parser.add_argument("--terms", default="execute,pg_", help="Comma-separated search keywords to extract SQL (default: 'execute,pg_')")
    parser.add_argument("--raw", action="store_true", help="Treat each matching line as raw SQL (skip extraction)")
    parser.add_argument("--out", default="crdb_audit_output/report", help="Output prefix for reports")
    parser.add_argument("--rules", required=False, help="Path to YAML rules file (defaults to Postgres rules)")
    args = parser.parse_args()

    if not args.dir and not args.file:
        parser.print_help()
        sys.exit(1)
    if args.dir and args.file:
        parser.error("Please provide only one of --dir or --file, not both")
    if args.dir and not os.path.isdir(args.dir):
        parser.error(f"--dir expects a directory. Got: {args.dir}")
    if args.file and not os.path.isfile(args.file):
        parser.error(f"--file expects a file. Got: {args.file}")

    search_terms = [t.strip() for t in args.terms.split(",")]
    logs_path = args.dir if args.dir else args.file
    seen_sql = extract_sql(logs_path, search_terms, raw_mode=args.raw)
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
