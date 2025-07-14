#!/usr/bin/env python3
"""
Deep investigation of Apple Mail database
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def investigate():
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🔍 DEEP INVESTIGATION OF APPLE MAIL DATABASE")
    print("=" * 60)
    
    # 1. Check total messages
    cursor.execute("SELECT COUNT(*) FROM messages")
    total = cursor.fetchone()[0]
    print(f"\n📊 Total messages in database: {total:,}")
    
    # 2. Check if subject column has data
    cursor.execute("SELECT COUNT(*) FROM messages WHERE subject IS NOT NULL AND subject != ''")
    with_subject = cursor.fetchone()[0]
    print(f"📧 Messages with subject: {with_subject:,} ({with_subject/total*100:.1f}%)")
    
    # 3. Get sample subjects
    print("\n📝 Sample message subjects:")
    cursor.execute("SELECT subject, typeof(subject) FROM messages WHERE subject IS NOT NULL LIMIT 10")
    for i, (subject, subject_type) in enumerate(cursor.fetchall(), 1):
        if subject_type == 'text' or subject_type == 'blob':
            print(f"   {i}. {str(subject)[:80]} (type: {subject_type})")
        else:
            print(f"   {i}. Value: {subject} (type: {subject_type} - UNEXPECTED!)")
    
    # 4. Check case sensitivity
    print("\n🔤 Testing case sensitivity:")
    
    # Try different case variations
    tests = [
        ("LOWER(subject) LIKE '%subscription%'", "lowercase search"),
        ("subject LIKE '%subscription%'", "case-sensitive search"),
        ("subject LIKE '%Subscription%'", "capitalized search"),
        ("subject LIKE '%SUBSCRIPTION%'", "uppercase search"),
    ]
    
    for query, desc in tests:
        cursor.execute(f"SELECT COUNT(*) FROM messages WHERE {query}")
        count = cursor.fetchone()[0]
        print(f"   {desc}: {count} matches")
    
    # 5. Search for ANY financial keywords
    print("\n💰 Searching for financial keywords (case-insensitive):")
    
    keywords = [
        'payment', 'invoice', 'receipt', 'billing', 'charge',
        'subscription', 'membership', 'renewal', 'monthly', 'annual',
        'netflix', 'spotify', 'apple', 'amazon', 'google',
        'visa', 'mastercard', 'paypal', 'bank', 'credit',
        'order', 'purchase', 'transaction', 'confirm', 'thank'
    ]
    
    found_any = False
    for keyword in keywords:
        cursor.execute(f"SELECT COUNT(*) FROM messages WHERE LOWER(subject) LIKE ?", (f'%{keyword}%',))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   ✅ '{keyword}': {count} messages")
            found_any = True
            
            # Get a sample
            cursor.execute(f"SELECT subject, date_received FROM messages WHERE LOWER(subject) LIKE ? ORDER BY date_received DESC LIMIT 1", (f'%{keyword}%',))
            result = cursor.fetchone()
            if result:
                subject, date_recv = result
                date = datetime.fromtimestamp(date_recv).strftime('%Y-%m-%d')
                print(f"      Latest: {subject[:60]}... ({date})")
    
    if not found_any:
        print("   ❌ No financial keywords found in any subjects!")
    
    # 6. Check if subjects might be encoded
    print("\n🔐 Checking for encoded/special subjects:")
    cursor.execute("SELECT subject FROM messages WHERE subject LIKE '%=?%' LIMIT 5")
    encoded = cursor.fetchall()
    if encoded:
        print("   Found encoded subjects (MIME encoded):")
        for (subj,) in encoded:
            print(f"   • {subj[:80]}")
    
    # 7. Check date ranges
    print("\n📅 Date range of messages:")
    cursor.execute("SELECT MIN(date_received), MAX(date_received) FROM messages")
    min_date, max_date = cursor.fetchone()
    if min_date and max_date:
        oldest = datetime.fromtimestamp(min_date).strftime('%Y-%m-%d')
        newest = datetime.fromtimestamp(max_date).strftime('%Y-%m-%d')
        print(f"   Oldest: {oldest}")
        print(f"   Newest: {newest}")
    
    # 8. Check sender addresses
    print("\n📮 Checking sender addresses for subscription services:")
    service_domains = ['netflix', 'spotify', 'apple', 'amazon', 'google', 'microsoft', 
                      'adobe', 'dropbox', 'github', 'paypal']
    
    for domain in service_domains:
        cursor.execute("""
            SELECT COUNT(*) 
            FROM messages m
            JOIN addresses a ON m.sender = a.rowid
            WHERE LOWER(a.address) LIKE ?
        """, (f'%{domain}%',))
        count = cursor.fetchone()[0]
        if count > 0:
            print(f"   ✅ From *{domain}*: {count} messages")
    
    # 9. Try searching message content (if available)
    print("\n📄 Checking for other searchable fields:")
    
    # Get all columns
    cursor.execute("PRAGMA table_info(messages)")
    columns = [col[1] for col in cursor.fetchall()]
    
    searchable = [col for col in columns if 'text' in col.lower() or 
                  'content' in col.lower() or 'body' in col.lower() or
                  'summary' in col.lower()]
    
    if searchable:
        print(f"   Found potential content fields: {', '.join(searchable)}")
    else:
        print("   No obvious content fields found")
    
    # 10. Final diagnostic
    print("\n🔧 DIAGNOSIS:")
    if with_subject < total * 0.5:
        print("   ⚠️  Many messages have empty subjects")
    if not found_any:
        print("   ⚠️  No financial keywords found - unusual for an email account")
        print("   💡 Possible issues:")
        print("      • Subjects might be encoded (MIME)")
        print("      • Database might be incomplete")
        print("      • Messages might not be fully indexed")
        print("      • Different database structure than expected")
    
    conn.close()

if __name__ == "__main__":
    investigate()
