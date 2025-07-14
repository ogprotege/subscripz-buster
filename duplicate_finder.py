#!/usr/bin/env python3
"""
Duplicate subscription finder - focuses on finding services you're paying for multiple times
"""

import sqlite3
import re
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

def find_duplicates():
    """Find and analyze duplicate subscriptions"""
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🔄 DUPLICATE SUBSCRIPTION FINDER")
    print("=" * 80)
    print("Finding services you're paying for multiple times...\n")
    
    cutoff = int((datetime.now() - timedelta(days=1825)).timestamp())  # 5 years
    
    # Get all subscription emails with recipients
    query = f"""
    SELECT 
        s.subject,
        m.date_received,
        a.address as sender,
        m.ROWID as msg_id
    FROM messages m
    JOIN subjects s ON m.subject = s.ROWID
    LEFT JOIN addresses a ON m.sender = a.rowid
    WHERE (
        LOWER(s.subject) LIKE '%payment%' OR
        LOWER(s.subject) LIKE '%subscription%' OR
        LOWER(s.subject) LIKE '%invoice%' OR
        LOWER(s.subject) LIKE '%billing%' OR
        LOWER(s.subject) LIKE '%receipt%' OR
        LOWER(s.subject) LIKE '%charged%'
    )
    AND m.date_received > {cutoff}
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Group by service and track accounts
    services = defaultdict(lambda: {
        'accounts': defaultdict(list),  # account -> list of (date, amount, subject)
        'all_amounts': [],
        'sender_variations': set()
    })
    
    print(f"Processing {len(results)} subscription emails...\n")
    
    for subject, date_recv, sender, msg_id in results:
        if not sender:
            continue
            
        # Extract service name
        service = None
        sender_lower = sender.lower()
        
        # Known service mappings
        service_map = {
            'netflix': 'Netflix',
            'spotify': 'Spotify',
            'apple.com': 'Apple',
            'itunes': 'Apple',
            'google': 'Google',
            'youtube': 'YouTube/Google',
            'microsoft': 'Microsoft',
            'office': 'Microsoft Office',
            'adobe': 'Adobe',
            'dropbox': 'Dropbox',
            'paypal': 'PayPal',
            'stripe': 'Stripe',
            'paddle': 'Paddle',
            'amazon': 'Amazon',
            'hulu': 'Hulu',
            'disney': 'Disney+',
            'hbo': 'HBO',
            'linkedin': 'LinkedIn',
            'medium': 'Medium',
            'reddit': 'Reddit',
            'github': 'GitHub',
            'zoom': 'Zoom',
            'slack': 'Slack'
        }
        
        for key, name in service_map.items():
            if key in sender_lower:
                service = name
                break
        
        if not service:
            # Extract from domain
            if '@' in sender:
                domain = sender.split('@')[1]
                service = domain.split('.')[0].title()
        
        if not service or service.lower() in ['gmail', 'yahoo', 'outlook', 'hotmail']:
            continue
        
        # Get recipient
        recipient = None
        try:
            recip_query = """
            SELECT a.address 
            FROM recipients r
            JOIN addresses a ON r.address = a.ROWID
            WHERE r.message = ?
            LIMIT 1
            """
            cursor.execute(recip_query, (msg_id,))
            result = cursor.fetchone()
            if result:
                recipient = result[0]
        except:
            # Try to extract from subject
            email_pattern = r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})'
            matches = re.findall(email_pattern, subject)
            if matches:
                recipient = matches[0]
        
        if not recipient:
            recipient = 'Unknown Account'
        
        # Extract amount
        amount = None
        amount_match = re.search(r'\$\s*([\d,]+\.?\d*)', subject)
        if amount_match:
            try:
                amount = float(amount_match.group(1).replace(',', ''))
                if amount > 0 and amount < 10000:
                    services[service]['all_amounts'].append(amount)
            except:
                pass
        
        # Store data
        date = datetime.fromtimestamp(date_recv)
        services[service]['accounts'][recipient].append({
            'date': date,
            'amount': amount,
            'subject': subject[:100]
        })
        services[service]['sender_variations'].add(sender)
    
    # Find actual duplicates (same service, multiple accounts)
    duplicates = []
    
    for service, data in services.items():
        if len(data['accounts']) > 1:
            # Calculate average amount
            avg_amount = 0
            if data['all_amounts']:
                avg_amount = sum(data['all_amounts']) / len(data['all_amounts'])
            
            duplicates.append({
                'service': service,
                'accounts': dict(data['accounts']),
                'account_count': len(data['accounts']),
                'avg_amount': avg_amount,
                'total_emails': sum(len(emails) for emails in data['accounts'].values()),
                'sender_variations': list(data['sender_variations'])
            })
    
    # Sort by potential waste
    duplicates.sort(key=lambda x: x['avg_amount'] * (x['account_count'] - 1), reverse=True)
    
    # Display results
    if not duplicates:
        print("✅ Good news! No duplicate subscriptions found.")
    else:
        print(f"⚠️  Found {len(duplicates)} services with multiple accounts!\n")
        
        total_waste = 0
        
        for i, dup in enumerate(duplicates, 1):
            waste = dup['avg_amount'] * (dup['account_count'] - 1)
            total_waste += waste
            
            print(f"{i}. {dup['service']}")
            print(f"   📧 Active on {dup['account_count']} accounts")
            print(f"   💰 Average amount: ${dup['avg_amount']:.2f}")
            print(f"   💸 Monthly waste: ${waste:.2f}")
            print(f"   📨 Total emails: {dup['total_emails']}")
            
            print(f"\n   Accounts:")
            for account, emails in sorted(dup['accounts'].items()):
                recent = max(emails, key=lambda x: x['date'])
                days_ago = (datetime.now() - recent['date']).days
                
                # Check if still active
                status = "✅ Active" if days_ago < 90 else "⚠️  Inactive" if days_ago < 180 else "❌ Dormant"
                
                print(f"      • {account}")
                print(f"        {len(emails)} emails, last: {days_ago} days ago {status}")
                if recent['amount']:
                    print(f"        Last amount: ${recent['amount']:.2f}")
            
            print(f"\n   Email variations from: {', '.join(dup['sender_variations'][:3])}")
            print("-" * 80)
        
        print(f"\n💸 TOTAL DUPLICATE WASTE SUMMARY")
        print("=" * 80)
        print(f"Monthly waste: ${total_waste:.2f}")
        print(f"Annual waste: ${total_waste * 12:.2f}")
        
        print(f"\n💡 RECOMMENDATIONS:")
        print("1. Cancel duplicate subscriptions on secondary accounts")
        print("2. Use family/group plans where available")
        print("3. Consolidate to one primary email for subscriptions")
        print("4. Check if 'inactive' subscriptions are still charging")
    
    conn.close()

if __name__ == "__main__":
    find_duplicates()
