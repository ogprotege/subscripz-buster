#!/usr/bin/env python3
"""
Fixed advanced subscription scanner - NO recipient queries
Uses 100+ keywords to find all subscription-related emails.
"""

import os
import sqlite3
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
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
    print("Note: common_structures.py not found. JSON export will be limited.")

# Comprehensive subscription keywords
SUBSCRIPTION_KEYWORDS = [
    # Payment terms
    "invoice", "billing", "bill", "payment", "charge", "charged",
    "receipt", "transaction", "purchase", "order", "checkout",
    "payment received", "payment confirmed", "payment processed",
    "payment successful", "payment failed", "payment declined",
    "payment due", "amount due", "balance due", "total due",
    
    # Subscription terms
    "subscription", "membership", "member", "premium", "pro",
    "plus", "unlimited", "subscribe", "subscribed", "subscriber",
    "plan", "tier", "package", "account", "service",
    
    # Renewal terms
    "renew", "renewal", "renewed", "renewing", "auto-renew",
    "automatic renewal", "recurring", "recur", "monthly",
    "annually", "yearly", "weekly", "quarterly",
    
    # Status terms
    "active", "activated", "confirmed", "approved", "processed",
    "cancelled", "canceled", "expired", "suspended", "terminated",
    "ended", "inactive", "paused", "stopped", "discontinued",
    
    # Trial terms
    "trial", "free trial", "trial period", "trial ends",
    "trial ending", "trial expired", "convert", "upgrade",
    
    # Financial terms
    "price", "cost", "fee", "rate", "total", "subtotal",
    "tax", "refund", "credit", "debit", "discount",
    "promo", "offer", "deal", "save", "savings",
    
    # Action terms
    "update payment", "add payment", "payment method",
    "card ending", "expires", "expiration", "update billing",
    "verify payment", "confirm payment", "authorize",
    
    # Company-specific terms
    "your spotify", "your netflix", "your apple", "your amazon",
    "your subscription", "your membership", "your account",
    "your plan", "your service", "thank you for subscribing",
    "welcome to", "thanks for joining", "you're all set"
]

# Spam patterns to filter out
SPAM_PATTERNS = [
    r'viagra', r'cialis', r'pharmacy', r'pills', r'medication',
    r'casino', r'lottery', r'winner', r'claim your', r'act now',
    r'limited time', r'urgent', r'click here', r'unsubscribe',
    r'hot singles', r'dating', r'meet women', r'enlargement'
]


class FixedAdvancedScanner:
    """Advanced scanner without recipient queries"""
    
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
    
    def _is_spam(self, subject: str, sender: str) -> bool:
        """Check if email is likely spam"""
        text = f"{subject} {sender}".lower()
        return any(re.search(pattern, text) for pattern in SPAM_PATTERNS)
    
    def scan_emails(self, days_back: int = 7300, dry_run: bool = False) -> Dict:
        """Scan emails with advanced filtering"""
        print(f"🚀 Advanced Subscription Scanner")
        print("=" * 60)
        print(f"🔍 Scanning {days_back} days ({days_back/365:.1f} years) of email history...")
        
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
            
            # Process keywords in batches
            batch_size = 15
            for i in range(0, len(SUBSCRIPTION_KEYWORDS), batch_size):
                batch_keywords = SUBSCRIPTION_KEYWORDS[i:i + batch_size]
                
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
                    print(f"   ✓ Batch {i//batch_size + 1}: {batch_count} emails")
                except Exception as e:
                    print(f"   ⚠️  Error counting batch {i//batch_size + 1}: {str(e)}")
            
            # Get total email count
            cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
            total_emails = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"\n🔍 DRY RUN RESULTS:")
            print(f"   Total emails in period: {total_emails:,}")
            print(f"   Subscription-related emails: ~{total_count:,}")
            print(f"   Percentage: ~{(total_count/total_emails*100):.1f}%" if total_emails > 0 else "N/A")
            print(f"\n💡 Run without --dry-run to process these emails")
            print(f"   Note: Actual count may be lower due to duplicate removal")
            
            return {}
        
        # Process keywords in batches to avoid SQL limits
        batch_size = 15
        all_results = []
        
        print(f"   Processing {len(SUBSCRIPTION_KEYWORDS)} keywords...")
        
        for i in range(0, len(SUBSCRIPTION_KEYWORDS), batch_size):
            batch_keywords = SUBSCRIPTION_KEYWORDS[i:i + batch_size]
            
            if has_subjects_table:
                # Normalized database - NO RECIPIENT JOINS
                keyword_conditions = []
                for keyword in batch_keywords:
                    escaped = keyword.replace("'", "''")
                    keyword_conditions.append(f"LOWER(s.subject) LIKE LOWER('%{escaped}%')")
                
                query = f"""
                SELECT DISTINCT
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
                LIMIT 5000
                """
            else:
                # Legacy database
                keyword_conditions = []
                for keyword in batch_keywords:
                    escaped = keyword.replace("'", "''")
                    keyword_conditions.append(f"LOWER(m.subject) LIKE LOWER('%{escaped}%')")
                
                query = f"""
                SELECT DISTINCT
                    m.message_id,
                    m.subject as subject_text,
                    m.date_received,
                    s.address as sender_address
                FROM messages m
                LEFT JOIN addresses s ON m.sender = s.ROWID
                WHERE ({' OR '.join(keyword_conditions)})
                AND m.date_received > {cutoff_timestamp}
                ORDER BY m.date_received DESC
                LIMIT 5000
                """
            
            try:
                cursor.execute(query)
                batch_results = cursor.fetchall()
                all_results.extend(batch_results)
                print(f"   ✓ Batch {i//batch_size + 1}: {len(batch_results)} results")
            except Exception as e:
                print(f"   ⚠️  Error in batch {i//batch_size + 1}: {str(e)}")
        
        # Remove duplicates
        unique_results = list({r[0]: r for r in all_results}.values())
        
        # Filter out spam
        filtered_results = []
        spam_count = 0
        
        for result in unique_results:
            message_id, subject, date_received, sender = result
            if not self._is_spam(subject or '', sender or ''):
                filtered_results.append(result)
            else:
                spam_count += 1
        
        # Get total email count
        cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
        total_emails = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"\n✅ Found {len(all_results)} subscription emails")
        print(f"✅ Filtered {spam_count} spam emails")
        print(f"✅ Processing {len(filtered_results)} legitimate subscription emails")
        
        # Process results
        self._process_results(filtered_results)
        
        # Create scan results
        if COMMON_STRUCTURES_AVAILABLE:
            duplicates = []  # No duplicates without recipient info
            
            self.scan_results = ScanResults(
                scan_date=scan_start,
                scan_parameters={
                    'days_back': days_back,
                    'keywords_used': len(SUBSCRIPTION_KEYWORDS),
                    'database_type': 'normalized' if has_subjects_table else 'legacy',
                    'spam_filtered': spam_count
                },
                total_emails_scanned=total_emails,
                subscription_emails_found=len(filtered_results),
                unique_subscriptions=list(self.subscriptions.values()),
                duplicate_subscriptions=duplicates,
                financial_summary=calculate_financial_summary(
                    list(self.subscriptions.values()), 
                    duplicates
                ),
                scan_metadata={
                    'scanner_version': '2.2',
                    'scanner_name': 'fixed_advanced_scanner',
                    'database_path': str(self.db_path),
                    'spam_filtered': spam_count
                }
            )
        
        return self.subscriptions
    
    def _process_results(self, emails: List[tuple]) -> None:
        """Process email results with advanced categorization"""
        subscription_map = defaultdict(lambda: {
            'emails': [],
            'sender_domains': set(),  # Track sender domains instead of recipients
            'amounts': [],
            'currencies': set(),
            'first_seen': None,
            'last_seen': None,
            'status': 'unknown',
            'payment_methods': set(),
            'frequencies': []
        })
        
        for email in emails:
            message_id, subject, date_received, sender = email
            
            if not sender:
                continue
                
            # Extract company name
            company = self._extract_company_advanced(sender, subject)
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
                    recipient='unknown',  # No recipient info
                    date_received=email_date
                )
                
                # Extract financial information
                amount, currency = self._extract_amount_advanced(subject or '')
                if amount:
                    email_obj.amount = amount
                    email_obj.currency = currency
                    subscription_map[company]['amounts'].append(amount)
                    subscription_map[company]['currencies'].add(currency)
                
                # Extract payment method
                payment_method = self._extract_payment_method(subject or '')
                if payment_method:
                    subscription_map[company]['payment_methods'].add(payment_method)
                
                # Extract frequency
                frequency = self._extract_frequency(subject or '')
                if frequency:
                    subscription_map[company]['frequencies'].append(frequency)
            
            # Update subscription data
            sub = subscription_map[company]
            if COMMON_STRUCTURES_AVAILABLE:
                sub['emails'].append(email_obj)
            
            # Track sender domain
            if '@' in sender:
                domain = sender.split('@')[1]
                sub['sender_domains'].add(domain)
            
            # Update dates
            if not sub['first_seen'] or email_date < sub['first_seen']:
                sub['first_seen'] = email_date
            if not sub['last_seen'] or email_date > sub['last_seen']:
                sub['last_seen'] = email_date
            
            # Advanced status detection
            sub['status'] = self._determine_status(subject or '', sub['status'])
        
        # Convert to Subscription objects
        if COMMON_STRUCTURES_AVAILABLE:
            for company, data in subscription_map.items():
                # Determine final status
                days_inactive = (datetime.now() - data['last_seen']).days
                if days_inactive > 180 and data['status'] not in ['cancelled', 'failed']:
                    data['status'] = 'inactive'
                
                # Calculate average amount
                avg_amount = sum(data['amounts']) / len(data['amounts']) if data['amounts'] else None
                
                # Determine most common frequency
                if data['frequencies']:
                    freq_counts = defaultdict(int)
                    for freq in data['frequencies']:
                        freq_counts[freq] += 1
                    frequency = max(freq_counts, key=freq_counts.get)
                else:
                    frequency = None
                
                self.subscriptions[company] = Subscription(
                    company=company,
                    emails=data['emails'],
                    accounts=set(['unknown']),  # No recipient info
                    amounts=data['amounts'],
                    currencies=data['currencies'],
                    first_seen=data['first_seen'],
                    last_seen=data['last_seen'],
                    status=data['status'],
                    email_count=len(data['emails']),
                    avg_amount=avg_amount,
                    frequency=frequency
                )
    
    def _extract_company_advanced(self, sender: str, subject: str) -> Optional[str]:
        """Advanced company extraction using sender and subject"""
        if not sender or '@' not in sender:
            return None
        
        # Try to extract from subject first (often has company name)
        if subject:
            # Look for patterns like "Your Netflix subscription"
            patterns = [
                r'your\s+(\w+)\s+(?:subscription|membership|account)',
                r'(\w+)\s+(?:receipt|invoice|payment)',
                r'welcome\s+to\s+(\w+)',
                r'(\w+)\s+order\s+confirmation'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    company = match.group(1)
                    if company.lower() not in ['your', 'the', 'a', 'an']:
                        return company.title()
        
        # Fall back to sender-based extraction
        email_lower = sender.lower()
        
        # Remove common prefixes
        for prefix in ['noreply@', 'no-reply@', 'billing@', 'support@', 'notification@', 
                      'receipts@', 'payments@', 'invoice@', 'team@', 'hello@']:
            if email_lower.startswith(prefix):
                domain = email_lower.replace(prefix, '')
                company = domain.split('.')[0]
                return self._clean_company_name(company)
        
        # Extract from domain
        domain = sender.split('@')[1]
        company = domain.split('.')[0]
        
        # Skip email providers
        if company.lower() in ['gmail', 'yahoo', 'outlook', 'hotmail', 'aol', 'icloud']:
            return None
            
        return self._clean_company_name(company)
    
    def _clean_company_name(self, company: str) -> str:
        """Clean and standardize company names"""
        # Common replacements
        replacements = {
            'amazonses': 'Amazon',
            'amazonsns': 'Amazon',
            'msft': 'Microsoft',
            'goog': 'Google',
            'fb': 'Facebook',
            'paypalobjects': 'PayPal'
        }
        
        company_lower = company.lower()
        for old, new in replacements.items():
            if old in company_lower:
                return new
                
        return company.title()
    
    def _extract_amount_advanced(self, text: str) -> Tuple[Optional[float], Optional[str]]:
        """Advanced amount extraction with multiple patterns"""
        if not text:
            return None, None
        
        # Extended currency patterns
        patterns = [
            # Standard formats
            (r'\$\s*([\d,]+\.?\d*)', 'USD'),
            (r'USD\s*([\d,]+\.?\d*)', 'USD'),
            (r'([\d,]+\.?\d*)\s*USD', 'USD'),
            (r'£\s*([\d,]+\.?\d*)', 'GBP'),
            (r'€\s*([\d,]+\.?\d*)', 'EUR'),
            (r'¥\s*([\d,]+\.?\d*)', 'JPY'),
            (r'C\$\s*([\d,]+\.?\d*)', 'CAD'),
            (r'A\$\s*([\d,]+\.?\d*)', 'AUD'),
            
            # Text-based patterns
            (r'amount:?\s*\$?\s*([\d,]+\.?\d*)', 'USD'),
            (r'total:?\s*\$?\s*([\d,]+\.?\d*)', 'USD'),
            (r'charged:?\s*\$?\s*([\d,]+\.?\d*)', 'USD'),
            (r'price:?\s*\$?\s*([\d,]+\.?\d*)', 'USD'),
            (r'you\s+paid:?\s*\$?\s*([\d,]+\.?\d*)', 'USD'),
        ]
        
        for pattern, currency in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount_str = match.group(1).replace(',', '')
                    amount = float(amount_str)
                    # Sanity check - subscriptions typically between $0.99 and $10,000
                    if 0.99 <= amount <= 10000:
                        return amount, currency
                except:
                    pass
                    
        return None, None
    
    def _extract_payment_method(self, text: str) -> Optional[str]:
        """Extract payment method from text"""
        methods = {
            'visa': 'Visa',
            'mastercard': 'Mastercard',
            'amex': 'American Express',
            'american express': 'American Express',
            'discover': 'Discover',
            'paypal': 'PayPal',
            'apple pay': 'Apple Pay',
            'google pay': 'Google Pay',
            'card ending': 'Credit Card',
            'credit card': 'Credit Card',
            'debit card': 'Debit Card',
            'bank account': 'Bank Account',
            'ach': 'ACH Transfer'
        }
        
        text_lower = text.lower()
        for key, value in methods.items():
            if key in text_lower:
                return value
                
        return None
    
    def _extract_frequency(self, text: str) -> Optional[str]:
        """Extract subscription frequency from text"""
        text_lower = text.lower()
        
        # Check for specific frequency terms
        if any(term in text_lower for term in ['annual', 'yearly', 'year', '/yr', 'per year']):
            return 'annual'
        elif any(term in text_lower for term in ['monthly', 'month', '/mo', 'per month']):
            return 'monthly'
        elif any(term in text_lower for term in ['weekly', 'week', '/wk', 'per week']):
            return 'weekly'
        elif any(term in text_lower for term in ['quarterly', 'quarter', '3 months']):
            return 'quarterly'
        elif any(term in text_lower for term in ['daily', 'day', '/day']):
            return 'daily'
            
        return None
    
    def _determine_status(self, subject: str, current_status: str) -> str:
        """Determine subscription status from subject line"""
        subject_lower = subject.lower()
        
        # Priority order: cancelled > failed > trial > active > unknown
        if any(term in subject_lower for term in ['cancelled', 'canceled', 'terminated', 
                                                   'ended', 'expired', 'closed']):
            return 'cancelled'
        elif any(term in subject_lower for term in ['failed', 'declined', 'unsuccessful',
                                                     'could not process', 'payment issue']):
            return 'failed'
        elif any(term in subject_lower for term in ['past due', 'overdue', 'late',
                                                     'missed payment']):
            return 'past_due'
        elif any(term in subject_lower for term in ['trial', 'free trial', 'trial period']):
            return 'trial'
        elif any(term in subject_lower for term in ['active', 'confirmed', 'successful',
                                                     'renewed', 'thank you', 'receipt']):
            return 'active'
        elif any(term in subject_lower for term in ['paused', 'on hold', 'suspended']):
            return 'paused'
            
        return current_status  # Keep existing status if no new information
    
    def display_results(self, show_all: bool = False) -> None:
        """Display comprehensive results"""
        if not self.subscriptions:
            print("\n📭 No subscriptions found")
            return
        
        print(f"\n✅ Identified {len(self.subscriptions)} unique subscriptions")
        
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            # Show summary statistics
            summary = self.scan_results.get_summary_stats()
            financial = self.scan_results.financial_summary
            
            print(f"\n📊 COMPREHENSIVE ANALYSIS")
            print("=" * 80)
            
            # Status breakdown
            print(f"\n📈 Status Breakdown:")
            status_counts = defaultdict(int)
            for sub in self.subscriptions.values():
                status_counts[sub.status] += 1
            
            for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
                print(f"   {status.title()}: {count}")
            
            # Financial summary
            print(f"\n💰 Financial Summary:")
            print(f"   Monthly total: {format_currency(financial['monthly_total'])}")
            print(f"   Annual total: {format_currency(financial['annual_total'])}")
        
        # Show subscriptions
        sorted_subs = sorted(self.subscriptions.items(), 
                           key=lambda x: x[1].email_count, 
                           reverse=True)
        
        limit = len(sorted_subs) if show_all else min(25, len(sorted_subs))
        
        print(f"\n📋 SUBSCRIPTIONS (showing {limit} of {len(sorted_subs)})")
        print("=" * 80)
        
        for i, (company, sub) in enumerate(sorted_subs[:limit], 1):
            print(f"\n{i}. {company}")
            print(f"   📧 {sub.email_count} emails")
            
            if sub.avg_amount:
                currency = list(sub.currencies)[0] if sub.currencies else 'USD'
                print(f"   💰 {format_currency(sub.avg_amount, currency)}", end='')
                if sub.frequency:
                    print(f" ({sub.frequency})")
                else:
                    print()
            
            print(f"   📅 Active: {sub.first_seen.strftime('%Y-%m-%d')} to {sub.last_seen.strftime('%Y-%m-%d')}")
            
            days_inactive = (datetime.now() - sub.last_seen).days
            if days_inactive > 30:
                print(f"   ⏰ Last email: {days_inactive} days ago")
            
            print(f"   🚦 Status: {sub.status}")
            
            if sub.emails and sub.emails[-1].subject:
                print(f"   📝 Recent: {sub.emails[-1].subject[:60]}...")
    
    def export_json(self, filepath: str) -> None:
        """Export results to JSON file"""
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            print(f"\n💾 Exporting to {filepath}...")
            self.scan_results.to_json(filepath)
            print(f"✅ Exported comprehensive scan results to {filepath}")
        else:
            print("⚠️  JSON export requires common_structures.py")


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Fixed advanced subscription scanner'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=7300,  # 20 years
        help='Number of days to scan back (default: 7300 = 20 years)'
    )
    parser.add_argument(
        '--show-all',
        action='store_true',
        help='Show all subscriptions, not just top 25'
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
    scanner = FixedAdvancedScanner()
    
    try:
        scanner.scan_emails(days_back=args.days, dry_run=args.dry_run)
        
        # Don't display full results or export if dry run
        if args.dry_run:
            return 0
        
        # Display results unless quiet mode
        if not args.quiet:
            scanner.display_results(show_all=args.show_all)
        
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
