#!/usr/bin/env python3
"""
Comprehensive subscription scanner that shows ALL results.
Exports complete analysis to JSON with standardized structure.
Enhanced with fraud detection and proper frequency/amount extraction.
"""

import os
import sqlite3
import re
import json
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
    print("Warning: common_structures.py not found. Using legacy format.")

# Import enhanced detectors
try:
    from enhanced_fraud_detector import EnhancedFraudDetector
    from enhanced_payment_extractor import EnhancedPaymentExtractor
    ENHANCED_DETECTION = True
except ImportError:
    print("Warning: Enhanced detectors not found. Using basic detection.")
    ENHANCED_DETECTION = False

# Comprehensive keywords
SUBSCRIPTION_KEYWORDS = [
    "subscription", "payment", "invoice", "billing", "receipt",
    "renewal", "renew", "recurring", "membership", "charge",
    "monthly", "annual", "yearly", "cancelled", "cancel",
    "trial", "premium", "paid", "plan", "subscribe",
    "charged", "transaction", "purchase", "order"
]


class ComprehensiveSubscriptionScanner:
    """Scanner that shows ALL subscriptions comprehensively"""
    
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
    
    def scan_emails(self, days_back: int = 1825) -> Dict:  # Default 5 years
        """Scan emails and return ALL subscriptions"""
        print(f"🚀 COMPREHENSIVE SUBSCRIPTION SCANNER")
        print("=" * 80)
        print(f"🔍 Scanning {days_back} days ({days_back/365:.1f} years) of email...")
        
        scan_start = datetime.now()
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Check database structure
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='subjects'")
        has_subjects_table = cursor.fetchone() is not None
        
        # Build query
        if has_subjects_table:
            keyword_conditions = []
            for keyword in SUBSCRIPTION_KEYWORDS:
                escaped = keyword.replace("'", "''")
                keyword_conditions.append(f"s.subject LIKE '%{escaped}%'")
            
            query = f"""
            SELECT 
                m.message_id,
                s.subject as subject_text,
                m.date_received,
                sender.address as sender_address,
                '' as recipient_address
            FROM messages m
            JOIN subjects s ON m.subject = s.ROWID
            LEFT JOIN addresses sender ON m.sender = sender.ROWID
            WHERE ({' OR '.join(keyword_conditions)})
            AND m.date_received > {cutoff_timestamp}
            ORDER BY m.date_received DESC
            """
        else:
            # Legacy query for older databases
            keyword_conditions = []
            for keyword in SUBSCRIPTION_KEYWORDS:
                escaped = keyword.replace("'", "''")
                keyword_conditions.append(f"m.subject LIKE '%{escaped}%'")
            
            query = f"""
            SELECT 
                m.message_id,
                m.subject as subject_text,
                m.date_received,
                s.address as sender_address,
                '' as recipient_address
            FROM messages m
            LEFT JOIN addresses s ON m.sender = s.ROWID
            WHERE ({' OR '.join(keyword_conditions)})
            AND m.date_received > {cutoff_timestamp}
            ORDER BY m.date_received DESC
            """
        
        print("   Executing comprehensive query...")
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Try to get recipient information separately (same approach as working scanner)
        recipients_map = defaultdict(list)  # Store list of recipients per message_id
        try:
            if results:
                # 1. Check for 'recipients' and 'addresses' tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('recipients', 'addresses')")
                tables_found = {row[0] for row in cursor.fetchall()}

                if 'recipients' in tables_found and 'addresses' in tables_found:
                    # 2. Get column info for 'recipients' table
                    cursor.execute("PRAGMA table_info(recipients)")
                    recipients_cols_info = {col[1]: col[2].upper() for col in cursor.fetchall()}

                    # 3. Get column info for 'addresses' table
                    cursor.execute("PRAGMA table_info(addresses)")
                    addresses_cols_info = {col[1]: col[2].upper() for col in cursor.fetchall()}

                    # Find relevant columns
                    message_link_col_rec = None
                    for name in ['message', 'message_id', 'messageID', 'messages_id', 'message_rowid']:
                        if name in recipients_cols_info and recipients_cols_info[name] == 'INTEGER':
                            message_link_col_rec = name
                            break
                    
                    address_data_col_rec = None
                    address_data_is_fk = False 
                    for name in ['address', 'address_id', 'addresses_id', 'recipient_address', 'email']:
                        if name in recipients_cols_info:
                            address_data_col_rec = name
                            if recipients_cols_info[name] == 'INTEGER':
                                address_data_is_fk = True
                            break

                    email_text_col_addr = None
                    for name in ['address', 'email', 'email_address', 'full_address']:
                        if name in addresses_cols_info and addresses_cols_info[name] == 'TEXT':
                            email_text_col_addr = name
                            break
                    
                    # Construct and execute query if critical columns are found
                    if message_link_col_rec and address_data_col_rec and (not address_data_is_fk or email_text_col_addr):
                        print(f"   🔍 Fetching recipient details...")
                        
                        # Batch message IDs to avoid overly long SQL queries
                        all_message_ids = [str(r[0]) for r in results]
                        batch_size = 500

                        for i in range(0, len(all_message_ids), batch_size):
                            batch_ids_str = ','.join(all_message_ids[i:i+batch_size])
                            
                            if address_data_is_fk:
                                recipient_query = f"""
                                SELECT DISTINCT r.{message_link_col_rec}, a.{email_text_col_addr}
                                FROM recipients r 
                                JOIN addresses a ON r.{address_data_col_rec} = a.ROWID
                                WHERE r.{message_link_col_rec} IN ({batch_ids_str})
                                """
                            else:
                                recipient_query = f"""
                                SELECT DISTINCT r.{message_link_col_rec}, r.{address_data_col_rec}
                                FROM recipients r
                                WHERE r.{message_link_col_rec} IN ({batch_ids_str})
                                """

                            try:
                                cursor.execute(recipient_query)
                                for row in cursor.fetchall():
                                    msg_id, address_val = row[0], row[1]
                                    if msg_id and address_val:
                                        recipients_map[msg_id].append(str(address_val))
                            except sqlite3.Error as e:
                                print(f"   ⚠️  Error fetching recipients: {e}")
                                break

        except Exception as e:
            print(f"   ⚠️  Error processing recipients: {e}")
        
        # Get total email count
        cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
        total_emails = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   ✅ Found {len(results)} subscription-related emails!")
        print(f"   📊 Total emails in period: {total_emails:,}")
        
        # Process all results
        self._process_results(results, recipients_map)
        
        # Report fraud statistics if enhanced detection is available
        if ENHANCED_DETECTION and hasattr(self, 'fraud_stats'):
            print(f"\n🛡️  Fraud Detection Results:")
            print(f"   Total emails analyzed: {self.fraud_stats['total_analyzed']}")
            print(f"   Fraudulent filtered: {self.fraud_stats['fraudulent_count']}")
            print(f"   Legitimate processed: {self.fraud_stats['legitimate_count']}")
            if self.fraud_stats['fraudulent_count'] > 0:
                print(f"   Fraud rate: {self.fraud_stats['fraudulent_count']/self.fraud_stats['total_analyzed']*100:.1f}%")
        
        # Create comprehensive scan results
        if COMMON_STRUCTURES_AVAILABLE:
            duplicates = self._find_duplicates()
            
            self.scan_results = ScanResults(
                scan_date=scan_start,
                scan_parameters={
                    'days_back': days_back,
                    'keywords_used': len(SUBSCRIPTION_KEYWORDS),
                    'database_type': 'normalized' if has_subjects_table else 'legacy'
                },
                total_emails_scanned=total_emails,
                subscription_emails_found=len(results),
                unique_subscriptions=list(self.subscriptions.values()),
                duplicate_subscriptions=duplicates,
                financial_summary=calculate_financial_summary(
                    list(self.subscriptions.values()), 
                    duplicates
                ),
                scan_metadata={
                    'scanner_version': '2.0',
                    'scanner_name': 'comprehensive_scanner',
                    'database_path': str(self.db_path),
                    'complete_results': True  # Indicates this includes ALL subscriptions
                }
            )
        
        return self.subscriptions
    
    def _process_results(self, emails: List[tuple], recipients_map: Dict[int, List[str]]) -> None:
        """Process all email results with enhanced fraud detection and payment extraction"""
        subscription_map = defaultdict(lambda: {
            'emails': [],
            'accounts': set(),
            'amounts': [],
            'currencies': set(),
            'first_seen': None,
            'last_seen': None,
            'status': 'unknown',
            'subjects': [],  # Keep track of all subjects
            'frequencies': [],  # Track detected frequencies
            'monthly_amounts': [],  # Track calculated monthly equivalents
            'full_senders': set()  # Track full sender information
        })
        
        # Initialize fraud statistics
        self.fraud_stats = {
            'total_analyzed': len(emails),
            'fraudulent_count': 0,
            'legitimate_count': 0,
            'fraud_reasons': defaultdict(int)
        }
        
        for email in emails:
            message_id, subject, date_received, sender, _ = email  # recipient is placeholder
            
            # Get actual recipients from map
            current_recipients = recipients_map.get(message_id, [])
            recipient = current_recipients[0] if current_recipients else 'unknown'
            
            if not sender:
                continue
            
            # Enhanced fraud detection
            if ENHANCED_DETECTION:
                # Extract amount and frequency first
                amount, currency, frequency = EnhancedPaymentExtractor.extract_amount_and_frequency(subject or '')
                
                # Check if likely fraud
                is_fraud, fraud_reasons = EnhancedFraudDetector.is_likely_fraud(
                    sender, subject, amount, frequency
                )
                
                if is_fraud:
                    self.fraud_stats['fraudulent_count'] += 1
                    for reason in fraud_reasons:
                        self.fraud_stats['fraud_reasons'][reason] += 1
                    continue  # Skip fraudulent emails
                
                # Extract legitimate company name
                company, full_sender = EnhancedFraudDetector.extract_legitimate_company_name(sender, subject)
                if not company:
                    self.fraud_stats['fraudulent_count'] += 1
                    continue
                
                self.fraud_stats['legitimate_count'] += 1
            else:
                # Fallback to basic extraction
                company = self._extract_company(sender, subject)
                if not company:
                    continue
                full_sender = sender
                amount, currency = self._extract_amount(subject or '')
                frequency = None
            
            # Convert timestamp
            email_date = datetime.fromtimestamp(date_received) if date_received else datetime.now()
            
            # Store subject for later analysis
            if subject:
                subscription_map[company]['subjects'].append(subject)
            
            # Store full sender information
            subscription_map[company]['full_senders'].add(full_sender)
            
            # Create email object
            if COMMON_STRUCTURES_AVAILABLE:
                email_obj = SubscriptionEmail(
                    message_id=message_id,
                    subject=subject or '',
                    sender=full_sender,  # Use full sender with display name
                    recipient=recipient or 'unknown',
                    date_received=email_date
                )
                
                # Enhanced amount and frequency handling
                if amount:
                    email_obj.amount = amount
                    email_obj.currency = currency
                    subscription_map[company]['amounts'].append(amount)
                    subscription_map[company]['currencies'].add(currency)
                    
                    # Store frequency
                    if frequency:
                        subscription_map[company]['frequencies'].append(frequency)
                        
                        # Calculate monthly equivalent
                        if ENHANCED_DETECTION:
                            monthly_equiv = EnhancedFraudDetector.calculate_monthly_equivalent(amount, frequency)
                            subscription_map[company]['monthly_amounts'].append(monthly_equiv)
                        else:
                            subscription_map[company]['monthly_amounts'].append(amount)
            
            # Update subscription data
            sub = subscription_map[company]
            if COMMON_STRUCTURES_AVAILABLE:
                sub['emails'].append(email_obj)
            # Add all recipient accounts
            if current_recipients:
                sub['accounts'].update(current_recipients)
            else:
                sub['accounts'].add('unknown')
            
            # Update dates
            if not sub['first_seen'] or email_date < sub['first_seen']:
                sub['first_seen'] = email_date
            if not sub['last_seen'] or email_date > sub['last_seen']:
                sub['last_seen'] = email_date
            
            # Determine status
            if subject:
                sub['status'] = self._determine_status(subject, sub['status'])
        
        # Convert to Subscription objects
        if COMMON_STRUCTURES_AVAILABLE:
            for company, data in subscription_map.items():
                # Check if inactive
                days_inactive = (datetime.now() - data['last_seen']).days
                if days_inactive > 180 and data['status'] not in ['cancelled', 'failed']:
                    data['status'] = 'inactive'
                
                # Calculate average amount - use monthly equivalents if available
                if data['monthly_amounts']:
                    avg_amount = sum(data['monthly_amounts']) / len(data['monthly_amounts'])
                elif data['amounts']:
                    avg_amount = sum(data['amounts']) / len(data['amounts'])
                else:
                    avg_amount = None
                
                # Determine frequency - use detected frequencies if available
                if data['frequencies']:
                    # Find most common frequency
                    freq_counts = defaultdict(int)
                    for freq in data['frequencies']:
                        freq_counts[freq] += 1
                    frequency = max(freq_counts, key=freq_counts.get)
                else:
                    frequency = self._determine_frequency(data['subjects'])
                
                # Create subscription with enhanced data
                sub = Subscription(
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
                    frequency=frequency
                )
                
                # Add sender information as metadata
                sub.metadata = {
                    'full_senders': list(data['full_senders']),
                    'detected_frequencies': data['frequencies'],
                    'monthly_equivalents': data['monthly_amounts']
                }
                
                self.subscriptions[company] = sub
        else:
            # Legacy format
            self.subscriptions = dict(subscription_map)
    
    def _extract_company(self, sender: str, subject: str) -> Optional[str]:
        """Extract company name"""
        if not sender or '@' not in sender:
            return None
        
        # Try subject-based extraction first
        if subject:
            patterns = [
                r'your\s+(\w+)\s+(?:subscription|membership)',
                r'(\w+)\s+(?:receipt|invoice|payment)',
                r'thank\s+you\s+for\s+(?:subscribing|joining)\s+(?:to\s+)?(\w+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, subject, re.IGNORECASE)
                if match:
                    company = match.group(1)
                    if company.lower() not in ['your', 'the', 'a', 'an']:
                        return company.title()
        
        # Sender-based extraction
        email_lower = sender.lower()
        
        # Remove prefixes
        for prefix in ['noreply@', 'no-reply@', 'billing@', 'support@', 
                      'notification@', 'team@', 'hello@']:
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
        """Extract amount and currency"""
        if not text:
            return None, None
        
        patterns = [
            (r'\$\s*([\d,]+\.?\d*)', 'USD'),
            (r'USD\s*([\d,]+\.?\d*)', 'USD'),
            (r'£\s*([\d,]+\.?\d*)', 'GBP'),
            (r'€\s*([\d,]+\.?\d*)', 'EUR'),
            (r'total:?\s*\$?\s*([\d,]+\.?\d*)', 'USD'),
            (r'amount:?\s*\$?\s*([\d,]+\.?\d*)', 'USD'),
        ]
        
        for pattern, currency in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    amount = float(match.group(1).replace(',', ''))
                    if 0.99 <= amount <= 10000:
                        return amount, currency
                except:
                    pass
                    
        return None, None
    
    def _determine_status(self, subject: str, current_status: str) -> str:
        """Determine subscription status"""
        subject_lower = subject.lower()
        
        # Status keywords
        if any(word in subject_lower for word in ['cancelled', 'canceled', 'terminated']):
            return 'cancelled'
        elif any(word in subject_lower for word in ['failed', 'declined', 'unsuccessful']):
            return 'failed'
        elif any(word in subject_lower for word in ['trial', 'free trial']):
            return 'trial'
        elif any(word in subject_lower for word in ['active', 'confirmed', 'receipt']):
            return 'active'
        elif any(word in subject_lower for word in ['paused', 'suspended']):
            return 'paused'
            
        return current_status
    
    def _determine_frequency(self, subjects: List[str]) -> Optional[str]:
        """Determine frequency from subject lines"""
        freq_counts = defaultdict(int)
        
        for subject in subjects:
            subject_lower = subject.lower()
            if any(term in subject_lower for term in ['annual', 'yearly', 'year']):
                freq_counts['annual'] += 1
            elif any(term in subject_lower for term in ['monthly', 'month']):
                freq_counts['monthly'] += 1
            elif any(term in subject_lower for term in ['weekly', 'week']):
                freq_counts['weekly'] += 1
            elif any(term in subject_lower for term in ['quarterly', 'quarter']):
                freq_counts['quarterly'] += 1
        
        if freq_counts:
            return max(freq_counts, key=freq_counts.get)
        return None
    
    def _find_duplicates(self) -> List[DuplicateSubscription]:
        """Find duplicate subscriptions"""
        duplicates = []
        
        if not COMMON_STRUCTURES_AVAILABLE:
            return duplicates
        
        for company, sub in self.subscriptions.items():
            if len(sub.accounts) > 1:
                monthly_waste = 0
                if sub.avg_amount:
                    if sub.frequency == 'monthly':
                        monthly_waste = sub.avg_amount * (len(sub.accounts) - 1)
                    elif sub.frequency == 'annual':
                        monthly_waste = (sub.avg_amount / 12) * (len(sub.accounts) - 1)
                    else:
                        monthly_waste = sub.avg_amount * (len(sub.accounts) - 1)
                
                duplicates.append(DuplicateSubscription(
                    company=company,
                    accounts=list(sub.accounts),
                    monthly_waste=monthly_waste,
                    total_emails=sub.email_count
                ))
        
        return duplicates
    
    def display_comprehensive_results(self) -> None:
        """Display ALL subscriptions comprehensively"""
        if not self.subscriptions:
            print("\n📭 No subscriptions found")
            return
        
        print(f"\n✅ COMPREHENSIVE RESULTS: {len(self.subscriptions)} subscriptions")
        print("=" * 80)
        
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            summary = self.scan_results.get_summary_stats()
            financial = self.scan_results.financial_summary
            
            # Overall statistics
            print(f"\n📊 OVERALL STATISTICS")
            print(f"   Total subscriptions: {summary['total_subscriptions']}")
            print(f"   Active: {summary['active_subscriptions']}")
            print(f"   Inactive: {summary['inactive_subscriptions']}")
            print(f"   Accounts involved: {summary['accounts_involved']}")
            print(f"   Duplicates found: {summary['duplicate_count']}")
            
            # Financial overview
            print(f"\n💰 FINANCIAL OVERVIEW")
            print(f"   Monthly total: {format_currency(financial['monthly_total'])}")
            print(f"   Annual total: {format_currency(financial['annual_total'])}")
            print(f"   Duplicate waste (monthly): {format_currency(financial['duplicate_monthly_waste'])}")
            print(f"   Potential annual savings: {format_currency(financial['potential_annual_savings'])}")
        
        # Categorize subscriptions
        active = []
        inactive = []
        cancelled = []
        failed = []
        trial = []
        
        for company, sub in self.subscriptions.items():
            if sub.status == 'active':
                active.append((company, sub))
            elif sub.status == 'inactive':
                inactive.append((company, sub))
            elif sub.status == 'cancelled':
                cancelled.append((company, sub))
            elif sub.status == 'failed':
                failed.append((company, sub))
            elif sub.status == 'trial':
                trial.append((company, sub))
            else:
                active.append((company, sub))  # Default to active if unknown
        
        # Display by category
        categories = [
            ("🟢 ACTIVE SUBSCRIPTIONS", active),
            ("🟡 INACTIVE SUBSCRIPTIONS", inactive),
            ("🔴 FAILED PAYMENTS", failed),
            ("🆓 TRIAL SUBSCRIPTIONS", trial),
            ("⚫ CANCELLED SUBSCRIPTIONS", cancelled)
        ]
        
        for category_name, subs in categories:
            if subs:
                print(f"\n{category_name} ({len(subs)})")
                print("-" * 80)
                
                # Sort by email count within category
                for company, sub in sorted(subs, key=lambda x: x[1].email_count, reverse=True):
                    print(f"\n• {company}")
                    print(f"  📧 Emails: {sub.email_count}")
                    print(f"  👤 Accounts: {', '.join(list(sub.accounts)[:3])}")
                    
                    # Show sender information if available
                    if hasattr(sub, 'metadata') and 'full_senders' in sub.metadata:
                        senders = sub.metadata['full_senders']
                        if senders:
                            print(f"  📨 From: {list(senders)[0]}")
                    
                    if sub.avg_amount:
                        currency = list(sub.currencies)[0] if sub.currencies else 'USD'
                        print(f"  💰 Amount: {format_currency(sub.avg_amount, currency)}", end='')
                        if sub.frequency:
                            print(f" ({sub.frequency})", end='')
                            # Show original amount if different from monthly
                            if hasattr(sub, 'metadata') and sub.amounts and sub.frequency == 'annual':
                                orig_amt = sub.amounts[-1] if sub.amounts else None
                                if orig_amt:
                                    print(f" [${orig_amt:.2f}/year]")
                                else:
                                    print()
                            else:
                                print()
                        else:
                            print()
                    
                    days_since = (datetime.now() - sub.last_seen).days
                    print(f"  📅 Last seen: {days_since} days ago")
                    
                    if sub.emails and sub.emails[-1].subject:
                        print(f"  📝 Recent: {sub.emails[-1].subject[:50]}...")
        
        # Show duplicates
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results.duplicate_subscriptions:
            print(f"\n⚠️  DUPLICATE SUBSCRIPTIONS ({len(self.scan_results.duplicate_subscriptions)})")
            print("-" * 80)
            
            for dup in sorted(self.scan_results.duplicate_subscriptions, 
                            key=lambda x: x.monthly_waste, reverse=True):
                print(f"\n• {dup.company}")
                print(f"  On {len(dup.accounts)} accounts: {', '.join(dup.accounts)}")
                if dup.monthly_waste > 0:
                    print(f"  💸 Monthly waste: {format_currency(dup.monthly_waste)}")
    
    def export_json(self, filepath: Optional[str] = None) -> str:
        """Export comprehensive results to JSON"""
        if not filepath:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"subscriptions_comprehensive_{timestamp}.json"
        
        if COMMON_STRUCTURES_AVAILABLE and self.scan_results:
            print(f"\n💾 Exporting comprehensive results to {filepath}...")
            self.scan_results.to_json(filepath)
            print(f"✅ Exported all {len(self.subscriptions)} subscriptions to {filepath}")
            return filepath
        else:
            # Legacy export
            data = {
                'scan_date': datetime.now().isoformat(),
                'total_subscriptions': len(self.subscriptions),
                'subscriptions': self.subscriptions
            }
            
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            print(f"✅ Exported to {filepath} (legacy format)")
            return filepath


def main():
    """Main function with argument parsing"""
    parser = argparse.ArgumentParser(
        description='Comprehensive subscription scanner showing ALL results'
    )
    parser.add_argument(
        '--days', 
        type=int, 
        default=1825,  # 5 years
        help='Number of days to scan back (default: 1825 = 5 years)'
    )
    parser.add_argument(
        '--output-json',
        type=str,
        help='Path to export JSON results (default: auto-generated)'
    )
    parser.add_argument(
        '--quiet',
        action='store_true',
        help='Suppress console output (useful with --output-json)'
    )
    
    args = parser.parse_args()
    
    # Run scanner
    scanner = ComprehensiveSubscriptionScanner()
    
    try:
        scanner.scan_emails(days_back=args.days)
        
        # Display comprehensive results unless quiet
        if not args.quiet:
            scanner.display_comprehensive_results()
        
        # Always export JSON for comprehensive scanner
        output_path = args.output_json or None
        exported_file = scanner.export_json(output_path)
        
        if not args.quiet:
            print(f"\n📊 Full details saved to: {exported_file}")
            print("   Open this file to see complete subscription data")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
