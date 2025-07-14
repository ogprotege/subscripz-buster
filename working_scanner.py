#!/usr/bin/env python3
"""
Working subscription scanner with consistent JSON output support.
This scanner has been tested and works with normalized Apple Mail databases.
FIXED: Corrected recipients table query
"""

import os
import sqlite3
import re
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict
from payment_extractor import PaymentExtractor

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

# Known subscription services
KNOWN_SERVICES = [
    "netflix", "spotify", "apple", "google", "amazon", "hulu",
    "disney", "hbo", "paramount", "peacock", "youtube", "adobe",
    "microsoft", "dropbox", "evernote", "notion", "slack", "zoom",
    "linkedin", "medium", "substack", "patreon", "onlyfans"
]


class WorkingSubscriptionScanner:
    """Scanner that works with normalized Apple Mail databases"""
    
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
        
        # Full query
        if has_subjects_table:
            # Normalized database query - FIXED recipient join
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
            # Legacy database query
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
        
        print("   Executing query...")
        cursor.execute(query)
        results = cursor.fetchall()
        
        # Try to get recipient information separately (if table structure allows)
        recipients_map = defaultdict(list)  # Store list of recipients per message_id
        try:
            if results:
                # 1. Check for 'recipients' and 'addresses' tables
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('recipients', 'addresses')")
                tables_found = {row[0] for row in cursor.fetchall()}

                if 'recipients' not in tables_found or 'addresses' not in tables_found:
                    print("   ⚠️  'recipients' or 'addresses' table not found. Skipping recipient details.")
                else:
                    # 2. Get column info for 'recipients' table
                    cursor.execute("PRAGMA table_info(recipients)")
                    recipients_cols_info = {col[1]: col[2].upper() for col in cursor.fetchall()}  # name: TYPE

                    # 3. Get column info for 'addresses' table
                    cursor.execute("PRAGMA table_info(addresses)")
                    addresses_cols_info = {col[1]: col[2].upper() for col in cursor.fetchall()}  # name: TYPE

                    # --- Heuristics to find relevant columns ---
                    # For recipients table:
                    #   - message_link_col: links to messages.ROWID (likely INTEGER)
                    #   - address_data_col: either a FK to addresses.ROWID (INTEGER) or direct email (TEXT)
                    
                    message_link_col_rec = None
                    # Common names for message link in 'recipients'
                    for name in ['message', 'message_id', 'messageID', 'messages_id', 'message_rowid']:
                        if name in recipients_cols_info and recipients_cols_info[name] == 'INTEGER':
                            message_link_col_rec = name
                            break
                    
                    address_data_col_rec = None
                    address_data_is_fk = False 
                    # Common names for address link/data in 'recipients'
                    for name in ['address', 'address_id', 'addresses_id', 'recipient_address', 'email']:
                        if name in recipients_cols_info:
                            address_data_col_rec = name
                            if recipients_cols_info[name] == 'INTEGER':
                                address_data_is_fk = True
                            break  # Take the first likely candidate

                    # For addresses table:
                    #   - email_text_col: contains the actual email string (likely TEXT)
                    email_text_col_addr = None
                    for name in ['address', 'email', 'email_address', 'full_address']:
                        if name in addresses_cols_info and addresses_cols_info[name] == 'TEXT':
                            email_text_col_addr = name
                            break
                    
                    # --- Construct and execute query if critical columns are found ---
                    if message_link_col_rec and address_data_col_rec and (not address_data_is_fk or email_text_col_addr):
                        print(f"   🔍 Attempting to fetch recipient details (message_link='{message_link_col_rec}', address_data='{address_data_col_rec}', is_fk='{address_data_is_fk}', email_text_addr='{email_text_col_addr}')...")
                        
                        recipient_query_parts = []
                        if address_data_is_fk:
                            # Need to join recipients with addresses
                            recipient_query_parts.append(f"SELECT DISTINCT r.{message_link_col_rec}, a.{email_text_col_addr}")
                            recipient_query_parts.append(f"FROM recipients r JOIN addresses a ON r.{address_data_col_rec} = a.ROWID")
                        else:
                            # Address is directly in recipients table
                            recipient_query_parts.append(f"SELECT DISTINCT r.{message_link_col_rec}, r.{address_data_col_rec}")
                            recipient_query_parts.append(f"FROM recipients r")
                        
                        # Assuming 'type = 0' is for 'To' recipients, adjust if different
                        # This 'type' column also needs to be dynamically checked or assumed with caution
                        type_col_rec = None
                        for name in ['type', 'recipient_type', 'kind']:
                             if name in recipients_cols_info and recipients_cols_info[name] == 'INTEGER':
                                type_col_rec = name
                                break
                        
                        if type_col_rec:
                            recipient_query_parts.append(f"WHERE r.{type_col_rec} = 0")  # Common value for 'To'
                        else:
                            print(f"   ⚠️  Could not identify recipient type column. Querying all recipient types.")

                        # Batch message IDs to avoid overly long SQL queries
                        all_message_ids_from_results = [str(r[0]) for r in results]
                        batch_size = 500  # SQLite has a variable limit, 500 is generally safe

                        for i in range(0, len(all_message_ids_from_results), batch_size):
                            batch_ids_str = ','.join(all_message_ids_from_results[i:i+batch_size])
                            
                            current_where_clause = f"r.{message_link_col_rec} IN ({batch_ids_str})"
                            if type_col_rec:  # Already have a WHERE clause
                                final_recipient_query = f"{' '.join(recipient_query_parts)} AND {current_where_clause}"
                            else:  # No WHERE clause yet
                                final_recipient_query = f"{' '.join(recipient_query_parts)} WHERE {current_where_clause}"

                            try:
                                # print(f"DEBUG: Recipient Query: {final_recipient_query}")  # Uncomment for debugging
                                cursor.execute(final_recipient_query)
                                for row in cursor.fetchall():
                                    msg_id, address_val = row[0], row[1]
                                    if msg_id and address_val:
                                        recipients_map[msg_id].append(str(address_val))
                            except sqlite3.Error as e_query:
                                print(f"   ⚠️  Error executing recipient batch query: {e_query}. Some recipient details may be missed.")
                                # Potentially log final_recipient_query here for debugging
                                break  # Stop trying if a batch fails

                    else:
                        missing_cols_msg = "   ⚠️  Could not reliably identify all necessary columns for recipient fetching:"
                        if not message_link_col_rec: missing_cols_msg += " message_link_col_rec"
                        if not address_data_col_rec: missing_cols_msg += " address_data_col_rec"
                        if address_data_is_fk and not email_text_col_addr: missing_cols_msg += " email_text_col_addr (for FK)"
                        print(missing_cols_msg + ". Skipping recipient details.")

        except sqlite3.Error as e_sqlite:
            print(f"   ⚠️  SQLite error during recipient fetching: {e_sqlite}. Skipping recipient details.")
            import traceback
            traceback.print_exc()  # For debugging, can be removed in production
        except Exception as e_general:
            print(f"   ⚠️  Unexpected error during recipient fetching: {e_general}. Skipping recipient details.")
            import traceback
            traceback.print_exc()  # For debugging
        
        # Count total emails for statistics
        cursor.execute("SELECT COUNT(*) FROM messages WHERE date_received > ?", (cutoff_timestamp,))
        total_emails = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"   ✅ Found {len(results)} subscription-related emails!")
        
        # Process results into structured data
        self._process_results(results, recipients_map)
        
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
                    'scanner_version': '2.1',
                    'scanner_name': 'working_scanner',
                    'database_path': str(self.db_path)
                }
            )
        
        return self.subscriptions
    
    def _process_results(self, emails: List[tuple], recipients_map: Dict[int, List[str]]) -> None:
        """Process email results into subscription objects"""
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
            message_id, subject, date_received, sender, _ = email  # Original query has placeholder
            
            # Try to get recipients from map
            current_recipients = recipients_map.get(message_id, [])  # Default to empty list
            display_recipient = current_recipients[0] if current_recipients else 'unknown'
            
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
                    recipient=display_recipient,  # Use the determined recipient
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
            sub['accounts'].update(current_recipients if current_recipients else ['unknown'])
            
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
        """Extract payment amount using enhanced extractor"""
        return PaymentExtractor.extract_amount(text)
    
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
        duplicates = []
        
        if COMMON_STRUCTURES_AVAILABLE:
            for company, sub in self.subscriptions.items():
                if len(sub.accounts) > 1:
                    # Calculate waste (assume paying for all but one)
                    monthly_waste = 0
                    if sub.avg_amount and sub.frequency:
                        if sub.frequency == 'monthly':
                            monthly_waste = sub.avg_amount * (len(sub.accounts) - 1)
                        elif sub.frequency == 'annual':
                            monthly_waste = (sub.avg_amount / 12) * (len(sub.accounts) - 1)
                    
                    duplicates.append(DuplicateSubscription(
                        company=company,
                        accounts=list(sub.accounts),
                        monthly_waste=monthly_waste,
                        total_emails=sub.email_count
                    ))
        
        return duplicates
    
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
            print(f"Duplicate subscriptions: {summary['duplicate_count']}")
            print(f"\n💰 ESTIMATED COSTS")
            print(f"Monthly total: {format_currency(financial['monthly_total'])}")
            print(f"Annual total: {format_currency(financial['annual_total'])}")
            if financial['duplicate_monthly_waste'] > 0:
                print(f"Duplicate monthly waste: {format_currency(financial['duplicate_monthly_waste'])}")
        
        # Sort by email count
        sorted_subs = sorted(self.subscriptions.items(), 
                           key=lambda x: len(x[1]['emails']) if isinstance(x[1], dict) else x[1].email_count, 
                           reverse=True)
        
        print(f"\n📋 TOP SUBSCRIPTIONS (showing {min(limit, len(sorted_subs))} of {len(sorted_subs)})")
        print("=" * 80)
        
        for i, (company, sub) in enumerate(sorted_subs[:limit], 1):
            if COMMON_STRUCTURES_AVAILABLE and isinstance(sub, Subscription):
                print(f"\n{i}. {company}")
                print(f"   📧 {sub.email_count} emails")
                print(f"   👤 Accounts: {', '.join(list(sub.accounts)[:3])}")
                if sub.avg_amount:
                    print(f"   💰 Avg amount: {format_currency(sub.avg_amount, list(sub.currencies)[0] if sub.currencies else 'USD')}")
                print(f"   📅 Last seen: {(datetime.now() - sub.last_seen).days} days ago")
                if sub.status == 'inactive':
                    print(f"   ⚠️  Possibly inactive!")
            else:
                # Fallback display
                print(f"\n{i}. {company}")
                print(f"   📧 {len(sub['emails'])} emails")
                print(f"   👤 Accounts: {', '.join(list(sub['accounts'])[:3])}")
    
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
        description='Scan Apple Mail for subscription emails with JSON export support'
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
    scanner = WorkingSubscriptionScanner()
    
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
