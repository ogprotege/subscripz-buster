# Subscripz-Buster v2.3.0

A comprehensive subscription detection and analysis system for Apple Mail that uncovers ALL your recurring charges, finds duplicate subscriptions, and helps you save money by identifying services you're paying for across multiple accounts or no longer using.

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Menu System - All 17 Options](#menu-system---all-17-options)
6. [Complete Script Documentation](#complete-script-documentation)
7. [MCP Server Integration](#mcp-server-integration)
8. [Technical Architecture](#technical-architecture)
9. [Adaptive Database Scanning](#adaptive-database-scanning)
10. [JSON Output and Data Interchange](#json-output-and-data-interchange)
11. [Troubleshooting Guide](#troubleshooting-guide)
12. [Performance and Optimization](#performance-and-optimization)
13. [Privacy and Security](#privacy-and-security)
14. [Advanced Usage](#advanced-usage)
15. [Development](#development)

## Overview

Subscripz-Buster is a powerful email analysis tool that scans your Apple Mail database to identify all subscription services, recurring payments, and membership charges. It uses advanced pattern recognition, adaptive database scanning, and intelligent categorization to find subscriptions you might have forgotten about or are paying for multiple times.

### What's New in v2.3.0 (June 2025)

- **🛡️ Enhanced Fraud Detection**: Now with 1000+ blacklisted domains, DNS validation, and typosquatting detection
- **📊 Proximity-Based Payment Detection**: Finds "$9.99/month" patterns near dollar amounts for better accuracy
- **📧 Sender Email in Excel**: Critical new column shows exact sender addresses for easy subscription management
- **💡 Smarter Financial Calculations**: High-value unknowns ($200+) tracked separately to avoid inflating monthly costs
- **🏢 Better Company Names**: "amazonses" → "Amazon", proper capitalization for 500+ services
- **📋 Billing Details Tracking**: New field stores text that determined frequency for transparency
- **🔍 Improved Frequency Detection**: Handles "annual plan, billed monthly" and other complex patterns

- **Adaptive Database Scanning**: Automatically detects and adapts to different Apple Mail database structures (V8, V9, V10+)
- **Comprehensive Detection**: Uses 100+ keywords and patterns to find ALL subscriptions
- **Advanced Fraud Detection**: Multi-layered protection against phishing and spam subscriptions
- **Enhanced Payment Extraction**: 40+ regex patterns for accurate amount detection across multiple currencies
- **Duplicate Detection**: Finds services you're paying for on multiple email accounts
- **Financial Analysis**: Calculates total monthly/annual costs and potential savings
- **Zero Configuration**: Works out of the box with any Apple Mail setup
- **100% Local**: All processing happens on your machine - no data leaves your computer
- **MCP Integration**: Natural language interface through Claude Desktop

## Key Features

### Core Capabilities

1. **Universal Apple Mail Compatibility**
   - Works with Apple Mail V8 (legacy structure)
   - Works with Apple Mail V9 (transitional)
   - Works with Apple Mail V10+ (normalized databases)
   - Automatically detects database version and adapts queries

2. **Advanced Detection Engine**
   - 100+ subscription-related keywords
   - Multi-language pattern matching
   - Payment amount extraction in multiple currencies
   - Frequency detection (monthly, annual, weekly, etc.)
   - Status tracking (active, cancelled, trial, failed)

3. **Enhanced Analysis**
   - Intelligent duplicate detection with fuzzy matching
   - Financial waste calculation with monthly equivalent conversions
   - Activity timeline analysis
   - Payment failure identification
   - High-value unknown frequency tracking (NEW)

4. **Advanced Fraud Protection** (Enhanced in v2.3.0)
   - Domain reputation checking against 1000+ blacklisted domains
   - DNS validation and MX record checking
   - Typosquatting detection (e.g., "mircosoft" → fraud)
   - Suspicious amount validation (filters out $100+/day scams)
   - Whitelist verification for 500+ legitimate services
   - Pattern matching to identify phishing emails
   - Automatic filtering of fraudulent subscriptions
   - Detailed fraud reporting and statistics

5. **Multiple Output Formats**
   - Console reports with color coding  
   - Excel workbooks with sender email column (NEW)
   - JSON export with billing details tracking
   - CSV export for custom analysis
   - MCP integration for natural language queries

## Installation

### Prerequisites

- macOS with Apple Mail configured
- Python 3.8 or later
- Claude Desktop (for MCP integration)

### Step 1: Clone or Download

```bash
cd ~/Desktop
git clone [repository-url] subscripz-buster
cd subscripz-buster
```

### Step 2: Set Up Virtual Environment

```bash
# Create virtual environment
python3 -m venv .venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

Or use the automated setup script:

```bash
chmod +x setup.sh
./setup.sh
```

### Step 3: Configure MCP Server (Optional)

For Claude Desktop integration, add to your Claude Desktop config:

```json
{
  "mcpServers": {
    "subscripz-buster": {
      "command": "/Users/YOUR_USERNAME/Desktop/subscripz-buster/.venv/bin/python",
      "args": ["/Users/YOUR_USERNAME/Desktop/subscripz-buster/server.py"],
      "env": {}
    }
  }
}
```

Replace `YOUR_USERNAME` with your actual Mac username.

## Quick Start

### Option 1: Use the Menu System

```bash
cd ~/Desktop/subscripz-buster
python3 scan_subscriptions_now.py
```

### Option 2: Direct Scanner Usage

```bash
# Quick scan with the most reliable scanner
python3 working_scanner.py

# Comprehensive scan with all features
python3 comprehensive_scanner.py

# Advanced scan with spam filtering
python3 advanced_subscription_scanner.py

# 🔒 NEW: Secure scan with fraud detection
python3 secure_scanner.py

# 🔒 NEW: Secure scan with Excel export
python3 secure_excel_scanner.py

# Export to Excel (without fraud filtering)
python3 excel_export_fixed.py
```

### Option 3: Use with Claude Desktop

After MCP setup, simply ask Claude:
- "Use subscripz-buster to scan all my subscriptions"
- "Find duplicate subscriptions across my accounts"
- "Show me subscriptions I haven't used in 6 months"
- "Export my subscription analysis to Excel"

## Menu System - All 17 Options

The main launcher (`scan_subscriptions_now.py`) provides a comprehensive menu with 17 options:

### Option 1: Simple Scan (Basic Keywords)
**Script**: `simple_scanner.py`
**Purpose**: Quick scan using 15 core subscription keywords
**Features**:
- Fastest scan option
- Most stable with large databases
- Basic duplicate detection
- Essential subscription identification
**Output**: Console report with top subscriptions
**Best For**: First-time users, quick checks, testing setup

### Option 2: Advanced Scan (Comprehensive)
**Script**: `advanced_subscription_scanner.py`
**Purpose**: Deep scan with 100+ keywords and spam filtering
**Features**:
- Comprehensive keyword matching
- Advanced spam filtering
- Payment amount extraction
- Frequency detection
- Status categorization
**Output**: Detailed console report with financial analysis
**Best For**: Thorough analysis, finding hidden subscriptions

### Option 3: Excel Export (Full Report)
**Script**: `subscription_scanner_excel.py`
**Purpose**: Generate comprehensive Excel workbook
**Features**:
- 6 analysis sheets
- Summary dashboard
- Duplicate analysis
- Account breakdown
- Payment issues tracking
- Timeline analysis
**Output**: Excel file on Desktop
**Best For**: Detailed analysis, record keeping, sharing results

### Option 4: Custom Time Range
**Script**: Variable (uses selected scanner)
**Purpose**: Scan specific time period
**Features**:
- User-defined date range
- Flexible scanning period
- All features of selected scanner
**Output**: Depends on scanner choice
**Best For**: Recent subscription checks, historical analysis

### Option 5: Debug Tools
**Script**: Multiple debug utilities
**Sub-options**:
- a) Check database structure
- b) Test email search
- c) Search by specific sender
- d) View raw email data
**Purpose**: Troubleshooting and investigation
**Best For**: Resolving issues, understanding data

### Option 6: Fixed Scanner (Normalized DBs)
**Script**: `fixed_scanner.py`
**Purpose**: Specifically for Apple Mail V10+ normalized databases
**Features**:
- Handles subjects in separate table
- Optimized for newer Mail versions
- Enhanced Unicode support
**Output**: Console report
**Best For**: macOS Big Sur and later

### Option 7: Working Scanner ⭐ (Recommended)
**Script**: `working_scanner.py`
**Purpose**: Most reliable scanner with adaptive capabilities
**Features**:
- Dynamic schema detection
- Robust recipient fetching
- Graceful error handling
- JSON export support
- Comprehensive logging
**Output**: Console report + optional JSON
**Best For**: Most users - best balance of features and reliability

### Option 8: Comprehensive Scanner (Show All)
**Script**: `comprehensive_scanner.py`
**Purpose**: Show EVERY subscription found
**Features**:
- No filtering or limits
- Complete results
- Automatic JSON export
- Detailed categorization
**Output**: Full report + JSON file
**Best For**: Complete subscription inventory

### Option 9: Financial Summary
**Script**: `financial_summary.py`
**Purpose**: Quick cost overview
**Features**:
- Total monthly/annual costs
- Cost by category
- Savings opportunities
- Duplicate waste calculation
**Output**: Financial report
**Best For**: Budget analysis, cost tracking

### Option 10: CSV Export
**Script**: `export_to_csv.py`
**Purpose**: Export for spreadsheet analysis
**Features**:
- Simple CSV format
- All subscription data
- Import to Excel/Google Sheets
**Output**: CSV file on Desktop
**Best For**: Custom analysis, data manipulation

### Option 11: Find Duplicates
**Script**: `duplicate_finder.py`
**Purpose**: Focus on duplicate subscriptions
**Features**:
- Cross-account detection
- Fuzzy name matching
- Waste calculation
- Consolidation recommendations
**Output**: Duplicate report with savings
**Best For**: Cost reduction, account cleanup

### Option 12: JSON Export Test
**Script**: `test_json_export.py`
**Purpose**: Test JSON functionality across all scanners
**Features**:
- Validates JSON output
- Tests data consistency
- Checks all scanners
**Output**: Test results and sample JSON
**Best For**: Development, testing, automation

### Option 13: Dry Run Test
**Script**: `test_dry_run.py`
**Purpose**: Preview scan scope without processing
**Features**:
- Shows email count
- Estimates processing time
- No actual scanning
- Database statistics
**Output**: Scan preview statistics
**Best For**: Planning, performance estimation

### Option 14: Ultra Simple Scan
**Script**: `ultra_simple_scan.py`
**Purpose**: Minimal scanner for quick testing
**Features**:
- Bare minimum functionality
- 5 core keywords only
- Fastest possible scan
- Basic output
**Output**: Simple list of subscriptions
**Best For**: Testing setup, minimal resource usage

### Option 15: Deep Investigation
**Script**: `deep_investigate.py`
**Purpose**: In-depth analysis of specific subscriptions
**Features**:
- Detailed email analysis
- Pattern investigation
- Historical tracking
- Forensic examination
**Output**: Detailed investigation report
**Best For**: Investigating specific issues or subscriptions

### Option 16: 🔒 Secure Scanner (Anti-Fraud) ⭐ NEW
**Script**: `secure_scanner.py`
**Purpose**: Scan with advanced fraud detection to filter out phishing/scam emails
**Features**:
- Domain reputation checking
- Blacklist verification
- Suspicious amount validation (>$100/day filtered)
- Whitelist of 500+ legitimate services
- Pattern matching for fraud indicators
- Automatic filtering of phishing attempts
**Output**: Clean results with fraud statistics
**Best For**: Getting accurate subscription list without spam/phishing

### Option 17: 🔒📊 Secure Excel Scanner ⭐ NEW
**Script**: `secure_excel_scanner.py`
**Purpose**: Fraud-filtered scan with direct Excel export
**Features**:
- All fraud detection from Option 16
- Direct Excel export integration
- Clean financial calculations
- Professional report generation
- No manual steps required
**Output**: Excel file with only legitimate subscriptions
**Best For**: One-click fraud-filtered Excel reports

## Complete Script Documentation

### Core Scanners

#### `working_scanner.py` ⭐
The most reliable scanner with adaptive database capabilities. Features:
- Dynamic schema discovery using PRAGMA table_info
- Intelligent column name detection
- Robust recipient fetching with fallback
- Batch processing for large datasets
- Comprehensive error handling
- JSON export with `--output-json` flag
- Dry run support with `--dry-run` flag

#### `advanced_subscription_scanner.py`
Comprehensive scanner with advanced features:
- 100+ keyword patterns
- Spam filtering
- Payment method detection
- Enhanced amount extraction
- Multi-currency support
- Frequency analysis
- Status categorization

#### `comprehensive_scanner.py`
Shows all subscriptions without filtering:
- Complete results
- Automatic JSON export
- No limits on display
- Full data preservation

#### `simple_scanner.py`
Lightweight scanner for quick checks:
- 15 core keywords only
- Fast execution
- Basic features
- Stable operation

#### `fixed_scanner.py`
Specialized for normalized databases:
- Handles separate subjects table
- Optimized queries
- Unicode support

### Utility Scripts

#### `duplicate_finder.py`
Dedicated duplicate detection:
- Cross-account analysis
- Fuzzy matching algorithm
- Waste calculation
- Recommendations

#### `financial_summary.py`
Financial analysis tool:
- Cost breakdowns
- Category analysis
- Trend identification
- Savings opportunities

#### `export_to_csv.py`
CSV export utility:
- Simple format
- All data included
- Spreadsheet compatible

#### `excel_export_fixed.py`
Enhanced Excel exporter:
- Multiple analysis sheets
- Charts and formatting
- Professional reports

### Debug and Testing Scripts

#### `check_schema.py`
Database structure analyzer:
- Table detection
- Column inspection
- Version identification

#### `check_exact_structure.py`
Detailed schema examination:
- Complete table listings
- Column types
- Relationship mapping

#### `check_recipients_structure.py`
Recipient table analyzer:
- Column discovery
- Type detection
- Join requirements

#### `investigate_structure.py`
Interactive database explorer:
- Query testing
- Data sampling
- Structure validation

#### `debug_scan.py`
Scanner debugging tool:
- Verbose logging
- Step-by-step execution
- Error identification

#### `test_setup.py`
Installation validator:
- Dependency checking
- Database access
- Configuration validation

#### `test_working_query.py`
Query tester:
- SQL validation
- Performance testing
- Result verification

#### `test_mail_db.py`
Database connection tester:
- Access validation
- Permission checking
- Path verification

#### `test_scanner_debug.py`
Scanner operation debugger:
- Execution tracing
- Error catching
- Performance profiling

#### `test_enhanced_features.py`
Feature validation:
- Adaptive scanning test
- Recipient fetching test
- JSON export test

#### `test_json_export.py`
JSON functionality tester:
- Format validation
- Data consistency
- Scanner compatibility

#### `test_dry_run.py`
Dry run feature tester:
- Preview functionality
- Count accuracy
- Performance estimation

### Support Scripts

### Payment Extraction (Enhanced in v2.3.0)

`enhanced_payment_extractor.py` provides sophisticated payment detection:

- **Proximity-Based Detection**: Finds frequency patterns near dollar amounts ("$9.99/month")
- **Multi-Currency Support**: USD, EUR, GBP, CAD, AUD, INR, JPY with proper symbols
- **Context-Aware Extraction**: Handles "annual plan, billed monthly" complexity
- **Frequency Standardization**: Converts variations to standard terms
- **Amount Validation**: Filters years (2024) and ZIP codes from amounts
- **Payment Context**: Extracts refunds, failures, trials, payment methods
- **Monthly Equivalents**: Converts all frequencies to monthly for comparison

### Data Structures (Enhanced in v2.3.0)

`common_structures.py` provides enhanced data models:

- **Subscription Class Updates**:
  - `billing_period_details`: Stores raw text that determined frequency
  - `metadata`: Flexible dict for full sender info and detection details
  - Improved `to_dict()` serialization
- **Financial Calculations**:
  - High-value unknowns ($200+) tracked separately
  - Proper monthly equivalents for all frequencies
  - Quarterly and semi-annual support added
- **Export Enhancements**:
  - All data structures support new fields
  - JSON output includes billing details
  - Better handling of ambiguous frequencies

#### `apple_mail_scanner.py`
Core database interface:
- Database detection
- Query execution
- Result processing

#### `server.py`
MCP server implementation:
- Natural language interface
- Tool registration
- Request handling
- Response formatting

#### `scan_subscriptions_now.py`
Main menu launcher:
- User interface
- Scanner selection
- Option handling
- Process management

#### `setup.sh`
Automated installation:
- Virtual environment setup
- Dependency installation
- Configuration assistance

#### `example_json_usage.py`
JSON usage examples:
- Loading scan results
- Data manipulation
- Analysis examples

### Archive and Old Versions

#### `scan_subscriptions.py`
Original scanner prototype

#### `scan_and_save.py`
Early version with file output

#### `scan_by_sender.py`
Sender-focused analysis tool

#### `deep_investigate.py`
Deep analysis prototype

#### `ultra_simple_scan.py`
Minimal scanner for testing

### Fraud Detection Scripts (Enhanced in v2.3.0)

#### `enhanced_fraud_detector.py` ⭐ NEW
Comprehensive fraud detection system with major improvements:
- **1000+ Blacklisted Domains**: Expanded from ~200 to over 1000 entries
- **DNS Validation**: Checks if domains actually exist and have MX records
- **Typosquatting Detection**: Catches "mircosoft", "amaz0n", "app1e" etc.
- **500+ Legitimate Services**: Properly maps "amazonses" → "Amazon"
- **Enhanced Company Name Extraction**: Better handling of subdomains and display names
- **Sender Details Extraction**: Full email parsing with display name support
- **Monthly Equivalent Calculation**: Converts any frequency to monthly for accurate totals
- **Intelligent Fraud Scoring**: Multi-factor analysis with weighted scoring
- **Fraud Report Generation**: Detailed statistics on detected fraud patterns

#### `secure_scanner.py` ⭐ NEW
Fraud-filtered subscription scanner:
- Integrates fraud_detector.py
- Filters out phishing emails before processing
- Shows fraud filtering statistics
- Clean subscription results
- JSON export support

#### `secure_excel_scanner.py` ⭐ NEW
Combines fraud filtering with Excel export:
- One-click secure Excel reports
- Fraud filtering + Excel generation
- Clean financial calculations
- Professional output
- Auto-generated filenames

## MCP Server Integration

The MCP (Model Context Protocol) server enables natural language interaction through Claude Desktop.

### Available MCP Tools

1. **scan_all_subscriptions**
   - Basic scan of last year
   - Quick overview
   - Essential results

2. **comprehensive_scan**
   - 5-year deep scan
   - Detailed categorization
   - Complete analysis

3. **advanced_scan**
   - 20-year scan
   - Spam filtering
   - Maximum detection

4. **find_duplicate_subscriptions**
   - Cross-account search
   - Waste calculation
   - Consolidation advice

5. **financial_summary**
   - Cost overview
   - Budget analysis
   - Savings opportunities

6. **export_to_excel**
   - Full Excel report
   - Multiple sheets
   - Professional output

7. **find_inactive_subscriptions**
   - Forgotten services
   - Activity analysis
   - Cancellation candidates

8. **analyze_spending_by_category**
   - Category breakdown
   - Spending patterns
   - Budget insights

9. **search_subscription**
   - Specific company lookup
   - Detailed information
   - Email history

### Natural Language Examples

- "Scan all my subscriptions from the last 2 years"
- "Find subscriptions I'm paying for twice"
- "Show me subscriptions I haven't used in 6 months"
- "How much am I spending on streaming services?"
- "Export a detailed report of all my subscriptions"
- "Search for my Netflix subscription details"
- 🆕 "Use a secure scan to filter out phishing emails"
- 🆕 "Show me only legitimate subscriptions without spam"
- 🆕 "Create a fraud-filtered Excel report of my subscriptions"

## Technical Architecture

### Database Handling

Subscripz-Buster uses sophisticated database detection and query adaptation:

1. **Version Detection**
   ```python
   # Automatic version detection
   V10: ~/Library/Mail/V10/MailData/Envelope Index
   V9:  ~/Library/Mail/V9/MailData/Envelope Index
   V8:  ~/Library/Mail/V8/MailData/Envelope Index
   ```

2. **Schema Detection**
   ```sql
   -- Check for normalized database
   SELECT sql FROM sqlite_master WHERE name='subjects'
   
   -- Discover table structure
   PRAGMA table_info(recipients)
   ```

3. **Query Adaptation**
   - Normalized: Joins with subjects table
   - Legacy: Direct subject access
   - Recipient handling: Dynamic based on structure

### Keyword System

The detection engine uses multiple keyword categories:

1. **Payment Keywords** (30+)
   - invoice, billing, payment, charge, receipt
   - transaction, purchase, checkout, order
   - payment received/confirmed/processed/failed

2. **Subscription Keywords** (25+)
   - subscription, membership, premium, plan
   - recurring, auto-renew, renewal, monthly
   - annual, trial, service, account

3. **Status Keywords** (20+)
   - active, cancelled, expired, suspended
   - failed, declined, trial, paused
   - terminated, ended, stopped

4. **Company Keywords** (50+)
   - Major services: Netflix, Spotify, Apple, Amazon
   - Software: Adobe, Microsoft, Dropbox
   - Platforms: Google, Facebook, LinkedIn
   - Many more...

### Data Processing Pipeline

1. **Email Fetching**
   - SQL query construction
   - Batch processing (500 emails/batch)
   - Memory-efficient streaming

2. **Information Extraction**
   - Company name extraction
   - Amount detection (40+ patterns)
   - Frequency identification
   - Status determination

3. **Aggregation**
   - Group by company
   - Multiple account detection
   - Financial calculation
   - Timeline analysis

4. **Output Generation**
   - Console formatting
   - Excel generation
   - JSON serialization
   - CSV export

## Adaptive Database Scanning

The v2.1.0 adaptive scanning system provides universal compatibility:

### How It Works

1. **Table Discovery**
   ```python
   # Check what tables exist
   cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
   ```

2. **Column Mapping**
   ```python
   # Discover column names and types
   cursor.execute("PRAGMA table_info(recipients)")
   recipients_cols = {col[1]: col[2] for col in cursor.fetchall()}
   ```

3. **Intelligent Heuristics**
   - Message link columns: message, message_id, messageID
   - Address columns: address, email, recipient_address
   - Type columns: type, recipient_type, kind

4. **Dynamic Query Building**
   ```python
   if address_is_foreign_key:
       query = f"JOIN addresses ON recipients.{addr_col} = addresses.ROWID"
   else:
       query = f"SELECT recipients.{addr_col} directly"
   ```

5. **Graceful Degradation**
   - Missing tables → Skip recipient analysis
   - Missing columns → Use partial data
   - Query failures → Continue with sender data

### Benefits

- **Zero Configuration**: No user setup required
- **Universal Compatibility**: Works with all Mail versions
- **Future Proof**: Adapts to schema changes
- **Diagnostic Capable**: Clear error messages
- **Performance Optimized**: Fails fast when needed

## JSON Output and Data Interchange

All major scanners support standardized JSON output for data interchange:

### JSON Structure

```json
{
  "scan_date": "2024-12-20T10:30:00",
  "scan_parameters": {
    "days_back": 365,
    "keywords_used": 15,
    "database_type": "normalized"
  },
  "subscriptions": [
    {
      "company": "Netflix",
      "status": "active",
      "accounts": ["user@email.com"],
      "monthly_cost": 15.99,
      "annual_cost": 191.88,
      "last_seen": "2024-12-19",
      "email_count": 47
    }
  ],
  "financial_summary": {
    "monthly_total": 127.89,
    "annual_total": 1534.68,
    "duplicate_waste": 45.99
  }
}
```

### Using JSON Output

```bash
# Export to JSON
python3 working_scanner.py --output-json results.json

# Quiet mode for automation
python3 working_scanner.py --output-json data.json --quiet

# Load in Python
import json
with open('results.json') as f:
    data = json.load(f)
```

### Data Model Classes

- `SubscriptionEmail`: Individual email record
- `Subscription`: Aggregated subscription data
- `DuplicateSubscription`: Duplicate findings
- `ScanResults`: Complete scan output

## Troubleshooting Guide

### Common Issues and Solutions

#### Too Many Fake Subscriptions Found

1. **Use Secure Scanner**
   ```bash
   python3 scan_subscriptions_now.py
   # Choose Option 16 or 17
   ```

2. **Check Results**
   - Look for realistic company names
   - Verify reasonable payment amounts
   - Check for known services you use

3. **Manual Review**
   - Export to Excel for detailed analysis
   - Sort by amount to find outliers
   - Look for patterns in fake entries

#### No Subscriptions Found

1. **Check Email Download**
   - Ensure Apple Mail has downloaded messages
   - Check Mail → Preferences → Accounts → Download

2. **Extend Time Range**
   ```bash
   python3 working_scanner.py --days 3650  # 10 years
   ```

3. **Try Debug Mode**
   ```bash
   python3 scan_subscriptions_now.py
   # Choose Option 5 → b (test email search)
   ```

4. **Check Database Access**
   ```bash
   python3 test_setup.py
   ```

#### SQL Errors

1. **"no such column" errors**
   - Use Option 7 (working_scanner) - has adaptive scanning
   - Avoid older scanners on newer Mail versions

2. **"syntax error" messages**
   - Keywords with apostrophes are now escaped
   - Update to latest version

3. **Permission errors**
   - Check Full Disk Access in System Preferences
   - Run from Terminal, not IDE

#### Performance Issues

1. **Slow Scanning**
   ```bash
   # Preview first
   python3 working_scanner.py --dry-run
   
   # Limit time range
   python3 working_scanner.py --days 90
   ```

2. **Memory Issues**
   - Scanners process in 500-email batches
   - Close other applications
   - Use simple_scanner for large databases

#### Excel Export Problems

1. **Missing openpyxl**
   ```bash
   pip install openpyxl pandas
   ```

2. **File Permission Errors**
   - Check Desktop write permissions
   - Close existing Excel files

3. **Empty Excel File**
   - Run scan first, then export
   - Check for scan errors

#### MCP Connection Issues

1. **Server Not Found**
   - Restart Claude Desktop completely
   - Check config path is correct
   - Verify Python path in config

2. **Tools Not Available**
   - Check MCP server logs
   - Ensure virtual environment activated
   - Verify server.py permissions

### Advanced Troubleshooting

#### Database Structure Issues

```bash
# Check exact structure
python3 check_exact_structure.py

# Test recipient fetching
python3 check_recipients_structure.py

# Investigate specific issues
python3 investigate_structure.py
```

#### Query Testing

```bash
# Test working queries
python3 test_working_query.py

# Debug SQL generation
python3 debug_scan.py
```

#### Log Analysis

```bash
# MCP server logs
tail -f ~/Library/Logs/Claude/mcp*.log

# Scanner logs
tail -f subscripz_buster_mcp.log
```

## Excel Export Enhancement (v2.3.0)

### Critical New Feature: Sender Email Column

The Excel export now includes the sender email address for each subscription, making it easy to:
- Track down exactly which email address to unsubscribe from
- Verify the legitimacy of subscriptions
- Contact services directly for cancellation
- Identify which specific sender variant a company uses

### Excel Report Contents

1. **Summary Dashboard**: Financial overview with unknown high-value tracking
2. **All Subscriptions**: Now includes "Sender Email" column showing exact sender  
3. **Duplicate Analysis**: Cross-account subscription waste calculations
4. **By Account**: Breakdown of subscriptions per email account
5. **Timeline Analysis**: Activity-based grouping with highlighting

Example Excel row:
```
Company | Status | Accounts | Sender Email | Monthly Cost | Frequency
Netflix | ACTIVE | user@... | noreply@netflix.com | $15.99 | monthly
Adobe | ACTIVE | user@... | adobe@email.adobe.com | $52.99 | monthly
```

## Performance and Optimization

### Scanning Performance

- **Typical scan times**:
  - 1 year: 10-30 seconds
  - 5 years: 30-90 seconds
  - 20 years: 2-5 minutes

- **Factors affecting speed**:
  - Email volume
  - Database size
  - Keyword count
  - Computer specifications

### Optimization Tips

1. **Use Appropriate Scanner**
   - Quick check: simple_scanner
   - Full analysis: working_scanner
   - Maximum detail: comprehensive_scanner

2. **Leverage Dry Run**
   ```bash
   # See scope before scanning
   python3 working_scanner.py --dry-run
   ```

3. **Batch Processing**
   - Automatic 500-email batches
   - Prevents memory issues
   - Maintains performance

4. **Time Range Selection**
   - Start with 1 year
   - Expand if needed
   - Most subscriptions email monthly

## Fraud Detection System (New in v2.2.0)

### How It Works

The fraud detection system uses a multi-layered approach to identify and filter out phishing emails, scams, and fraudulent "subscriptions" that pollute your results:

#### 1. Domain Reputation Checking
```python
# Checks sender domains against:
- Known phishing domain blacklists
- Disposable email services
- Suspicious TLDs (.tk, .ml, .ga)
- DNS validation (domain must exist)
```

#### 2. Payment Amount Validation
```python
# Filters out unrealistic amounts:
- Daily charges over $100 (likely scams)
- Common scam amounts ($999, $399)
- Suspiciously precise amounts ($123.456)
```

#### 3. Service Whitelist Verification
```python
# 500+ known legitimate services including:
- Streaming: Netflix, Spotify, Hulu, etc.
- Software: Adobe, Microsoft, GitHub, etc.
- News: NYTimes, WSJ, The Guardian, etc.
- Shopping: Amazon, eBay, Etsy, etc.
```

#### 4. Pattern Matching
```python
# Identifies common fraud indicators:
- Urgent language ("ACT NOW!", "VERIFY IMMEDIATELY")
- Generic company names ("Email", "Mail", "Account")
- Excessive capitalization
- Multiple exclamation marks
```

### Example: Before and After Fraud Detection

**Before (without fraud detection):**
```
Found 1,006 "subscriptions" including:
- Email: $168.08/day (phishing)
- Mail: $410.00/day (scam)
- URGENT ACCOUNT: $999/month (fraud)
- Netflix: $15.99/month (legitimate)
```

**After (with secure scanner):**
```
Found 94 legitimate subscriptions:
- Netflix: $15.99/month ✓
- Spotify: $9.99/month ✓
- Adobe CC: $52.99/month ✓

Filtered out 912 fraudulent emails
```

### Using Fraud Detection

1. **For new scans**: Use Option 16 or 17 in the menu
2. **Command line**: `python3 secure_scanner.py`
3. **With Excel**: `python3 secure_excel_scanner.py`
4. **MCP**: "Use subscripz-buster secure scan to find my real subscriptions"

## Privacy and Security

### Data Protection

- **100% Local Processing**: No network connections
- **Read-Only Access**: Never modifies emails
- **No Data Collection**: No analytics or telemetry
- **No External APIs**: Everything runs on your Mac
- **Fraud Detection**: All filtering happens locally

### Security Considerations

1. **Database Access**
   - Read-only SQLite connections
   - No write permissions needed
   - Standard Apple Mail location

2. **File Outputs**
   - Saved to user Desktop only
   - Standard file permissions
   - No hidden locations

3. **MCP Server**
   - Local process only
   - No network exposure
   - Communicates via stdio

## Advanced Usage

### Command Line Options

```bash
# Specify time range
python3 working_scanner.py --days 730

# JSON export
python3 working_scanner.py --output-json results.json

# Quiet mode
python3 working_scanner.py --quiet --output-json data.json

# Dry run
python3 working_scanner.py --dry-run

# Show all results
python3 advanced_subscription_scanner.py --show-all
```

### Automation Examples

```bash
#!/bin/bash
# Monthly subscription audit
cd ~/Desktop/subscripz-buster
source .venv/bin/activate

# Run comprehensive scan
python3 comprehensive_scanner.py

# Export to Excel
python3 excel_export_fixed.py

# Email notification (example)
echo "Subscription scan complete" | mail -s "Monthly Audit" user@example.com
```

### Custom Integration

```python
# Use scan results programmatically
from working_scanner import WorkingSubscriptionScanner
from common_structures import format_currency

scanner = WorkingSubscriptionScanner()
results = scanner.scan_emails(days_back=365)

# Process results
total_monthly = sum(
    sub.avg_amount for sub in results.values() 
    if sub.status == 'active' and sub.avg_amount
)

print(f"Total monthly cost: {format_currency(total_monthly)}")
```

### Extending the System

1. **Add Keywords**
   ```python
   # In any scanner file
   SUBSCRIPTION_KEYWORDS.extend([
       "your_new_keyword",
       "another_pattern"
   ])
   ```

2. **Add Currency Patterns**
   ```python
   # In payment_extractor.py
   CURRENCY_PATTERNS.append(
       (r'R\s*(\d+)', 'ZAR')  # South African Rand
   )
   ```

3. **Custom Scanners**
   - Extend base scanner classes
   - Implement scan_emails method
   - Add to menu system

## Development

### Project Structure

```
subscripz-buster/
├── Core Files
│   ├── server.py              # MCP server
│   ├── scan_subscriptions_now.py  # Menu launcher
│   ├── common_structures.py   # Data models
│   └── payment_extractor.py   # Payment detection
├── Scanners/
│   ├── working_scanner.py     # Adaptive scanner
│   ├── advanced_subscription_scanner.py
│   ├── comprehensive_scanner.py
│   ├── simple_scanner.py
│   ├── fixed_scanner.py
│   ├── secure_scanner.py 🆕  # Fraud-filtered scanner
│   └── secure_excel_scanner.py 🆕 # Fraud + Excel
├── Fraud Detection/ 🆕
│   └── fraud_detector.py      # Multi-layer fraud detection
├── Utilities/
│   ├── duplicate_finder.py
│   ├── financial_summary.py
│   ├── export_to_csv.py
│   └── excel_export_fixed.py
├── Debug Tools/
│   ├── check_*.py
│   ├── test_*.py
│   └── investigate_*.py
├── Configuration/
│   ├── requirements.txt
│   ├── setup.sh
│   └── .gitignore
└── Documentation/
    ├── README.md
    ├── CHANGELOG.md
    ├── ADAPTIVE_SCANNING.md
    └── QUICK_REFERENCE.md
```

### Contributing

1. **Adding Features**
   - Maintain backward compatibility
   - Add tests for new functionality
   - Update documentation

2. **Reporting Issues**
   - Include macOS version
   - Include Apple Mail version
   - Run debug tools first
   - Include error messages

3. **Code Style**
   - Follow PEP 8
   - Add type hints
   - Document functions
   - Handle errors gracefully

### Testing

```bash
# Run all tests
python3 test_enhanced_features.py
python3 test_json_export.py
python3 test_dry_run.py

# Validate setup
python3 test_setup.py

# Check specific features
python3 test_working_query.py
```

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.

### Recent Updates

#### v2.3.0 (Latest - June 2025)
- **Enhanced Fraud Detection**
  - Expanded to 1000+ blacklisted domains and patterns
  - Added DNS validation and MX record checking
  - Typosquatting detection (mircosoft, amaz0n, etc.)
  - Improved company name extraction with display name support
  - Better handling of service name variations (amazonses → Amazon)
- **Payment Extraction Improvements**
  - Proximity-based frequency detection near amounts
  - Enhanced context-aware extraction for complex patterns
  - Better handling of "annual plan, billed monthly" scenarios
- **Data Structure Enhancements**
  - Added billing_period_details field to track frequency determination
  - Smarter financial calculations for high-value unknowns
  - Separate tracking of $200+ subscriptions with unknown frequency
- **Excel Export Improvements**
  - NEW: Sender Email column for easy subscription management
  - Enhanced financial summaries with unknown tracking
  - Better formatting and data organization
- **MCP Server Updates**
  - More robust error handling
  - Better integration with enhanced detectors

#### v2.2.0
- Advanced Fraud Detection System
- Multi-layer filtering for phishing/scam emails  
- Domain reputation checking and blacklists
- Suspicious amount validation
- 500+ service whitelist
- New Secure Scanners (Options 16 & 17)
- Filters out fake $100+/day "subscriptions"
- Removes generic phishing attempts
- Accurate financial calculations

#### v2.1.0
- Adaptive database scanning
- Robust recipient detection  
- Enhanced payment extraction
- Fixed Excel export
- Comprehensive JSON support
- Improved error handling

## License

MIT License - See LICENSE file for details.

## Acknowledgments

Built to solve the universal problem of subscription creep. Special thanks to the MCP team at Anthropic for enabling natural language integration.

## Support

For issues or questions:
1. Check the Troubleshooting Guide
2. Run debug tools (Option 5)
3. Review logs
4. Check GitHub issues

---

Remember: The best subscription is the one you actually use and remember paying for!
