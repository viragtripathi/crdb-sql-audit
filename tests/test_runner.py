import os
import subprocess

def run_test():
    print("🧪 Running crdb-sql-audit on test logs...")
    test_output = "tests/output/test_report"
    os.makedirs("tests/output", exist_ok=True)

    subprocess.run([
        "crdb-sql-audit",
        "--dir", "tests/sample_logs",
        "--filters", "execute,pg_",
        "--rules", "tests/rules/test_rules.yaml",
        "--out", test_output
    ], check=True)

    if os.path.exists(test_output + ".csv"):
        print("✅ CSV report generated successfully")
    else:
        print("❌ CSV report not found")

if __name__ == "__main__":
    run_test()
