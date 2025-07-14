"""
subscripz-buster: Local Apple Mail Edition
This version reads directly from your Apple Mail database where ALL your
Gmail accounts are already consolidated. No APIs needed!
"""

import os
import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
from mcp.server.fastmcp import FastMCP
import pandas as pd

mcp = FastMCP(
    "subscripz-buster-local",
    description="Scans ALL your email accounts through Apple Mail's local database"
)

# Define subscription keywords
SUBSCRIPTION_KEYWORDS = [
    'subscription', 'subscribe', 'renewal', 'recurring', 'membership',
    'billing', 'invoice', 'payment', 'charged', 'receipt',
    'trial', 'premium', 'upgrade', 'plan', 'cancel',
    'monthly', 'yearly', 'annual', 'charge', 'auto-renew'
]

class AppleMailSubscriptionHunter:
    """Reads directly from Apple Mail's local SQLite database"""
    
    def __init__(self):
        # Apple Mail stores everything in a few key locations
        self.mail_root = Path.home() / "Library" / "Mail"
        self.db_path = self._find_envelope_index()
        self.subscriptions = defaultdict(dict)
        
    def _find_envelope_index(self) -> Path:
        """Find the Envelope Index database (location varies by macOS version)"""
        possible_paths = [
            self.mail_root / "V10" / "MailData" / "Envelope Index",
            self.mail_root / "V9" / "MailData" / "Envelope Index",
            self.mail_root / "V8" / "MailData" / "Envelope Index",
            self.mail_root / "V7" / "MailData" / "Envelope Index",
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
                
        # If not found, try to locate it
        envelope_files = list(self.mail_root.rglob("Envelope Index"))
        if envelope_files:
            return envelope_files[0]
            
        raise FileNotFoundError("Could not find Apple Mail's Envelope Index database")
    
    def get_all_accounts(self) -> List[Dict]:
        """Discover all email accounts configured in Apple Mail"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get all unique email addresses from the database
        query = """
        SELECT DISTINCT address 
        FROM addresses 
        WHERE address LIKE '%@%' 
        ORDER BY address
        """
        
        try:
            results = cursor.execute(query).fetchall()
            accounts = [{'email': row[0]} for row in results if row[0]]
            
            # Also try to get account info from mailboxes
            mailbox_query = """
            SELECT DISTINCT account_identifier, url 
            FROM mailboxes 
            WHERE account_identifier IS NOT NULL
            """
            
            mailbox_results = cursor.execute(mailbox_query).fetchall()
            
            conn.close()
            
            return accounts
            
        except Exception as e:
            conn.close()
            return []
    
    def scan_all_emails(self, days_back: int = 365) -> Dict:
        """Scan all emails across all accounts for subscriptions"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Build the search query for subscription keywords
        keyword_conditions = []
        for keyword in SUBSCRIPTION_KEYWORDS[:15]:  # Use top 15 keywords
            keyword_conditions.append(f"m.subject LIKE '%{keyword}%'")
            keyword_conditions.append(f"m.snippet LIKE '%{keyword}%'")
        
        keyword_clause = " OR ".join(keyword_conditions)
        
        # Calculate date cutoff (Apple Mail uses Unix timestamps)
        cutoff_timestamp = int((datetime.now() - timedelta(days=days_back)).timestamp())
        
        # Main query to find subscription-related emails
        query = f"""
        SELECT 
            m.message_id,
            m.subject,
            m.date_sent,
            m.date_received,
            s.address as sender,
            r.address as recipient,
            m.snippet,
            mb.url as mailbox_url
        FROM messages m
        LEFT JOIN addresses s ON m.sender = s.rowid
        LEFT JOIN recipients rec ON m.message_id = rec.message_id
        LEFT JOIN addresses r ON rec.address_id = r.rowid
        LEFT JOIN mailboxes mb ON m.mailbox = mb.rowid
        WHERE ({keyword_clause})
        AND m.date_received > {cutoff_timestamp}
        ORDER BY m.date_received DESC
        """
        
        results = []
        try:
            cursor.execute(query)
            columns = [description[0] for description in cursor.description]
            
            for row in cursor:
                email_data = dict(zip(columns, row))
                
                # Extract account from mailbox URL or recipient
                if email_data['mailbox_url']:
                    # Parse account from IMAP URL
                    account_match = re.search(r'imap://([^/]+)@', email_data['mailbox_url'])
                    if account_match:
                        email_data['account'] = account_match.group(1) + '@' + \
                                              email_data['mailbox_url'].split('@')[1].split('/')[0]
                else:
                    email_data['account'] = email_data['recipient']
                
                results.append(email_data)
                
        except Exception as e:
            print(f"Error scanning emails: {e}")
        finally:
            conn.close()
            
        # Store results for other tools
        self.subscriptions = self._process_results(results)
        return self.subscriptions
    
    def _process_results(self, emails: List[Dict]) -> Dict:
        """Process email results to extract subscription information"""
        subscriptions_by_company = defaultdict(lambda: {
            'emails': [],
            'accounts': set(),
            'amounts': [],
            'last_seen': None,
            'first_seen': None,
            'status': 'unknown'
        })
        
        for email in emails:
            # Extract company from sender
            company = self._extract_company_name(email['sender'])
            if not company:
                continue
                
            # Convert timestamp to datetime
            email_date = datetime.fromtimestamp(email['date_received'])
            
            sub = subscriptions_by_company[company]
            sub['emails'].append(email)
            sub['accounts'].add(email.get('account', 'unknown'))
            
            # Update date ranges
            if not sub['first_seen'] or email_date < sub['first_seen']:
                sub['first_seen'] = email_date
            if not sub['last_seen'] or email_date > sub['last_seen']:
                sub['last_seen'] = email_date
            
            # Try to extract amount from snippet
            amount_match = re.search(r'\$\s*([\d,]+\.?\d*)', email['snippet'] or '')
            if amount_match:
                try:
                    amount = float(amount_match.group(1).replace(',', ''))
                    sub['amounts'].append(amount)
                except:
                    pass
            
            # Update status based on subject/snippet
            text = (email['subject'] + ' ' + (email['snippet'] or '')).lower()
            if 'cancel' in text or 'terminated' in text:
                sub['status'] = 'cancelled'
            elif 'active' in text or 'renewed' in text or 'confirmed' in text:
                sub['status'] = 'active'
            elif 'trial' in text:
                sub['status'] = 'trial'
        
        return dict(subscriptions_by_company)
    
    def _extract_company_name(self, sender_email: str) -> Optional[str]:
        """Extract a clean company name from email address"""
        if not sender_email:
            return None
            
        # Remove common prefixes
        email_lower = sender_email.lower()
        for prefix in ['noreply@', 'no-reply@', 'billing@', 'support@', 'notification@']:
            if email_lower.startswith(prefix):
                domain = email_lower.replace(prefix, '')
                company = domain.split('.')[0]
                return company.title()
        
        # Extract domain
        if '@' in sender_email:
            domain = sender_email.split('@')[1]
            company = domain.split('.')[0]
            
            # Clean up common email providers
            if company.lower() not in ['gmail', 'yahoo', 'outlook', 'hotmail']:
                return company.title()
                
        return None

# Global instance
hunter = AppleMailSubscriptionHunter()

@mcp.tool()
def scan_apple_mail(days_back: int = 365) -> str:
    """
    Scan ALL your email accounts in Apple Mail for subscriptions.
    No API setup needed - reads directly from your local email database!
    
    Args:
        days_back: How many days of history to scan (default: 365)
    """
    # First, discover all accounts
    accounts = hunter.get_all_accounts()
    
    output = f"🔍 Found {len(accounts)} email accounts in Apple Mail\n"
    output += "=" * 50 + "\n\n"
    
    # Scan all emails
    results = hunter.scan_all_emails(days_back)
    
    output += f"📧 Scanned emails from the last {days_back} days\n"
    output += f"💎 Found {len(results)} potential subscriptions\n\n"
    
    # Sort by number of emails (most active subscriptions first)
    sorted_subs = sorted(results.items(), 
                        key=lambda x: len(x[1]['emails']), 
                        reverse=True)
    
    # Display top subscriptions
    for company, data in sorted_subs[:25]:
        output += f"\n🏢 {company}\n"
        output += f"   📧 {len(data['emails'])} emails\n"
        output += f"   👤 Accounts: {', '.join(data['accounts'])}\n"
        
        if data['amounts']:
            avg_amount = sum(data['amounts']) / len(data['amounts'])
            output += f"   💰 Avg amount: ${avg_amount:.2f}\n"
        
        output += f"   📅 First seen: {data['first_seen'].strftime('%Y-%m-%d')}\n"
        output += f"   📅 Last seen: {data['last_seen'].strftime('%Y-%m-%d')}\n"
        output += f"   🚦 Status: {data['status']}\n"
    
    return output

@mcp.tool()
def find_duplicate_subscriptions() -> str:
    """
    Find subscriptions you're paying for multiple times across different accounts.
    This is the sneaky stuff that really adds up!
    """
    if not hunter.subscriptions:
        return "Run scan_apple_mail first to find subscriptions!"
    
    duplicates = []
    
    for company, data in hunter.subscriptions.items():
        if len(data['accounts']) > 1:
            duplicates.append((company, data))
    
    if not duplicates:
        return "Good news! No duplicate subscriptions found across your accounts."
    
    output = f"⚠️  Found {len(duplicates)} subscriptions across multiple accounts!\n"
    output += "=" * 50 + "\n\n"
    
    total_waste = 0
    
    for company, data in duplicates:
        output += f"🔄 {company}\n"
        output += f"   Active on {len(data['accounts'])} accounts:\n"
        
        for account in data['accounts']:
            output += f"     • {account}\n"
        
        if data['amounts']:
            avg_amount = sum(data['amounts']) / len(data['amounts'])
            potential_waste = avg_amount * (len(data['accounts']) - 1)
            total_waste += potential_waste
            
            output += f"   💸 Potential monthly waste: ${potential_waste:.2f}\n"
        
        output += "\n"
    
    output += f"\n💰 Total potential monthly savings: ${total_waste:.2f}"
    output += f"\n💰 Annual savings: ${total_waste * 12:.2f}"
    
    return output

@mcp.tool()
def analyze_by_account() -> str:
    """See subscription breakdown by each email account"""
    if not hunter.subscriptions:
        return "Run scan_apple_mail first to find subscriptions!"
    
    account_breakdown = defaultdict(list)
    
    for company, data in hunter.subscriptions.items():
        for account in data['accounts']:
            account_breakdown[account].append({
                'company': company,
                'amount': sum(data['amounts']) / len(data['amounts']) if data['amounts'] else 0,
                'email_count': len([e for e in data['emails'] if e.get('account') == account])
            })
    
    output = "📊 Subscription Breakdown by Email Account\n"
    output += "=" * 50 + "\n\n"
    
    for account, subs in account_breakdown.items():
        total = sum(s['amount'] for s in subs)
        output += f"\n📧 {account}\n"
        output += f"   Subscriptions: {len(subs)}\n"
        output += f"   Est. monthly total: ${total:.2f}\n"
        output += f"   Top subscriptions:\n"
        
        # Show top 3 for each account
        for sub in sorted(subs, key=lambda x: x['amount'], reverse=True)[:3]:
            if sub['amount'] > 0:
                output += f"     • {sub['company']}: ${sub['amount']:.2f}\n"
    
    return output

if __name__ == "__main__":
    mcp.run()