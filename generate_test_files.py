import csv
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

# WAF rules CSV
waf_rules_file = BASE_DIR / "waf_rules.csv"
with open(waf_rules_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "rule_name", "pattern", "action", "category"])
    writer.writerow([1, "Block SQL Injection", ".*select.*from.*", "block", "security"])
    writer.writerow([2, "Block XSS", "<script>.*", "block", "security"])
    writer.writerow([3, "Allow Login Page", "/login", "allow", "functionality"])

# Traffic CSV
traffic_file = BASE_DIR / "traffic.csv"
with open(traffic_file, mode="w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["id", "url", "method", "status_code"])
    writer.writerow([1, "/login", "POST", 200])
    writer.writerow([2, "/search?q=select+*+from", "GET", 403])
    writer.writerow([3, "/profile", "GET", 200])

print(f"Test files created at {waf_rules_file} and {traffic_file}")
