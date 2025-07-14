#!/usr/bin/env python3
"""
Check the structure of the recipients table to fix SQL errors
"""

import sqlite3
from pathlib import Path

def check_recipients():
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🔍 CHECKING RECIPIENTS TABLE STRUCTURE")
    print("=" * 60)
    
    # Check if recipients table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='recipients'")
    if not cursor.fetchone():
        print("❌ No recipients table found!")
        return
    
    # Get table structure
    print("\n📋 Recipients table columns:")
    cursor.execute("PRAGMA table_info(recipients)")
    cols = cursor.fetchall()
    for col in cols:
        print(f"   • {col[1]} ({col[2]})")
    
    # Get sample data
    print("\n📊 Sample data from recipients table:")
    cursor.execute("SELECT * FROM recipients LIMIT 5")
    samples = cursor.fetchall()
    col_names = [col[1] for col in cols]
    
    for sample in samples:
        print("\n   Record:")
        for i, value in enumerate(sample):
            print(f"     {col_names[i]}: {value}")
    
    # Try different join approaches
    print("\n🔗 Testing different join methods:")
    
    # Method 1: Direct address column (if exists)
    try:
        cursor.execute("""
        SELECT r.message_id, r.address 
        FROM recipients r 
        LIMIT 5
        """)
        print("   ✅ Method 1: Recipients table has 'address' column directly")
        for row in cursor.fetchall():
            print(f"     Message {row[0]}: {row[1]}")
    except:
        print("   ❌ Method 1 failed: No 'address' column")
    
    # Method 2: Join with addresses table via ROWID
    try:
        cursor.execute("""
        SELECT r.message_id, a.address 
        FROM recipients r 
        JOIN addresses a ON r.address = a.ROWID
        LIMIT 5
        """)
        print("   ✅ Method 2: Join via address ROWID works")
        for row in cursor.fetchall():
            print(f"     Message {row[0]}: {row[1]}")
    except Exception as e:
        print(f"   ❌ Method 2 failed: {e}")
    
    # Method 3: Alternative column names
    for col_name in ['address_id', 'to_address', 'recipient', 'recipient_id']:
        try:
            cursor.execute(f"""
            SELECT r.message_id, r.{col_name}
            FROM recipients r 
            LIMIT 1
            """)
            print(f"   ✅ Found column '{col_name}' in recipients table")
        except:
            pass
    
    conn.close()

if __name__ == "__main__":
    check_recipients()
