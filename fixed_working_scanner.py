#!/usr/bin/env python3
"""
Fixed working scanner - NO recipient queries to avoid all SQL errors
This version only uses sender information which is more reliable
"""

import os
import sqlite3
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict

# Import common structures for standardized output
try:
    from common_structures import (
        SubscriptionEmail, Subscription, DuplicateSubscription, 
        ScanResults, calculate_financial_summary, format_currency
    )
    COMMON_STRUCTURES_AVAILABLE = True
except ImportError:
    COMMON_STRUCTURES_AVAILABLE = False
    print("Note: common_structures.py not found. JSON export will be limited.")

# Subscription-related keywords
SUBSCRIPTION_KEYWORDS = [
    "subscription", "payment", "invoice", "billing", "receipt",
    "renewal", "renew", "recurring", "membership", "charge",
    "monthly", "annual", "yearly", "cancelled", "cancel",
    "trial", "premium", "paid", "plan", "subscribe"
]


class FixedWorkingScanner:
    """Scanner that works without recipient queries"""
    
    def __init__(self):
        self.mail_root = Path.home() / "Library" / "Mail"
        self.db_path = self._find_envelope_index()
        self.subscriptions = {}
        self.scan_results = None
        
    def _find_envelope_index(self) -> Path:
        """Find the Envelope Index database"""
        possible_paths = [
            self.mail_root / "V10" / "MailData" / "Envelope Index",
            self.mail_root / "V9" / "MailData" / "Envelope Index",
            self.mail_root / "V8" / "MailData" / "Envelope Index",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        raise FileNotFoundError("Could not find Apple Mail's Envelope Index database")
    
    def scan_emails(self, days_back: int = 365, dry_run: bool = False) -> Dict:
        """Scan emails and return structured data"""
        print(f"🔍 Scanning {days_back} days ({days_back/365:.1f} years) of email...")
        
        scan_start = datetime.now()
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check if we have normalized database
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='subjects'")
        has_subjects_table = cursor.fetchone() is not None
        
        # Build keyword conditions
        keyword_conditions = []
        for keyword in SUBSCRIPTION_KEYWORDS:
            escaped = keyword.replace("'", "''")
            if has_subjects_table:
                keyword_conditions.append(f"s.subject LIKE '%{escaped}%'")
            else:
                keyword_conditions.append(f"m.subject LIKE '%{escaped}%'")
        
        # Dry run - just count
        if dry_run:
            if has_subjects_table:
                count_query = f"""
                SELECT COUNT(DISTINCT m.message_id)
                FROM messages m
                JOIN subjects s ON m.subject = s.ROWID
                WHERE ({' OR '.join(keyword_conditions)})
                AND m.date_received > {cutoff_timestamp}
                """
            else:
                count_query = f"""
                SELECT COUNT(DISTINCT m.message_id)
                FROM messages m
                WHERE ({' OR '.join(keyword_conditions)})
                AND m.date_received > {cutoff_timestamp}
                """
            
            cursor.execute(count_query)
            count = cursor.fetchone()[0]
            
            # Also get total emails in period
            cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
            total_emails = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\n🔍 DRY RUN RESULTS:")
            print(f"   Total emails in period: {total_emails:,}")
            print(f"   Subscription emails found: {count:,}")
            print(f"   Percentage: {(count/total_emails*100):.1f}%" if total_emails > 0 else "N/A")
            print(f"\n💡 Run without --dry-run to process these emails")
            
            return {}
        
        # Full query - NO RECIPIENT INFO
        if has_subjects_table:
            # Normalized database query
            query = f"""
            SELECT 
                m.message_id,
                s.subject as subject_text,
                m.date_received,
                sender.address as sender_address
            FROM messages m
            JOIN subjects s ON m.subject = s.ROWID
            LEFT JOIN addresses sender ON m.sender = sender.ROWID
            WHERE ({' OR '.join(keyword_conditions)})
            AND m.date_received > {cutoff_timestamp}
            ORDER BY m.date_received DESC
            """
        else:
            # Legacy database query
            query = f"""
            SELECT 
                m.message_id,
                m.subject as subject_text,
                m.date_received,
                s.address as sender_address
            FROM messages m
            LEFT JOIN addresses s ON m.sender = s.ROWID
            WHERE ({' OR '.join(keyword_conditions)})
            AND m.date_received > {cutoff_timestamp}
            ORDER BY m.date_received DESC
            """
        
        print("   Executing query...")
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Count total emails for statistics
        cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
        total_emails = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   ✅ Found {len(results)} subscription-related emails!")
        
        # Process results into structured data
        self._process_results(results)
        
        # Create scan results object
        if COMMON_STRUCTURES_AVAILABLE:
            self.scan_results = ScanResults(
                scan_date=scan_start,
                scan_parameters={
                    'days_back': days_back,
                    'keywords_used': len(SUBSCRIPTION_KEYWORDS),
                    'database_type': 'normalized' if has_subjects_table else 'legacy'
                },
                total_emails_scanned=total_emails,
                subscription_emails_found=len(results),
                unique_subscriptions=list(self.subscriptions.values()) if COMMON_STRUCTURES_AVAILABLE else [],
                duplicate_subscriptions=self._find_duplicates(),
                financial_summary=calculate_financial_summary(
                    list(self.subscriptions.values()), 
                    self._find_duplicates()
                ),
                scan_metadata={
                    'scanner_version': '2.2',
                    'scanner_name': 'fixed_working_scanner',
                    'database_path': str(self.db_path)
                }
            )
        
        return self.subscriptions
    
    def _process_results(self, emails: List[tuple]) -> None:
        """Process email results into subscription objects"""
        subscription_map = defaultdict(lambda: {
            'emails': [],
            'companies': set(),  # Track by sender domain instead of recipient
            'amounts': [],
            'currencies': set(),
            'first_seen': None,
            'last_seen': None,
            'status': 'unknown'
        })
        
        for email in emails:
            message_id, subject, date_received, sender = email
            
            if not sender:
                continue
                
            # Extract company name
            company = self._extract_company(sender)
            if not company:
                continue
            
            # Convert timestamp
            email_date = datetime.fromtimestamp(date_received) if date_received else datetime.now()
            
            # Create email object if using common structures
            if COMMON_STRUCTURES_AVAILABLE:
                email_obj = SubscriptionEmail(
                    message_id=message_id,
                    subject=subject or '',
                    sender=sender,
                    recipient='unknown',  # We don't have recipient info
                    date_received=email_date
                )
                
                # Extract amount if possible
                amount, currency = self._extract_amount(subject or '')
                if amount:
                    email_obj.amount = amount
                    email_obj.currency = currency
                    subscription_map[company]['amounts'].append(amount)
                    subscription_map[company]['currencies'].add(currency)
            
            # Update subscription data
            sub = subscription_map[company]
            if COMMON_STRUCTURES_AVAILABLE:
                sub['emails'].append(email_obj)
            
            # Track sender domain as pseudo-account
            if '@' in sender:
                domain = sender.split('@')[1]
                sub['companies'].add(domain)
            
            # Update dates
            if not sub['first_seen'] or email_date < sub['first_seen']:
                sub['first_seen'] = email_date
            if not sub['last_seen'] or email_date > sub['last_seen']:
                sub['last_seen'] = email_date
            
            # Update status based on keywords
            if subject:
                subject_lower = subject.lower()
                if any(word in subject_lower for word in ['cancel', 'terminated']):
                    sub['status'] = 'cancelled'
                elif any(word in subject_lower for word in ['active', 'renewed', 'payment received']):
                    sub['status'] = 'active'
                elif 'trial' in subject_lower:
                    sub['status'] = 'trial'
                elif any(word in subject_lower for word in ['failed', 'declined']):
                    sub['status'] = 'failed'
        
        # Convert to Subscription objects
        if COMMON_STRUCTURES_AVAILABLE:
            for company, data in subscription_map.items():
                # Determine if inactive
                days_inactive = (datetime.now() - data['last_seen']).days
                if days_inactive > 180 and data['status'] not in ['cancelled', 'failed']:
                    data['status'] = 'inactive'
                
                # Calculate average amount
                avg_amount = sum(data['amounts']) / len(data['amounts']) if data['amounts'] else None
                
                # Guess frequency based on email patterns
                frequency = self._guess_frequency(data['emails']) if COMMON_STRUCTURES_AVAILABLE else None
                
                self.subscriptions[company] = Subscription(
                    company=company,
                    emails=data['emails'],
                    accounts=set(['unknown']),  # We don't have recipient info
                    amounts=data['amounts'],
                    currencies=data['currencies'],
                    first_seen=data['first_seen'],
                    last_seen=data['last_seen'],
                    status=data['status'],
                    email_count=len(data['emails']),
                    avg_amount=avg_amount,
                    frequency=frequency
                )
        else:
            # Fallback for when common_structures is not available
            self.subscriptions = dict(subscription_map)
    
    def _extract_company(self, sender_email: str) -> Optional[str]:
        """Extract company name from sender email"""
        if not sender_email or '@' not in sender_email:
            return None
            
        # Remove common prefixes
        email_lower = sender_email.lower()
        for prefix in ['noreply@', 'no-reply@', 'billing@', 'support@']:
            if email_lower.startswith(prefix):
                domain = email_lower.replace(prefix, '')
                company = domain.split('.')[0]
                return company.title()
        
        # Extract domain
        domain = sender_email.split('@')[1]
        company = domain.split('.')[0]
        
        # Skip common email providers
        if company.lower() in ['gmail', 'yahoo', 'outlook', 'hotmail']:
            return None
            
        return company.title()
    
    def _extract_amount(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Extract payment amount and currency from text"""
        if not text:
            return None, None
            
        # Currency patterns
        patterns = [
            (r'\$\s*([\d,]+\.?\d*)', 'USD'),
            (r'USD\s*([\d,]+\.?\d*)', 'USD'),
            (r'£\s*([\d,]+\.?\d*)', 'GBP'),
            (r'€\s*([\d,]+\.?\d*)', 'EUR'),
        ]
        
        for pattern, currency in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    return amount, currency
                except:
                    pass
                    
        return None, None
    
    def _guess_frequency(self, emails: List[SubscriptionEmail]) -> Optional[str]:
        """Guess subscription frequency based on email patterns"""
        if len(emails) < 2:
            return None
            
        # Check subject lines for frequency keywords
        for email in emails:
            subject_lower = email.subject.lower()
            if any(word in subject_lower for word in ['annual', 'yearly']):
                return 'annual'
            elif any(word in subject_lower for word in ['monthly', 'month']):
                return 'monthly'
                
        # Could add more sophisticated frequency detection based on email intervals
        return None
    
    def _find_duplicates(self) -> List[DuplicateSubscription]:
        """Find subscriptions that appear on multiple accounts"""
        # Since we don't have recipient info, we can't find duplicates
        return []
    
    def display_results(self, limit: int = 25) -> None:
        """Display results in console"""
        if not self.subscriptions:
            print("\n📭 No subscriptions found")
            return
        
        print(f"\n✅ Processed {len(self.subscriptions)} unique subscriptions")
        
        # Calculate totals
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            summary = self.scan_results.get_summary_stats()
            financial = self.scan_results.financial_summary
            
            print(f"\n📊 SUBSCRIPTION ANALYSIS")
            print("=" * 80)
            print(f"Total unique subscriptions: {summary['total_subscriptions']}")
            print(f"Active subscriptions: {summary['active_subscriptions']}")
            print(f"Inactive subscriptions: {summary['inactive_subscriptions']}")
            print(f"\n💰 ESTIMATED COSTS")
            print(f"Monthly total: {format_currency(financial['monthly_total'])}")
            print(f"Annual total: {format_currency(financial['annual_total'])}")
        
        # Sort by email count
        sorted_subs = sorted(self.subscriptions.items(), 
                           key=lambda x: x[1].email_count if COMMON_STRUCTURES_AVAILABLE else len(x[1]['emails']), 
                           reverse=True)
        
        print(f"\n📋 TOP SUBSCRIPTIONS (showing {min(limit, len(sorted_subs))} of {len(sorted_subs)})")
        print("=" * 80)
        
        for i, (company, sub) in enumerate(sorted_subs[:limit], 1):
            if COMMON_STRUCTURES_AVAILABLE and isinstance(sub, Subscription):
                print(f"\n{i}. {company}")
                print(f"   📧 {sub.email_count} emails")
                if sub.avg_amount:
                    print(f"   💰 Avg amount: {format_currency(sub.avg_amount, list(sub.currencies)[0] if sub.currencies else 'USD')}")
                print(f"   📅 Last seen: {(datetime.now() - sub.last_seen).days} days ago")
                if sub.status == 'inactive':
                    print(f"   ⚠️  Possibly inactive!")
            else:
                # Fallback display
                print(f"\n{i}. {company}")
                print(f"   📧 {len(sub['emails'])} emails")
    
    def export_json(self, filepath: str) -> None:
        """Export results to JSON file"""
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            print(f"\n💾 Exporting to {filepath}...")
            self.scan_results.to_json(filepath)
            print(f"✅ Exported scan results to {filepath}")
        else:
            print("⚠️  JSON export requires common_structures.py")


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Fixed scanner without recipient queries'
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
        '--quiet',
        action='store_true',
        help='Suppress console output (useful with --output-json)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show how many emails would be processed without actually processing them'
    )
    
    args = parser.parse_args()
    
    # Run scanner
    scanner = FixedWorkingScanner()
    
    try:
        scanner.scan_emails(days_back=args.days, dry_run=args.dry_run)
        
        # Don't display full results or export if dry run
        if args.dry_run:
            return 0
        
        # Display results unless quiet mode
        if not args.quiet:
            scanner.display_results(limit=args.limit)
        
        # Export JSON if requested
        if args.output_json:
            scanner.export_json(args.output_json)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
