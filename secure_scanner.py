#!/usr/bin/env python3
"""
Enhanced subscription scanner with integrated fraud detection
Filters out phishing, spam, and fraudulent subscription emails
"""

import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# Import our modules
from common_structures import (
    SubscriptionEmail, Subscription, DuplicateSubscription, 
    ScanResults, calculate_financial_summary, format_currency
)
from payment_extractor import PaymentExtractor
from fraud_detector import FraudDetector
from working_scanner import WorkingSubscriptionScanner


class SecureSubscriptionScanner(WorkingSubscriptionScanner):
    """
    Enhanced scanner that filters out fraudulent subscription emails.
    
    This scanner extends the working scanner with:
    - Advanced fraud detection
    - Domain reputation checking
    - Payment amount validation
    - Legitimate service verification
    """
    
    def __init__(self):
        super().__init__()
        self.fraud_detector = FraudDetector()
        self.filtered_emails = []  # Store fraudulent emails for reporting
        
    def scan_emails(self, days_back: int = 365, dry_run: bool = False) -> Dict:
        """Enhanced scan with fraud filtering"""
        print(f"🔒 SECURE SUBSCRIPTION SCANNER WITH FRAUD DETECTION")
        print("=" * 60)
        print(f"🔍 Scanning {days_back} days ({days_back/365:.1f} years) of email...")
        
        # First, run the parent scanner to get raw results
        raw_subscriptions = super().scan_emails(days_back, dry_run)
        
        if dry_run:
            return raw_subscriptions
        
        print("\n🛡️ Applying fraud detection filters...")
        
        # Now filter the results
        filtered_subscriptions = {}
        fraud_count = 0
        suspicious_count = 0
        
        for company, subscription in self.subscriptions.items():
            # Check if this subscription appears legitimate
            if hasattr(subscription, 'emails') and subscription.emails:
                # Get a representative email to check
                sample_email = subscription.emails[0]
                
                # Check for fraud indicators
                is_fraud, fraud_reasons = self.fraud_detector.is_likely_fraud(
                    sender=sample_email.sender,
                    subject=sample_email.subject,
                    amount=subscription.avg_amount,
                    frequency=subscription.frequency
                )
                
                if is_fraud:
                    fraud_count += 1
                    print(f"   ❌ Filtered '{company}': {', '.join(fraud_reasons)}")
                    continue
                
                # Additional checks for suspicious patterns
                if self._is_suspicious_subscription(subscription):
                    suspicious_count += 1
                    print(f"   ⚠️  Suspicious '{company}': Generic name, verifying...")
                    
                    # Try to extract legitimate company name
                    legit_company = self.fraud_detector.extract_legitimate_company_name(
                        sample_email.sender, sample_email.subject
                    )
                    
                    if legit_company:
                        # Update with cleaned name
                        subscription.company = legit_company
                        filtered_subscriptions[legit_company] = subscription
                        print(f"      ✅ Verified as: {legit_company}")
                    else:
                        print(f"      ❌ Could not verify, filtering out")
                        fraud_count += 1
                        continue
                else:
                    # Appears legitimate
                    filtered_subscriptions[company] = subscription
        
        print(f"\n📊 Filtering Results:")
        print(f"   Total subscriptions found: {len(self.subscriptions)}")
        print(f"   Fraudulent filtered out: {fraud_count}")
        print(f"   Suspicious verified: {suspicious_count}")
        print(f"   Legitimate subscriptions: {len(filtered_subscriptions)}")
        
        # Update the scanner's subscriptions with filtered results
        self.subscriptions = filtered_subscriptions
        
        # Recalculate scan results with clean data
        if hasattr(self, 'scan_results') and self.scan_results:
            self.scan_results.unique_subscriptions = list(filtered_subscriptions.values())
            self.scan_results.duplicate_subscriptions = self._find_duplicates()
            self.scan_results.financial_summary = calculate_financial_summary(
                list(filtered_subscriptions.values()),
                self._find_duplicates()
            )
            
            # Add fraud statistics to metadata
            self.scan_results.scan_metadata['fraud_filtered'] = fraud_count
            self.scan_results.scan_metadata['suspicious_verified'] = suspicious_count
        
        return filtered_subscriptions
    
    def _is_suspicious_subscription(self, subscription: Subscription) -> bool:
        """Check if a subscription has suspicious characteristics"""
        # Generic company names that need verification
        generic_names = {
            'email', 'mail', 'e', 'secure', 'account', 'notification',
            'alert', 'update', 'verify', 'confirm', 'payment', 'billing',
            'invoice', 'order', 'receipt', 'transaction', 'service',
            'support', 'customer', 'help', 'info', 'contact', 'my',
            'emails', 'ordering', 'agent', 'digest'
        }
        
        company_lower = subscription.company.lower()
        
        # Check for generic names
        if company_lower in generic_names:
            return True
        
        # Check for unusually high daily charges
        if subscription.frequency == 'daily' and subscription.avg_amount:
            if subscription.avg_amount > 50:  # More than $50/day is suspicious
                return True
        
        # Check for nonsensical amounts
        if subscription.avg_amount:
            # Convert to monthly for comparison
            if subscription.frequency == 'annual':
                monthly = subscription.avg_amount / 12
            elif subscription.frequency == 'daily':
                monthly = subscription.avg_amount * 30
            elif subscription.frequency == 'weekly':
                monthly = subscription.avg_amount * 4.33
            else:
                monthly = subscription.avg_amount
            
            # More than $500/month for a single subscription is suspicious
            if monthly > 500:
                return True
        
        return False
    
    def display_results(self, limit: int = 25, show_fraud: bool = False) -> None:
        """Enhanced display with fraud statistics"""
        super().display_results(limit)
        
        if hasattr(self, 'scan_results') and self.scan_results:
            metadata = self.scan_results.scan_metadata
            if 'fraud_filtered' in metadata:
                print(f"\n🛡️ FRAUD DETECTION SUMMARY")
                print("=" * 80)
                print(f"Fraudulent emails filtered: {metadata['fraud_filtered']}")
                print(f"Suspicious emails verified: {metadata.get('suspicious_verified', 0)}")
                
                # Show some examples of what was filtered if requested
                if show_fraud and metadata['fraud_filtered'] > 0:
                    print("\nExamples of filtered fraudulent subscriptions:")
                    print("(These were removed from your results)")
                    # This would show examples of filtered emails


def main():
    """Run the secure scanner with fraud detection"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Secure subscription scanner with fraud detection'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=365,
        help='Number of days to scan back (default: 365)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=25,
        help='Number of results to display (default: 25)'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        help='Path to export JSON results'
    )
    parser.add_argument(
        '--show-fraud',
        action='store_true',
        help='Show examples of filtered fraudulent emails'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview scan without processing'
    )
    
    args = parser.parse_args()
    
    # Run scanner
    scanner = SecureSubscriptionScanner()
    
    try:
        scanner.scan_emails(days_back=args.days, dry_run=args.dry_run)
        
        if args.dry_run:
            return 0
        
        # Display results
        scanner.display_results(limit=args.limit, show_fraud=args.show_fraud)
        
        # Export JSON if requested
        if args.output_json:
            scanner.export_json(args.output_json)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
