#!/usr/bin/env python3
"""
Simple subscription scanner with basic keyword detection and JSON export support.
Most stable option with fewer keywords to avoid SQL errors.
"""

import os
import sqlite3
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from collections import defaultdict

# Import common structures
try:
    from common_structures import (
        SubscriptionEmail, Subscription, DuplicateSubscription, 
        ScanResults, calculate_financial_summary, format_currency
    )
    COMMON_STRUCTURES_AVAILABLE = True
except ImportError:
    COMMON_STRUCTURES_AVAILABLE = False

# Core subscription keywords (limited set for stability)
CORE_KEYWORDS = [
    "subscription", "payment", "invoice", "billing", "receipt",
    "renewal", "renew", "recurring", "membership", "charge",
    "monthly", "annual", "cancelled", "trial", "premium"
]


class SimpleSubscriptionScanner:
    """Simple scanner with basic functionality"""
    
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
        """Simple scan with core keywords"""
        print(f"🚀 SIMPLE SUBSCRIPTION SCANNER")
        print("=" * 60)
        print(f"🔍 Scanning {days_back} days of email...")
        
        scan_start = datetime.now()
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check database structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='subjects'")
        has_subjects_table = cursor.fetchone() is not None
        
        # Dry run - just count
        if dry_run:
            print(f"   🔍 DRY RUN MODE - Counting matching emails...")
            
            total_count = 0
            for i in range(0, len(CORE_KEYWORDS), 5):
                batch_keywords = CORE_KEYWORDS[i:i + 5]
                
                if has_subjects_table:
                    keyword_conditions = []
                    for keyword in batch_keywords:
                        escaped = keyword.replace("'", "''")
                        keyword_conditions.append(f"LOWER(s.subject) LIKE LOWER('%{escaped}%')")
                    
                    count_query = f"""
                    SELECT COUNT(DISTINCT m.message_id)
                    FROM messages m
                    JOIN subjects s ON m.subject = s.ROWID
                    WHERE ({' OR '.join(keyword_conditions)})
                    AND m.date_received > {cutoff_timestamp}
                    """
                else:
                    keyword_conditions = []
                    for keyword in batch_keywords:
                        escaped = keyword.replace("'", "''")
                        keyword_conditions.append(f"LOWER(m.subject) LIKE LOWER('%{escaped}%')")
                    
                    count_query = f"""
                    SELECT COUNT(DISTINCT m.message_id)
                    FROM messages m
                    WHERE ({' OR '.join(keyword_conditions)})
                    AND m.date_received > {cutoff_timestamp}
                    """
                
                try:
                    cursor.execute(count_query)
                    batch_count = cursor.fetchone()[0]
                    total_count += batch_count
                    print(f"   ✓ Batch {i//5 + 1}: {batch_count} emails")
                except Exception as e:
                    print(f"   ⚠️  Error counting batch {i//5 + 1}: {str(e)}")
            
            # Get total email count
            cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
            total_emails = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\n🔍 DRY RUN RESULTS:")
            print(f"   Total emails in period: {total_emails:,}")
            print(f"   Subscription-related emails: ~{total_count:,}")
            print(f"   Percentage: ~{(total_count/total_emails*100):.1f}%" if total_emails > 0 else "N/A")
            print(f"\n💡 Run without --dry-run to process these emails")
            
            return {}
        
        # Process keywords in small batches
        batch_size = 5
        all_results = []
        
        for i in range(0, len(CORE_KEYWORDS), batch_size):
            batch_keywords = CORE_KEYWORDS[i:i + batch_size]
            
            try:
                if has_subjects_table:
                    # Normalized database
                    keyword_conditions = []
                    for keyword in batch_keywords:
                        escaped = keyword.replace("'", "''")
                        keyword_conditions.append(f"s.subject LIKE '%{escaped}%'")
                    
                    query = f"""
                    SELECT 
                        m.message_id,
                        s.subject as subject_text,
                        m.date_received,
                        sender.address as sender_address,
                        recipient.address as recipient_address
                    FROM messages m
                    JOIN subjects s ON m.subject = s.ROWID
                    LEFT JOIN addresses sender ON m.sender = sender.ROWID
                    LEFT JOIN addresses recipient ON recipient.ROWID = (
                        SELECT address_id FROM recipients 
                        WHERE message_id = m.ROWID 
                        AND type = 0
                        LIMIT 1
                    )
                    WHERE ({' OR '.join(keyword_conditions)})
                    AND m.date_received > {cutoff_timestamp}
                    """
                else:
                    # Legacy database
                    keyword_conditions = []
                    for keyword in batch_keywords:
                        escaped = keyword.replace("'", "''")
                        keyword_conditions.append(f"m.subject LIKE '%{escaped}%'")
                    
                    query = f"""
                    SELECT 
                        m.message_id,
                        m.subject as subject_text,
                        m.date_received,
                        s.address as sender_address,
                        r.address as recipient_address
                    FROM messages m
                    LEFT JOIN addresses s ON m.sender = s.ROWID
                    LEFT JOIN addresses r ON r.ROWID = (
                        SELECT address_id FROM recipients 
                        WHERE message_id = m.ROWID 
                        LIMIT 1
                    )
                    WHERE ({' OR '.join(keyword_conditions)})
                    AND m.date_received > {cutoff_timestamp}
                    """
                
                cursor.execute(query)
                batch_results = cursor.fetchall()
                all_results.extend(batch_results)
                print(f"  ✓ Batch {i//batch_size + 1}: {len(batch_results)} results")
                
            except Exception as e:
                print(f"  ⚠️  Error in batch {i//batch_size + 1}: {str(e)}")
        
        # Get total email count
        cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
        total_emails = cursor.fetchone()[0]
        
        conn.close()
        
        # Remove duplicates
        unique_results = list({r[0]: r for r in all_results}.values())
        
        print(f"\n✅ Found {len(unique_results)} subscription emails")
        
        # Process results
        self._process_results(unique_results)
        
        # Create scan results
        if COMMON_STRUCTURES_AVAILABLE:
            duplicates = self._find_duplicates()
            
            self.scan_results = ScanResults(
                scan_date=scan_start,
                scan_parameters={
                    'days_back': days_back,
                    'keywords_used': len(CORE_KEYWORDS),
                    'database_type': 'normalized' if has_subjects_table else 'legacy',
                    'scanner': 'simple'
                },
                total_emails_scanned=total_emails,
                subscription_emails_found=len(unique_results),
                unique_subscriptions=list(self.subscriptions.values()),
                duplicate_subscriptions=duplicates,
                financial_summary=calculate_financial_summary(
                    list(self.subscriptions.values()), 
                    duplicates
                ),
                scan_metadata={
                    'scanner_version': '2.0',
                    'scanner_name': 'simple_scanner',
                    'database_path': str(self.db_path)
                }
            )
        
        print(f"✅ Identified {len(self.subscriptions)} unique subscriptions")
        
        return self.subscriptions
    
    def _process_results(self, emails: List[tuple]) -> None:
        """Process email results"""
        subscription_map = defaultdict(lambda: {
            'emails': [],
            'accounts': set(),
            'amounts': [],
            'currencies': set(),
            'first_seen': None,
            'last_seen': None,
            'status': 'unknown'
        })
        
        for email in emails:
            message_id, subject, date_received, sender, recipient = email
            
            if not sender:
                continue
                
            # Extract company
            company = self._extract_company(sender)
            if not company:
                continue
            
            # Convert timestamp
            email_date = datetime.fromtimestamp(date_received) if date_received else datetime.now()
            
            # Create email object
            if COMMON_STRUCTURES_AVAILABLE:
                email_obj = SubscriptionEmail(
                    message_id=message_id,
                    subject=subject or '',
                    sender=sender,
                    recipient=recipient or 'unknown',
                    date_received=email_date
                )
                
                # Extract amount
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
            sub['accounts'].add(recipient or 'unknown')
            
            # Update dates
            if not sub['first_seen'] or email_date < sub['first_seen']:
                sub['first_seen'] = email_date
            if not sub['last_seen'] or email_date > sub['last_seen']:
                sub['last_seen'] = email_date
            
            # Simple status detection
            if subject:
                subject_lower = subject.lower()
                if 'cancel' in subject_lower:
                    sub['status'] = 'cancelled'
                elif 'trial' in subject_lower:
                    sub['status'] = 'trial'
                elif any(word in subject_lower for word in ['receipt', 'payment', 'charged']):
                    sub['status'] = 'active'
        
        # Convert to Subscription objects
        if COMMON_STRUCTURES_AVAILABLE:
            for company, data in subscription_map.items():
                # Check if inactive
                days_inactive = (datetime.now() - data['last_seen']).days
                if days_inactive > 180 and data['status'] not in ['cancelled']:
                    data['status'] = 'inactive'
                
                # Calculate average amount
                avg_amount = sum(data['amounts']) / len(data['amounts']) if data['amounts'] else None
                
                self.subscriptions[company] = Subscription(
                    company=company,
                    emails=data['emails'],
                    accounts=data['accounts'],
                    amounts=data['amounts'],
                    currencies=data['currencies'],
                    first_seen=data['first_seen'],
                    last_seen=data['last_seen'],
                    status=data['status'],
                    email_count=len(data['emails']),
                    avg_amount=avg_amount,
                    frequency=None  # Simple scanner doesn't determine frequency
                )
        else:
            self.subscriptions = dict(subscription_map)
    
    def _extract_company(self, sender: str) -> Optional[str]:
        """Simple company extraction"""
        if not sender or '@' not in sender:
            return None
            
        email_lower = sender.lower()
        
        # Remove common prefixes
        for prefix in ['noreply@', 'no-reply@', 'billing@', 'support@']:
            if email_lower.startswith(prefix):
                domain = email_lower.replace(prefix, '')
                company = domain.split('.')[0]
                return company.title()
        
        # Extract from domain
        domain = sender.split('@')[1]
        company = domain.split('.')[0]
        
        # Skip email providers
        if company.lower() in ['gmail', 'yahoo', 'outlook', 'hotmail']:
            return None
            
        return company.title()
    
    def _extract_amount(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Simple amount extraction"""
        if not text:
            return None, None
            
        # Basic patterns
        patterns = [
            (r'\$\s*([\d,]+\.?\d*)', 'USD'),
            (r'USD\s*([\d,]+\.?\d*)', 'USD'),
        ]
        
        for pattern, currency in patterns:
            match = re.search(pattern, text)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if 0.99 <= amount <= 10000:
                        return amount, currency
                except:
                    pass
                    
        return None, None
    
    def _find_duplicates(self) -> List[DuplicateSubscription]:
        """Find duplicate subscriptions"""
        duplicates = []
        
        if not COMMON_STRUCTURES_AVAILABLE:
            return duplicates
        
        for company, sub in self.subscriptions.items():
            if len(sub.accounts) > 1:
                monthly_waste = 0
                if sub.avg_amount:
                    # Assume monthly if no frequency
                    monthly_waste = sub.avg_amount * (len(sub.accounts) - 1)
                
                duplicates.append(DuplicateSubscription(
                    company=company,
                    accounts=list(sub.accounts),
                    monthly_waste=monthly_waste,
                    total_emails=sub.email_count
                ))
        
        return duplicates
    
    def display_results(self) -> None:
        """Display simple results"""
        if not self.subscriptions:
            print("\n📭 No subscriptions found")
            return
        
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            # Show summary
            summary = self.scan_results.get_summary_stats()
            financial = self.scan_results.financial_summary
            
            print(f"\n📊 SUMMARY")
            print("=" * 60)
            print(f"Total subscriptions: {summary['total_subscriptions']}")
            print(f"Duplicate subscriptions: {summary['duplicate_count']}")
            
            if financial['monthly_total'] > 0:
                print(f"\n💰 Estimated monthly total: {format_currency(financial['monthly_total'])}")
                print(f"💰 Estimated annual total: {format_currency(financial['annual_total'])}")
        
        # Show top subscriptions
        sorted_subs = sorted(self.subscriptions.items(), 
                           key=lambda x: x[1].email_count if COMMON_STRUCTURES_AVAILABLE else len(x[1]['emails']), 
                           reverse=True)
        
        print(f"\n📋 TOP SUBSCRIPTIONS")
        print("=" * 60)
        
        for i, (company, sub) in enumerate(sorted_subs[:20], 1):
            if COMMON_STRUCTURES_AVAILABLE:
                print(f"\n{i}. {company}")
                print(f"   📧 {sub.email_count} emails")
                print(f"   👤 {len(sub.accounts)} account(s)")
                if sub.avg_amount:
                    print(f"   💰 ${sub.avg_amount:.2f}")
                print(f"   🚦 Status: {sub.status}")
    
    def export_json(self, filepath: str) -> None:
        """Export results to JSON"""
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            print(f"\n💾 Exporting to {filepath}...")
            self.scan_results.to_json(filepath)
            print(f"✅ Exported scan results to {filepath}")
        else:
            print("⚠️  JSON export requires common_structures.py")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description='Simple subscription scanner with basic detection'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=365,
        help='Number of days to scan back (default: 365)'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        help='Path to export JSON results'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show how many emails would be processed without actually processing them'
    )
    
    args = parser.parse_args()
    
    # Run scanner
    scanner = SimpleSubscriptionScanner()
    
    try:
        # Prompt for years if interactive (not in dry-run mode)
        if not args.quiet and not args.dry_run and sys.stdin.isatty():
            years_input = input("\nHow many years to scan? (default 1): ").strip()
            if years_input:
                try:
                    years = float(years_input)
                    args.days = int(years * 365)
                except:
                    pass
        
        scanner.scan_emails(days_back=args.days, dry_run=args.dry_run)
        
        # Don't display full results or export if dry run
        if args.dry_run:
            return 0
        
        # Display results unless quiet
        if not args.quiet:
            scanner.display_results()
        
        # Export JSON if requested
        if args.output_json:
            scanner.export_json(args.output_json)
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
