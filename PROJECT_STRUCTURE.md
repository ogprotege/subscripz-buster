# Project Structure

## Core Files
- `server.py` - MCP server implementation
- `scan_subscriptions_now.py` - Main menu launcher
- `common_structures.py` - Shared data models and JSON standardization
- `payment_extractor.py` - Payment amount extraction utilities
- `fraud_detector.py` - Fraud detection system

## Active Scanners
- `working_scanner.py` - Recommended adaptive scanner
- `comprehensive_scanner.py` - Shows all subscriptions
- `advanced_subscription_scanner.py` - Advanced 100+ keyword scanner
- `simple_scanner.py` - Basic quick scanner
- `fixed_scanner.py` - For normalized databases
- `fixed_working_scanner.py` - Fixed version without recipient errors
- `fixed_advanced_scanner.py` - Fixed advanced scanner
- `secure_scanner.py` - Fraud-filtered scanner
- `secure_excel_scanner.py` - Fraud-filtered Excel export

## Utility Scripts
- `duplicate_finder.py` - Find duplicate subscriptions
- `financial_summary.py` - Financial analysis
- `export_to_csv.py` - CSV export
- `subscription_scanner_excel.py` - Excel export

## Debug Tools
- `debug_scan.py` - Quick subscription check
- `deep_investigate.py` - Deep investigation
- `scan_by_sender.py` - Scan by sender domain
- `investigate_structure.py` - Database structure investigation

## Configuration
- `requirements.txt` - Python dependencies
- `pyproject.toml` - Project configuration
- `setup.sh` - Setup script
- `.gitignore` - Git ignore rules
- `uv.lock` - UV lock file

## Documentation
- `README.md` - Main documentation
- `CHANGELOG.md` - Version history
- `QUICK_REFERENCE.md` - Quick reference guide
- `ADAPTIVE_SCANNING.md` - Adaptive scanning documentation

## Directories
- `old/` - Archived and deprecated files
- `Logs_ETC/` - Log files and temporary data
- `chat_log/` - Development chat logs