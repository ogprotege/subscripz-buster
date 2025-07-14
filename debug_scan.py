#!/usr/bin/env python3
"""
Quick test to see what happens with the last scan attempt
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
conn = sqlite3.connect(str(db_path))
cursor = conn.cursor()

print("Testing Apple Mail queries...")

# Test 1: Basic count with subscription keyword
try:
    cursor.execute("SELECT COUNT(*) FROM messages WHERE LOWER(subject) LIKE '%subscription%'")
    count = cursor.fetchone()[0]
    print(f"✅ Messages with 'subscription' in subject: {count}")
except Exception as e:
    print(f"❌ Error: {e}")

# Test 2: Look further back - maybe no recent subscription emails
cutoff_1year = int((datetime.now() - timedelta(days=365)).timestamp())
cutoff_5years = int((datetime.now() - timedelta(days=1825)).timestamp())

try:
    cursor.execute(f"SELECT COUNT(*) FROM messages WHERE LOWER(subject) LIKE '%subscription%' AND date_received > {cutoff_1year}")
    count1 = cursor.fetchone()[0]
    
    cursor.execute(f"SELECT COUNT(*) FROM messages WHERE LOWER(subject) LIKE '%subscription%' AND date_received > {cutoff_5years}")
    count5 = cursor.fetchone()[0]
    
    print(f"✅ Subscription emails in last 1 year: {count1}")
    print(f"✅ Subscription emails in last 5 years: {count5}")
except Exception as e:
    print(f"❌ Error with date queries: {e}")

# Test 3: Try different keywords
keywords = ['netflix', 'spotify', 'apple', 'amazon', 'payment', 'invoice', 'receipt']
print("\nChecking for common services:")

for keyword in keywords:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM messages WHERE LOWER(subject) LIKE '%{keyword}%'")
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"✅ {keyword}: {count} messages")
    except:
        pass

# Test 4: Check if snippet column exists
try:
    cursor.execute("SELECT snippet FROM messages LIMIT 1")
    print("✅ Snippet column exists")
except:
    print("❌ Snippet column does NOT exist")

# Test 5: Get a sample subscription email
try:
    query = """
    SELECT 
        m.subject,
        s.address as sender,
        m.date_received
    FROM messages m
    LEFT JOIN addresses s ON m.sender = s.rowid
    WHERE (
        LOWER(m.subject) LIKE '%subscription%' OR
        LOWER(m.subject) LIKE '%payment%' OR
        LOWER(m.subject) LIKE '%invoice%' OR
        LOWER(m.subject) LIKE '%billing%'
    )
    ORDER BY m.date_received DESC
    LIMIT 5
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    if results:
        print(f"\n📧 Found {len(results)} recent subscription-related emails:")
        for subject, sender, date_recv in results:
            date = datetime.fromtimestamp(date_recv).strftime('%Y-%m-%d')
            print(f"  • {subject[:60]}...")
            print(f"    From: {sender}, Date: {date}")
    else:
        print("\n❌ No subscription-related emails found")
        
except Exception as e:
    print(f"❌ Error getting sample emails: {e}")

conn.close()
