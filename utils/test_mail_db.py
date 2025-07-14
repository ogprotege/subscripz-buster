#!/usr/bin/env python3
"""Test Apple Mail database connection"""

import sqlite3
from pathlib import Path

try:
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    print(f"Attempting to connect to: {db_path}")
    print(f"File exists: {db_path.exists()}")
    print(f"File size: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Get table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f"\nFound {len(tables)} tables:")
    for table in tables[:10]:  # Show first 10
        print(f"  - {table[0]}")
    
    # Count messages
    cursor.execute("SELECT COUNT(*) FROM messages")
    message_count = cursor.fetchone()[0]
    print(f"\nTotal messages in database: {message_count:,}")
    
    # Count addresses
    cursor.execute("SELECT COUNT(*) FROM addresses")
    address_count = cursor.fetchone()[0]
    print(f"Total addresses in database: {address_count:,}")
    
    # Get some recent messages with subscription keywords
    query = """
    SELECT m.subject, s.address as sender
    FROM messages m
    LEFT JOIN addresses s ON m.sender = s.rowid
    WHERE (m.subject LIKE '%subscription%' OR m.subject LIKE '%billing%')
    ORDER BY m.date_received DESC
    LIMIT 10
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    print(f"\nSample subscription emails found:")
    for subject, sender in results:
        print(f"  - {subject[:60]}... from {sender}")
    
    conn.close()
    print("\n✅ Database connection successful!")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
