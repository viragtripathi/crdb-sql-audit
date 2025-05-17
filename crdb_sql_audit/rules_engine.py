import logging
import os
import re
import yaml

def load_rules(rules_path=None):
    if rules_path:
        logging.info(f"📄 Loading rules from user-provided file: {rules_path}")
        with open(rules_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    # Fallback to built-in rule file inside package
    default_path = os.path.join(os.path.dirname(__file__), "rules", "postgres_to_crdb.yaml")
    logging.info(f"📦 Loading built-in default rules from: {default_path}")
    try:
        with open(default_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except Exception as e:
        logging.error(f"❌ Failed to load default rules: {e}")
        return []

def apply_rules(sql, rules):
    matched = []

    for rule in rules:
        try:
            pattern = re.compile(rule["match"], re.IGNORECASE)
        except re.error as e:
            logging.error(f"❌ Regex compile error in rule {rule.get('id', '?')}: {e}")
            continue

        if pattern.search(sql):
            logging.info(f"✅ MATCH: Rule {rule['id']} matched on SQL: {sql}")

            # Try to extract SQL type (optional fallback)
            stmt_type_match = re.match(
                r'^\s*(SELECT|INSERT|UPDATE|DELETE|UPSERT|WITH|BEGIN|COMMIT|ROLLBACK|SAVEPOINT|MERGE|CALL)',
                sql,
                re.IGNORECASE
            )
            sql_type = stmt_type_match.group(1).upper() if stmt_type_match else rule.get("type", "OTHER")

            matched.append({
                "Rule_ID": rule["id"],
                "SQL_Type": sql_type,
                "Issue": rule["message"],
                "Level": rule.get("level", "warning"),
                "Example": sql,
                "Tags": rule.get("tags", [])
            })

    return matched
