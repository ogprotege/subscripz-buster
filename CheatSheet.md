# Subscripz-Buster Command Cheat Sheet

Quick reference for all commands, scanners, and utilities in the Subscripz-Buster toolkit.

## 🚀 Quick Start

### Interactive Menu (Easiest Way)
```bash
python scan_subscriptions_now.py
```
This launches an interactive menu with 17 different scanning options.

### Most Common Commands
```bash
# Basic scan for last year
python simple_scanner.py --days 365

# Comprehensive scan with fraud filtering
python secure_scanner.py --days 730

# Export to Excel with fraud filtering
python secure_excel_scanner.py --output my_subscriptions.xlsx

# Quick financial summary
python financial_summary.py
```

## 📋 Main Scanners

### 1. Simple Scanner (Most Stable)
**Purpose**: Basic subscription detection with minimal keywords to avoid SQL errors
```bash
python simple_scanner.py [OPTIONS]

Options:
  --days INT          Days to scan back (default: 365)
  --output-json PATH  Export results to JSON
  --quiet            Suppress console output
  --dry-run          Test mode without processing
  
Examples:
  python simple_scanner.py                    # Interactive mode
  python simple_scanner.py --days 730         # Scan 2 years
  python simple_scanner.py --dry-run          # Test run
  python simple_scanner.py --quiet --output-json results.json
```

### 2. Advanced Scanner (111 Keywords)
**Purpose**: Comprehensive scanning with extensive keyword list
```bash
python advanced_subscription_scanner.py [OPTIONS]

Options:
  --days INT          Days to scan back (default: 7300/20 years)
  --show-all         Show all results (not just top 25)
  --output-json PATH  Export results to JSON
  --quiet            Suppress console output
  --dry-run          Test mode
  
Examples:
  python advanced_subscription_scanner.py --days 365 --show-all
  python advanced_subscription_scanner.py --output-json full_scan.json
```

### 3. Secure Scanner (Fraud Filtering)
**Purpose**: Scans with integrated fraud/phishing detection
```bash
python secure_scanner.py [OPTIONS]

Options:
  --days INT     Days to scan back (default: 365)
  --limit INT    Number of results to display (default: 25)
  --output-json  Export results to JSON
  --quiet        Suppress console output
  --dry-run      Test mode
  
Examples:
  python secure_scanner.py --days 1825 --limit 50
  python secure_scanner.py --quiet --output-json secure_results.json
```

### 4. Comprehensive Scanner
**Purpose**: Shows ALL subscriptions with complete analysis
```bash
python comprehensive_scanner.py [OPTIONS]

Options:
  --days INT          Days to scan back (default: 1825/5 years)
  --output-json PATH  Export to JSON (auto-generated if not specified)
  --quiet            Suppress console output
  
Examples:
  python comprehensive_scanner.py --days 3650  # 10 years
  python comprehensive_scanner.py --output-json report.json
```

## 📊 Export Tools

### Excel Export with Fraud Filtering
```bash
python secure_excel_scanner.py [OPTIONS]

Options:
  --days INT      Days to scan back (default: 1825/5 years)
  --output PATH   Excel filename (auto-generated if not specified)
  
Examples:
  python secure_excel_scanner.py
  python secure_excel_scanner.py --days 365 --output yearly_subs.xlsx
```

### CSV Export
```bash
python export_to_csv.py
# No options - exports last 5 years to Desktop with timestamp
# Output: subscriptions_export_YYYYMMDD_HHMMSS.csv
```

## 💰 Analysis Tools

### Financial Summary
```bash
python financial_summary.py
# Shows spending analysis by company, year, and recent activity
# No command-line options
```

### Duplicate Finder
```bash
python duplicate_finder.py
# Finds services you're paying for multiple times
# Shows potential monthly/annual savings
# No command-line options
```

## 🧪 Debug & Utility Tools

### Database Utilities (in utils/ folder)
```bash
# Test database connection
python utils/test_mail_db.py

# Check database schema
python utils/check_exact_structure.py

# Check recipients table structure
python utils/check_recipients_structure.py
```

### Debug Scanner Options
```bash
python debug_scan.py              # Quick subscription check
python deep_investigate.py        # Deep email structure analysis
python scan_by_sender.py         # Analyze by sender domain
python investigate_structure.py   # Database structure investigation
```

## 🔧 Fixed/Specialized Scanners

### Working Scanner (Recommended)
```bash
python working_scanner.py
# Optimized version with better error handling
```

### Fixed Scanners (No Recipient Errors)
```bash
python fixed_working_scanner.py   # Fixed basic scanner
python fixed_advanced_scanner.py  # Fixed advanced scanner
# These avoid recipient table queries that can cause errors
```

## 🖥️ MCP Server

### Start MCP Server
```bash
python server.py
# Runs as Model Context Protocol server for integration
# Provides standardized JSON output for other tools
```

### Apple Mail Scanner (MCP Implementation)
```bash
python apple_mail_scanner.py
# Alternative MCP server implementation
# Specifically for Apple Mail integration
```

## 📝 Interactive Menu Options

When running `python scan_subscriptions_now.py`:

1. **Simple scan** - Basic scanning (prompts for years)
2. **Advanced scan** - Full 20-year scan with console output
3. **Excel export** - Full scan with Excel report
4. **Custom scan** - Specify custom time range
5. **Debug menu**:
   - a) Quick subscription check
   - b) Deep investigation
   - c) Scan by sender
   - d) Database structure
6. **Fixed scanner** - For normalized databases
7. **WORKING SCANNER** ⭐ - Recommended option
8. **Comprehensive Report** - Shows ALL subscriptions
9. **Financial Summary** - Quick spending analysis
10. **Export to CSV** - Simple CSV export
11. **Duplicate Finder** - Find duplicate services
12. **JSON Export Test** - Test JSON export functionality
13. **Test Dry-Run** - Test without processing emails
14. **Fixed Working Scanner** - No recipient errors
15. **Fixed Advanced Scanner** - Advanced with no errors
16. **SECURE Scanner** 🔒 - With fraud filtering
17. **SECURE Excel Scanner** 🔒📊 - Fraud filter + Excel

## 🎯 Common Use Cases

### "I want to see all my subscriptions quickly"
```bash
python scan_subscriptions_now.py
# Choose option 7 (WORKING SCANNER)
```

### "I want a clean Excel report without spam"
```bash
python secure_excel_scanner.py
```

### "I want to find duplicate subscriptions"
```bash
python duplicate_finder.py
```

### "I want to see how much I'm spending"
```bash
python financial_summary.py
```

### "I want to export everything to analyze elsewhere"
```bash
python comprehensive_scanner.py --output-json full_export.json
# OR
python export_to_csv.py
```

### "I want to test without processing emails"
```bash
python advanced_subscription_scanner.py --dry-run
```

### "I'm getting SQL errors"
```bash
# Use the simple scanner with fewer keywords
python simple_scanner.py --days 365
# OR use fixed scanners
python fixed_working_scanner.py
```

## 📊 Output Formats

### JSON Export Structure
All scanners that support `--output-json` produce standardized JSON with:
- Scan metadata (date, duration, parameters)
- Subscriptions with full details
- Financial summary
- Duplicate analysis

### Excel Export Sheets
Excel exports include:
1. **Summary Dashboard** - Key metrics and financials
2. **All Subscriptions** - Detailed list with amounts
3. **Duplicate Analysis** - Services on multiple accounts
4. **By Account** - Breakdown by email account
5. **Timeline Analysis** - Activity timeline

### CSV Export Columns
- Date, Sender, Subject, Amount, Your Email Account

## 🚨 Troubleshooting

### SQL Expression Too Complex
Use scanners with fewer keywords:
- `simple_scanner.py` (most stable)
- `fixed_working_scanner.py`
- `fixed_advanced_scanner.py`

### No Results Found
- Increase the `--days` parameter
- Check database connectivity with `python utils/test_mail_db.py`
- Try `python debug_scan.py` for quick check

### Permission Errors
- Ensure Terminal has Full Disk Access in macOS settings
- Run from user account that owns the Mail data

## 💡 Pro Tips

1. **Start with the interactive menu** (`scan_subscriptions_now.py`) to explore options
2. **Use secure scanners** to filter out phishing/spam automatically
3. **Export to JSON** for programmatic analysis or integration
4. **Run financial_summary.py** monthly to track spending trends
5. **Check for duplicates** quarterly to avoid waste
6. **Use dry-run mode** to test before processing large date ranges
7. **Fixed scanners** are more reliable but might miss some emails

## 🔍 Keyword Detection

Scanners use different keyword sets:
- **Simple Scanner**: ~20 basic keywords
- **Advanced Scanner**: 66-111 comprehensive keywords
- **Secure Scanner**: Same as advanced + fraud filtering

Common detected keywords:
- Payment: invoice, billing, receipt, charge, payment
- Subscription: subscription, membership, renewal, recurring
- Status: cancelled, failed, expired, active, trial
- Frequency: monthly, annual, yearly, weekly

## 📅 Time Ranges

Default scan periods:
- Simple Scanner: 1 year (365 days)
- Advanced Scanner: 20 years (7300 days)
- Comprehensive Scanner: 5 years (1825 days)
- Secure Scanner: 1 year (365 days)
- Financial tools: 5 years (1825 days)

Maximum recommended: 20 years (email data may not go back further)