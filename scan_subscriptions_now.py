#!/usr/bin/env python3
"""
Subscription Scanner Launcher
Main menu for running different subscription scanners
"""

import os
import sys
import subprocess
from pathlib import Path

def clear_screen():
    """Clear the terminal screen"""
    os.system('clear' if os.name == 'posix' else 'cls')

def run_scanner(script_name, args=None):
    """Run a scanner script with optional arguments"""
    cmd = [sys.executable, script_name]
    if args:
        cmd.extend(args)
    
    try:
        subprocess.run(cmd, cwd=Path(__file__).parent)
    except KeyboardInterrupt:
        print("\n\n⚠️  Scan cancelled by user")
    except Exception as e:
        print(f"\n❌ Error running scanner: {e}")

def main():
    """Main menu loop"""
    while True:
        clear_screen()
        print("🔍 SUBSCRIPTION SCANNER LAUNCHER")
        print("=" * 50)
        print("\nChoose an option:")
        print("1. Simple scan (basic)")
        print("2. Advanced scan with console output")
        print("3. Full scan with Excel export")
        print("4. Custom scan (specify years)")
        print("5. Debug - check what's in your email")
        print("6. Fixed scanner (normalized databases)")
        print("7. ⭐ WORKING SCANNER - Recommended")
        print("8. 📊 Comprehensive Report (ALL subscriptions)")
        print("9. 💰 Financial Summary Only")
        print("10. 📄 Export to CSV")
        print("11. 🔍 Duplicate Finder")
        print("12. 🆕 JSON Export Test")
        print("13. 🧪 Test Dry-Run Mode")
        print("14. 🔧 Fixed Working Scanner (NO recipient errors)")
        print("15. 🔧 Fixed Advanced Scanner (NO recipient errors)")
        print("16. 🔒 SECURE Scanner - Filters Fraud (NEW!)")
        print("17. 🔒📊 SECURE Excel Scanner - Fraud Filter + Excel Export (NEW!)")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-17): ").strip()
        
        if choice == '0':
            print("\n👋 Goodbye!")
            break
            
        elif choice == '1':
            print("\n🚀 Running simple scanner (most stable)...")
            years = input("How many years to scan? (default 1): ").strip() or "1"
            days = int(float(years) * 365)
            run_scanner("simple_scanner.py", ["--days", str(days)])
            
        elif choice == '2':
            print("\n🚀 Running advanced scanner...")
            run_scanner("advanced_subscription_scanner.py")
            
        elif choice == '3':
            print("\n📊 Running full scan with Excel export...")
            run_scanner("subscription_scanner_excel.py")
            
        elif choice == '4':
            print("\n🔧 Custom scan")
            years = input("How many years to scan? (default 20): ").strip() or "20"
            days = int(float(years) * 365)
            run_scanner("advanced_subscription_scanner.py", ["--days", str(days)])
            
        elif choice == '5':
            # Debug submenu
            print("\n🔍 Debug Options:")
            print("a) Quick check for subscriptions")
            print("b) Deep investigation")
            print("c) Scan by sender domain")
            print("d) Investigate database structure")
            
            debug_choice = input("\nEnter choice (a-d): ").strip().lower()
            
            if debug_choice == 'a':
                run_scanner("debug_scan.py")
            elif debug_choice == 'b':
                run_scanner("deep_investigate.py")
            elif debug_choice == 'c':
                run_scanner("scan_by_sender.py")
            elif debug_choice == 'd':
                run_scanner("investigate_structure.py")
            
        elif choice == '6':
            print("\n🔧 Running fixed scanner for normalized databases...")
            years = input("How many years to scan? (default 5): ").strip() or "5"
            days = int(float(years) * 365)
            run_scanner("fixed_scanner.py", ["--days", str(days)])
            
        elif choice == '7':
            print("\n⭐ Running WORKING scanner (tested with your database)...")
            years = input("How many years to scan? (default 5): ").strip() or "5"
            days = int(float(years) * 365)
            run_scanner("working_scanner.py", ["--days", str(days)])
            
        elif choice == '8':
            print("\n📊 Running comprehensive scanner (shows ALL subscriptions)...")
            years = input("How many years to scan? (default 5): ").strip() or "5"
            days = int(float(years) * 365)
            run_scanner("comprehensive_scanner.py", ["--days", str(days)])
            
        elif choice == '9':
            print("\n💰 Running financial summary...")
            run_scanner("financial_summary.py")
            
        elif choice == '10':
            print("\n📄 Exporting to CSV...")
            years = input("How many years to export? (default 5): ").strip() or "5"
            days = int(float(years) * 365)
            run_scanner("export_to_csv.py", ["--days", str(days)])
            
        elif choice == '11':
            print("\n🔍 Running duplicate finder...")
            run_scanner("duplicate_finder.py")
            
        elif choice == '12':
            print("\n🆕 Testing JSON Export capabilities...")
            print("\nSelect scanner to test JSON export:")
            print("1. Working Scanner")
            print("2. Advanced Scanner")
            print("3. Comprehensive Scanner")
            
            json_choice = input("\nEnter choice (1-3): ").strip()
            
            if json_choice == '1':
                print("\nTesting Working Scanner with JSON export...")
                run_scanner("working_scanner.py", ["--days", "365", "--output-json", "test_working.json"])
                print("\n✅ Check test_working.json for results")
                
            elif json_choice == '2':
                print("\nTesting Advanced Scanner with JSON export...")
                run_scanner("advanced_subscription_scanner.py", ["--days", "365", "--output-json", "test_advanced.json"])
                print("\n✅ Check test_advanced.json for results")
                
            elif json_choice == '3':
                print("\nTesting Comprehensive Scanner with JSON export...")
                run_scanner("comprehensive_scanner.py", ["--days", "365", "--output-json", "test_comprehensive.json"])
                print("\n✅ Check test_comprehensive.json for results")
        
        elif choice == '13':
            print("\n🧪 Testing Dry-Run Mode...")
            print("\nDry-run shows how many emails would be processed without actually processing them.")
            print("\nSelect scanner to test:")
            print("1. Working Scanner")
            print("2. Advanced Scanner")
            print("3. Simple Scanner")
            
            dry_choice = input("\nEnter choice (1-3): ").strip()
            
            if dry_choice == '1':
                print("\nTesting Working Scanner dry-run...")
                run_scanner("working_scanner.py", ["--days", "365", "--dry-run"])
                
            elif dry_choice == '2':
                print("\nTesting Advanced Scanner dry-run...")
                run_scanner("advanced_subscription_scanner.py", ["--days", "365", "--dry-run"])
                
            elif dry_choice == '3':
                print("\nTesting Simple Scanner dry-run...")
                run_scanner("simple_scanner.py", ["--days", "365", "--dry-run"])
        
        elif choice == '14':
            print("\n🔧 Running FIXED Working Scanner (no recipient errors)...")
            years = input("How many years to scan? (default 5): ").strip() or "5"
            days = int(float(years) * 365)
            run_scanner("fixed_working_scanner.py", ["--days", str(days)])
            
        elif choice == '15':
            print("\n🔧 Running FIXED Advanced Scanner (no recipient errors)...")
            years = input("How many years to scan? (default 20): ").strip() or "20"
            days = int(float(years) * 365)
            run_scanner("fixed_advanced_scanner.py", ["--days", str(days)])
            
        elif choice == '16':
            print("\n🔒 Running SECURE Scanner with Fraud Detection...")
            print("\nThis scanner filters out:")
            print("  • Phishing emails with fake payment amounts")
            print("  • Spam from suspicious domains")
            print("  • Fraudulent services with unrealistic charges")
            print("  • Generic senders that can't be verified")
            years = input("\nHow many years to scan? (default 5): ").strip() or "5"
            days = int(float(years) * 365)
            show_fraud = input("Show filtered fraud examples? (y/N): ").strip().lower() == 'y'
            args = ["--days", str(days)]
            if show_fraud:
                args.append("--show-fraud")
            run_scanner("secure_scanner.py", args)
            
        elif choice == '17':
            print("\n🔒📊 Running SECURE Excel Scanner...")
            print("\nThis scanner:")
            print("  1️⃣  Filters out fraud, phishing, and spam")
            print("  2️⃣  Creates a clean Excel report with only legitimate subscriptions")
            print("  3️⃣  Saves the Excel file to your Desktop")
            years = input("\nHow many years to scan? (default 5): ").strip() or "5"
            days = int(float(years) * 365)
            filename = input("Excel filename (press Enter for auto-generated): ").strip()
            args = ["--days", str(days)]
            if filename:
                args.extend(["--output", filename])
            run_scanner("secure_excel_scanner.py", args)
        
        else:
            print("\n⚠️  Invalid choice!")
        
        if choice != '0':
            input("\n✅ Press Enter to continue...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
