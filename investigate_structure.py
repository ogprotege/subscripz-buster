#!/usr/bin/env python3
"""
Investigate Apple Mail database structure - find where subjects are really stored
"""

import sqlite3
from pathlib import Path

def investigate_structure():
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🔍 INVESTIGATING APPLE MAIL DATABASE STRUCTURE")
    print("=" * 60)
    
    # 1. Check what the subject column actually contains
    print("\n📊 Analyzing 'subject' column in messages table:")
    cursor.execute("SELECT subject, typeof(subject), COUNT(*) FROM messages GROUP BY typeof(subject)")
    for value_type, type_name, count in cursor.fetchall():
        print(f"   Type: {type_name}, Count: {count}")
        if type_name == 'integer':
            print("   ⚠️  Subject is stored as INTEGER - likely a foreign key!")
    
    # 2. Find all tables
    print("\n📋 All tables in database:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    for table in tables:
        print(f"   • {table}")
    
    # 3. Look for subject-related tables
    print("\n🔎 Tables that might contain subjects:")
    subject_tables = [t for t in tables if 'subject' in t.lower() or 'text' in t.lower() or 'content' in t.lower()]
    if subject_tables:
        for table in subject_tables:
            print(f"   • {table}")
            # Check columns
            cursor.execute(f"PRAGMA table_info({table})")
            cols = cursor.fetchall()
            print(f"     Columns: {', '.join([col[1] for col in cols])}")
    else:
        print("   No obvious subject/text tables found")
    
    # 4. Check if subjects table exists
    if 'subjects' in tables:
        print("\n✅ Found 'subjects' table!")
        cursor.execute("PRAGMA table_info(subjects)")
        cols = cursor.fetchall()
        print("   Columns:", ', '.join([col[1] for col in cols]))
        
        # Get sample subjects
        cursor.execute("SELECT * FROM subjects LIMIT 5")
        samples = cursor.fetchall()
        print("\n   Sample subjects:")
        for sample in samples:
            print(f"     {sample}")
        
        # Try to join messages with subjects
        print("\n🔗 Attempting to join messages with subjects:")
        try:
            query = """
            SELECT s.subject, COUNT(*) as count
            FROM messages m
            JOIN subjects s ON m.subject = s.ROWID
            WHERE s.subject LIKE '%payment%' 
               OR s.subject LIKE '%subscription%'
               OR s.subject LIKE '%invoice%'
            GROUP BY s.subject
            LIMIT 10
            """
            cursor.execute(query)
            results = cursor.fetchall()
            if results:
                print("   ✅ Found subscription-related subjects!")
                for subject, count in results:
                    print(f"     • {subject[:80]}... ({count} messages)")
            else:
                print("   ❌ No subscription keywords found in subjects table")
        except Exception as e:
            print(f"   ❌ Join failed: {e}")
    
    # 5. Analyze the messages table structure more
    print("\n📧 Messages table structure:")
    cursor.execute("PRAGMA table_info(messages)")
    cols = cursor.fetchall()
    print("   All columns:")
    for col in cols:
        print(f"     • {col[1]} ({col[2]})")
    
    # 6. Look for any column that might contain email text
    print("\n📄 Columns that might contain email content:")
    text_cols = [col[1] for col in cols if any(word in col[1].lower() for word in ['text', 'content', 'body', 'snippet', 'summary'])]
    if text_cols:
        print(f"   Found: {', '.join(text_cols)}")
    else:
        print("   No obvious content columns in messages table")
    
    # 7. Sample query to find subscription emails by sender
    print("\n📮 Trying to find subscriptions by sender address:")
    query = """
    SELECT a.address, COUNT(*) as count
    FROM messages m
    JOIN addresses a ON m.sender = a.rowid
    WHERE LOWER(a.address) LIKE '%netflix%'
       OR LOWER(a.address) LIKE '%spotify%'
       OR LOWER(a.address) LIKE '%apple%'
       OR LOWER(a.address) LIKE '%billing%'
       OR LOWER(a.address) LIKE '%noreply%'
    GROUP BY a.address
    ORDER BY count DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    senders = cursor.fetchall()
    if senders:
        print("   ✅ Found subscription service senders:")
        for sender, count in senders:
            print(f"     • {sender}: {count} messages")
    else:
        print("   ❌ No subscription service senders found")
    
    conn.close()

if __name__ == "__main__":
    investigate_structure()
