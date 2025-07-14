#!/usr/bin/env python3
"""
Secure Excel Scanner - Combines fraud detection with Excel export
Filters out phishing/spam and creates comprehensive Excel reports
"""

from datetime import datetime
from pathlib import Path
from secure_scanner import SecureSubscriptionScanner
from excel_export_fixed import FixedExcelExporter


class SecureExcelScanner(SecureSubscriptionScanner):
    """
    Scanner that filters fraud AND exports to Excel.
    
    This combines the best of both worlds:
    - Removes phishing, spam, and fraudulent emails
    - Creates a professional Excel report with the clean data
    """
    
    def scan_and_export(self, days_back: int = 1825, excel_filename: str = None):
        """
        Scan emails with fraud filtering and export directly to Excel.
        
        Args:
            days_back: Number of days to scan (default 5 years)
            excel_filename: Output filename (auto-generated if not provided)
        """
        # First, run the secure scan to get clean data
        print("=" * 60)
        print("🔒 SECURE EXCEL SCANNER")
        print("Fraud Filtering + Excel Export")
        print("=" * 60)
        
        # Run the secure scan with fraud filtering
        clean_subscriptions = self.scan_emails(days_back=days_back)
        
        if not clean_subscriptions:
            print("\n❌ No legitimate subscriptions found after filtering.")
            print("   This might mean:")
            print("   • All emails were filtered as fraud/spam")
            print("   • No subscription emails in the time period")
            print("   • Try extending the time range")
            return None
        
        # Now export the clean data to Excel
        print("\n📊 Generating Excel report with clean data...")
        
        exporter = FixedExcelExporter()
        
        # Generate filename if not provided
        if not excel_filename:
            excel_filename = f"secure_subscriptions_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        # Export to Excel
        filepath = exporter.export_to_excel(clean_subscriptions, excel_filename)
        
        if filepath:
            print(f"\n✨ Success! Your fraud-filtered Excel report is ready:")
            print(f"   📁 {filepath}")
            print("\n📊 The Excel file contains:")
            print("   • Summary Dashboard - Financial overview without fraud")
            print("   • All Subscriptions - Only legitimate services")  
            print("   • Duplicate Analysis - Real duplicates, not spam")
            print("   • Account Breakdown - Clean view by email")
            print("   • Timeline Analysis - Actual subscription activity")
            
            # Show summary statistics
            if hasattr(self, 'scan_results') and self.scan_results:
                metadata = self.scan_results.scan_metadata
                print(f"\n🛡️ Fraud Filtering Statistics:")
                print(f"   • Fraudulent emails removed: {metadata.get('fraud_filtered', 0)}")
                print(f"   • Suspicious emails verified: {metadata.get('suspicious_verified', 0)}")
                print(f"   • Clean subscriptions exported: {len(clean_subscriptions)}")
        
        return filepath


def main():
    """Main function to run secure Excel scanner"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Secure scanner with fraud detection and Excel export'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=1825,  # 5 years
        help='Number of days to scan back (default: 1825 = 5 years)'
    )
    parser.add_argument(
        '--output',
        type=str,
        help='Excel filename (auto-generated if not specified)'
    )
    
    args = parser.parse_args()
    
    # Create and run scanner
    scanner = SecureExcelScanner()
    
    try:
        filepath = scanner.scan_and_export(
            days_back=args.days,
            excel_filename=args.output
        )
        
        if not filepath:
            return 1
            
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
