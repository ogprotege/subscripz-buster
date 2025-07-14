#!/usr/bin/env python3
"""
Fixed scanner that handles Apple Mail's normalized database structure
"""

import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

# Core keywords only
CORE_KEYWORDS = [
    'subscription', 'membership', 'billing', 'invoice', 'payment',
    'charged', 'receipt', 'renewal', 'recurring', 'monthly',
    'annual', 'cancelled', 'trial', 'expired', 'failed'
]

class FixedSubscriptionScanner:
    def __init__(self):
        self.db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
        if not self.db_path.exists():
            raise FileNotFoundError(f"Apple Mail database not found at {self.db_path}")
        
        self.results = defaultdict(lambda: {
            'count': 0,
            'accounts': set(),
            'amounts': [],
            'last_seen': None,
            'first_seen': None,
            'subjects': []
        })
        
        # Check if subjects are normalized
        self._check_database_structure()
    
    def _check_database_structure(self):
        """Check if subjects are in a separate table"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        # Check if subjects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='subjects'")
        self.has_subjects_table = cursor.fetchone() is not None
        
        if self.has_subjects_table:
            print("✅ Detected normalized database (subjects in separate table)")
        else:
            print("ℹ️  Standard database structure")
        
        conn.close()
    
    def scan(self, days_back=365):
        """Scan with proper handling of normalized structure"""
        print(f"🔍 Scanning {days_back} days of email...")
        
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cutoff = int((datetime.now() - timedelta(days=days_back)).timestamp())
        total_found = 0
        
        # Build the appropriate query based on database structure
        if self.has_subjects_table:
            # Normalized structure - join with subjects table
            print("   Using normalized query (joining with subjects table)...")
            
            # Process keywords in batches
            batch_size = 5
            for i in range(0, len(CORE_KEYWORDS), batch_size):
                batch = CORE_KEYWORDS[i:i+batch_size]
                
                conditions = []
                for keyword in batch:
                    escaped = keyword.replace("'", "''")
                    conditions.append(f"LOWER(s.subject) LIKE '%{escaped}%'")
                
                query = f"""
                SELECT 
                    s.subject,
                    m.date_received,
                    a.address as sender,
                    r.address as recipient
                FROM messages m
                JOIN subjects s ON m.subject = s.ROWID
                LEFT JOIN addresses a ON m.sender = a.rowid
                LEFT JOIN recipients rec ON m.message_id = rec.message_id
                LEFT JOIN addresses r ON rec.address_id = r.rowid
                WHERE ({' OR '.join(conditions)})
                AND m.date_received > {cutoff}
                """
                
                try:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    total_found += len(results)
                    self._process_results(results)
                    print(f"  • Batch {i//batch_size + 1}: {len(results)} emails")
                except Exception as e:
                    print(f"  ⚠️  Error in batch {i//batch_size + 1}: {e}")
        
        else:
            # Standard structure - search directly in messages
            print("   Using standard query...")
            
            # Try sender-based search as fallback
            print("\n   Searching by sender domain (more reliable)...")
            
            service_domains = [
                'netflix', 'spotify', 'apple', 'amazon', 'google',
                'microsoft', 'adobe', 'dropbox', 'github', 'paypal',
                'hulu', 'disney', 'hbo', 'uber', 'lyft', 'doordash'
            ]
            
            for domain in service_domains:
                query = f"""
                SELECT 
                    m.subject,
                    m.date_received,
                    a.address as sender,
                    r.address as recipient
                FROM messages m
                LEFT JOIN addresses a ON m.sender = a.rowid
                LEFT JOIN recipients rec ON m.message_id = rec.message_id
                LEFT JOIN addresses r ON rec.address_id = r.rowid
                WHERE LOWER(a.address) LIKE '%{domain}%'
                AND m.date_received > {cutoff}
                """
                
                try:
                    cursor.execute(query)
                    results = cursor.fetchall()
                    if results:
                        total_found += len(results)
                        self._process_results(results)
                        print(f"  • {domain}: {len(results)} emails")
                except Exception as e:
                    print(f"  ⚠️  Error searching {domain}: {e}")
        
        conn.close()
        print(f"\n✅ Found {total_found} subscription-related emails")
        print(f"✅ Identified {len(self.results)} unique subscriptions")
    
    def _process_results(self, results):
        """Process query results"""
        for row in results:
            subject, date_recv, sender, recipient = row
            
            company = self._extract_company(sender)
            if not company:
                continue
            
            # Update subscription data
            sub = self.results[company]
            sub['count'] += 1
            
            if recipient:
                sub['accounts'].add(recipient)
            
            # Track dates
            date = datetime.fromtimestamp(date_recv)
            if not sub['first_seen'] or date < sub['first_seen']:
                sub['first_seen'] = date
            if not sub['last_seen'] or date > sub['last_seen']:
                sub['last_seen'] = date
            
            # Store subject if it's text
            if subject and isinstance(subject, str):
                sub['subjects'].append(subject[:100])
                
                # Extract amount from subject
                amount_match = re.search(r'\$\s*([\d,]+\.?\d*)', subject)
                if amount_match:
                    try:
                        amount = float(amount_match.group(1).replace(',', ''))
                        if 0.01 <= amount <= 10000:
                            sub['amounts'].append(amount)
                    except:
                        pass
    
    def _extract_company(self, sender):
        """Extract company name from sender"""
        if not sender or '@' not in sender:
            return None
        
        email_lower = sender.lower()
        
        # Remove common prefixes
        for prefix in ['noreply@', 'no-reply@', 'billing@', 'support@', 'notification@']:
            if email_lower.startswith(prefix):
                email_lower = email_lower.replace(prefix, '')
                break
        
        # Get domain
        domain = email_lower.split('@')[1] if '@' in email_lower else email_lower
        company = domain.split('.')[0]
        
        # Skip generic providers
        if company in ['gmail', 'yahoo', 'outlook', 'hotmail', 'icloud']:
            return None
        
        return company.title()
    
    def show_results(self):
        """Display results"""
        if not self.results:
            print("\n📭 No subscriptions found")
            print("\n💡 Try:")
            print("   • Scanning more years (some subscriptions are old)")
            print("   • Running the structure investigation (option 5)")
            print("   • Checking if Apple Mail has downloaded all messages")
            return
        
        # Convert sets to lists
        for company in self.results:
            self.results[company]['accounts'] = list(self.results[company]['accounts'])
        
        # Sort by email count
        sorted_subs = sorted(self.results.items(), 
                           key=lambda x: x[1]['count'], 
                           reverse=True)
        
        print("\n📊 SUBSCRIPTIONS FOUND")
        print("=" * 60)
        
        for i, (company, data) in enumerate(sorted_subs[:20], 1):
            print(f"\n{i}. {company}")
            print(f"   📧 {data['count']} emails")
            print(f"   👤 {len(data['accounts'])} account(s)")
            
            if data['amounts']:
                avg = sum(data['amounts']) / len(data['amounts'])
                print(f"   💰 Avg: ${avg:.2f}/mo")
            
            if data['subjects']:
                print(f"   📝 Sample: {data['subjects'][0][:60]}...")
            
            if data['last_seen']:
                days_ago = (datetime.now() - data['last_seen']).days
                print(f"   📅 Last seen: {days_ago} days ago")

def main():
    print("🚀 FIXED SUBSCRIPTION SCANNER")
    print("=" * 60)
    
    try:
        scanner = FixedSubscriptionScanner()
        
        # Ask for timeframe
        years = input("\nHow many years to scan? (default 5): ").strip()
        years = int(years) if years else 5
        
        scanner.scan(days_back=years * 365)
        scanner.show_results()
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
