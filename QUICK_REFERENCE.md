# Subscripz-Buster Quick Reference

## 🚀 Quick Start

```bash
cd ~/Desktop/subscripz-buster
python3 scan_subscriptions_now.py
# Choose option 7 (Working Scanner)
```

## 📋 Most Useful Commands

### Find All Subscriptions
```bash
python3 working_scanner.py --days 365
```

### Get Complete Report
```bash
python3 comprehensive_scanner.py
```

### Export to Excel
```bash
python3 subscription_scanner_excel.py
```

### Find Duplicates
```bash
python3 duplicate_finder.py
```

### Quick Financial Summary
```bash
python3 financial_summary.py
```

## 🎯 Menu Options Cheat Sheet

| Option | Purpose | Best For |
|--------|---------|----------|
| **7** | Working Scanner ⭐ | Most users - reliable and fast |
| **8** | Comprehensive Report | See ALL subscriptions |
| **3** | Excel Export | Detailed analysis with charts |
| **11** | Duplicate Finder | Find services you're paying twice |
| **9** | Financial Summary | Quick cost overview |
| **5** | Debug Tools | If something's not working |

## 💡 Pro Tips

### Scan Different Time Periods
```bash
# Last 30 days
python3 working_scanner.py --days 30

# Last 2 years
python3 working_scanner.py --days 730

# Last 10 years
python3 working_scanner.py --days 3650
```

### Export Results
```bash
# Export to JSON
python3 working_scanner.py --days 365 --output-json my_subs.json

# Export without console output
python3 working_scanner.py --days 365 --output-json my_subs.json --quiet
```

### Preview Before Scanning
```bash
# See how many emails would be processed
python3 working_scanner.py --days 365 --dry-run
```

## 🔍 Troubleshooting

### No Subscriptions Found?
1. Try debug mode: Option 5 → b
2. Search by sender: Option 5 → c
3. Extend time range: `--days 3650`

### SQL Errors?
- Use Option 7 (Working Scanner) - it's the most compatible
- The adaptive system handles database variations automatically

### Slow Performance?
- Use `--dry-run` first to estimate
- Try Simple Scanner (Option 1) for quick checks
- Limit time range with `--days`

## 📊 Understanding Results

### Subscription Status
- **Active**: Recent activity, likely still charging
- **Inactive**: No emails for 6+ months (might still be charging!)
- **Cancelled**: Explicitly terminated
- **Trial**: Free trial period
- **Failed**: Payment issues

### Duplicate Detection
- **Exact Match**: Same service, different accounts
- **Fuzzy Match**: Netflix vs Netflix Inc.
- **Monthly Waste**: How much you'd save by consolidating

## 🛠️ Advanced Usage

### Automation Script
```bash
#!/bin/bash
# Monthly subscription audit
cd ~/Desktop/subscripz-buster
python3 comprehensive_scanner.py > monthly_report_$(date +%Y%m).txt
python3 export_to_csv.py
```

### JSON Processing
```python
import json
with open('results.json') as f:
    data = json.load(f)
print(f"Total monthly: ${data['financial_summary']['totals']['monthly_total']}")
```

## 🔒 Privacy Notes

- **100% Local**: No data leaves your computer
- **Read-Only**: Never modifies your emails
- **No Tracking**: No analytics or telemetry

## 📚 More Information

- Full documentation: `README.md`
- Technical details: `ADAPTIVE_SCANNING.md`
- Change history: `CHANGELOG.md`

---

*Quick tip: Start with Option 7, then try Option 8 for complete results!*
