#!/usr/bin/env python3
"""
Check the exact structure of the recipients table to properly fix the SQL errors
"""

import sqlite3
from pathlib import Path

def check_exact_structure():
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("🔍 CHECKING EXACT DATABASE STRUCTURE")
    print("=" * 60)
    
    # 1. Get recipients table structure
    print("\n📋 Recipients table structure:")
    cursor.execute("PRAGMA table_info(recipients)")
    recipients_cols = cursor.fetchall()
    
    if not recipients_cols:
        print("❌ No recipients table found!")
    else:
        print("Columns:")
        for col in recipients_cols:
            print(f"   • {col[1]} ({col[2]})")
    
    # 2. Get addresses table structure
    print("\n📋 Addresses table structure:")
    cursor.execute("PRAGMA table_info(addresses)")
    addresses_cols = cursor.fetchall()
    
    print("Columns:")
    for col in addresses_cols:
        print(f"   • {col[1]} ({col[2]})")
    
    # 3. Test different ways to get recipient addresses
    print("\n🔗 Testing recipient queries:")
    
    # Get a sample message ID
    cursor.execute("SELECT message_id FROM messages LIMIT 1")
    sample_msg = cursor.fetchone()
    
    if sample_msg:
        msg_id = sample_msg[0]
        print(f"\nUsing message_id: {msg_id}")
        
        # Test 1: Direct recipient query
        try:
            cursor.execute("SELECT * FROM recipients WHERE message_id = ? LIMIT 1", (msg_id,))
            recipient = cursor.fetchone()
            if recipient:
                print(f"\n✅ Recipient record: {recipient}")
                # Map column names
                col_names = [col[1] for col in recipients_cols]
                recipient_dict = dict(zip(col_names, recipient))
                print(f"   As dict: {recipient_dict}")
        except Exception as e:
            print(f"\n❌ Error: {e}")
        
        # Test 2: Check if 'address' column contains ID or actual address
        try:
            cursor.execute("""
            SELECT r.*, a.address as actual_address
            FROM recipients r
            LEFT JOIN addresses a ON r.address = a.ROWID
            WHERE r.message_id = ?
            LIMIT 1
            """, (msg_id,))
            
            result = cursor.fetchone()
            if result:
                print(f"\n✅ Join successful: {result}")
        except Exception as e:
            print(f"\n❌ Join failed: {e}")
    
    # 4. Show the working query structure
    print("\n📝 WORKING QUERY STRUCTURE:")
    print("""
    For normalized database (with subjects table):
    SELECT 
        m.message_id,
        s.subject as subject_text,
        m.date_received,
        sender.address as sender_address
    FROM messages m
    JOIN subjects s ON m.subject = s.ROWID
    LEFT JOIN addresses sender ON m.sender = sender.ROWID
    WHERE (subject conditions)
    
    Then separately (if needed):
    SELECT r.message_id, a.address
    FROM recipients r
    JOIN addresses a ON r.address = a.ROWID
    WHERE r.message_id IN (message_ids)
    """)
    
    conn.close()

if __name__ == "__main__":
    check_exact_structure()
