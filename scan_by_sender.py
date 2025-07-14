#!/usr/bin/env python3
"""
Alternative search - look at ALL emails from known services
"""

import sqlite3
from pathlib import Path
from datetime import datetime
from collections import defaultdict

def scan_by_sender():
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🔍 SCANNING BY SENDER DOMAIN")
    print("=" * 60)
    
    # Known subscription services
    service_patterns = {
        'Netflix': ['netflix.com', 'netflix.net'],
        'Spotify': ['spotify.com'],
        'Apple': ['apple.com', 'itunes.com', 'icloud.com'],
        'Amazon': ['amazon.com', 'amazonaws.com'],
        'Google': ['google.com', 'youtube.com', 'googleapis.com'],
        'Microsoft': ['microsoft.com', 'office.com', 'outlook.com'],
        'Adobe': ['adobe.com', 'adobesystems.com'],
        'Dropbox': ['dropbox.com', 'dropboxmail.com'],
        'GitHub': ['github.com'],
        'PayPal': ['paypal.com'],
        'Hulu': ['hulu.com'],
        'Disney': ['disney.com', 'disneyplus.com'],
        'HBO': ['hbo.com', 'hbomax.com'],
        'Uber': ['uber.com'],
        'Lyft': ['lyft.com'],
        'DoorDash': ['doordash.com'],
        'Grubhub': ['grubhub.com'],
        'LinkedIn': ['linkedin.com'],
        'Zoom': ['zoom.us', 'zoom.com'],
        'Slack': ['slack.com'],
        'Notion': ['notion.so'],
        'Canva': ['canva.com'],
        'Figma': ['figma.com']
    }
    
    results = defaultdict(lambda: {'count': 0, 'samples': []})
    
    # Search for each service
    for service, domains in service_patterns.items():
        for domain in domains:
            query = """
            SELECT 
                m.subject,
                a.address as sender,
                m.date_received
            FROM messages m
            JOIN addresses a ON m.sender = a.rowid
            WHERE LOWER(a.address) LIKE ?
            ORDER BY m.date_received DESC
            LIMIT 5
            """
            
            cursor.execute(query, (f'%@{domain}%',))
            emails = cursor.fetchall()
            
            if emails:
                results[service]['count'] += len(emails)
                for subject, sender, date_recv in emails:
                    date = datetime.fromtimestamp(date_recv).strftime('%Y-%m-%d')
                    results[service]['samples'].append({
                        'subject': subject,
                        'sender': sender,
                        'date': date
                    })
    
    # Display results
    if not results:
        print("❌ No emails from known subscription services found!")
        
        # Try to see what domains we DO have
        print("\n📧 Top sender domains in your email:")
        cursor.execute("""
            SELECT 
                SUBSTR(a.address, INSTR(a.address, '@') + 1) as domain,
                COUNT(*) as count
            FROM messages m
            JOIN addresses a ON m.sender = a.rowid
            WHERE a.address LIKE '%@%'
            GROUP BY domain
            ORDER BY count DESC
            LIMIT 20
        """)
        
        for domain, count in cursor.fetchall():
            print(f"   • {domain}: {count} messages")
    
    else:
        print(f"\n✅ Found emails from {len(results)} subscription services:\n")
        
        # Sort by count
        sorted_services = sorted(results.items(), key=lambda x: x[1]['count'], reverse=True)
        
        for service, data in sorted_services:
            print(f"\n📮 {service}: {data['count']} emails")
            
            # Show samples
            for i, sample in enumerate(data['samples'][:3], 1):
                subject = sample['subject'] if sample['subject'] else "[No Subject]"
                print(f"   {i}. {subject[:60]}...")
                print(f"      From: {sample['sender']}")
                print(f"      Date: {sample['date']}")
    
    # Check for billing-specific addresses
    print("\n💳 Checking for billing-specific email addresses:")
    
    billing_patterns = [
        'billing@', 'invoice@', 'payment@', 'subscription@',
        'noreply@', 'no-reply@', 'donotreply@', 'account@',
        'support@', 'help@', 'service@'
    ]
    
    for pattern in billing_patterns:
        cursor.execute("""
            SELECT COUNT(*)
            FROM messages m
            JOIN addresses a ON m.sender = a.rowid
            WHERE LOWER(a.address) LIKE ?
        """, (f'{pattern}%',))
        
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   ✅ {pattern}*: {count} messages")
    
    conn.close()

if __name__ == "__main__":
    scan_by_sender()
