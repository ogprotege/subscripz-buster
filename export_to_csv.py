#!/usr/bin/env python3
"""
Export comprehensive subscription data to CSV for easy analysis
"""

import sqlite3
import re
import csv
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

def export_to_csv():
    """Export all subscription data to CSV"""
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("📊 Exporting subscription data to CSV...")
    
    cutoff = int((datetime.now() - timedelta(days=1825)).timestamp())  # 5 years
    
    # Query all subscription emails
    query = f"""
    SELECT 
        s.subject,
        m.date_received,
        a.address as sender,
        m.ROWID as message_rowid
    FROM messages m
    JOIN subjects s ON m.subject = s.ROWID
    LEFT JOIN addresses a ON m.sender = a.rowid
    WHERE (
        LOWER(s.subject) LIKE '%payment%' OR
        LOWER(s.subject) LIKE '%subscription%' OR
        LOWER(s.subject) LIKE '%invoice%' OR
        LOWER(s.subject) LIKE '%billing%' OR
        LOWER(s.subject) LIKE '%receipt%' OR
        LOWER(s.subject) LIKE '%charged%' OR
        LOWER(s.subject) LIKE '%renewal%' OR
        LOWER(s.subject) LIKE '%membership%'
    )
    AND m.date_received > {cutoff}
    ORDER BY a.address, m.date_received DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Prepare CSV data
    csv_data = []
    
    for subject, date_recv, sender, msg_rowid in results:
        # Extract company
        company = 'Unknown'
        if sender and '@' in sender:
            domain = sender.split('@')[1]
            company = domain.split('.')[0].title()
        
        # Extract amount
        amount = ''
        amount_match = re.search(r'\$\s*([\d,]+\.?\d*)', subject)
        if amount_match:
            amount = amount_match.group(1).replace(',', '')
        
        # Get recipient
        recipient = ''
        try:
            recip_query = """
            SELECT a.address 
            FROM recipients r
            JOIN addresses a ON r.address = a.ROWID
            WHERE r.message = ?
            LIMIT 1
            """
            cursor.execute(recip_query, (msg_rowid,))
            result = cursor.fetchone()
            if result:
                recipient = result[0]
        except:
            pass
        
        # Format date
        date = datetime.fromtimestamp(date_recv).strftime('%Y-%m-%d %H:%M:%S')
        
        csv_data.append({
            'Date': date,
            'Company': company,
            'Sender': sender,
            'Recipient': recipient,
            'Subject': subject[:200],  # Limit subject length
            'Amount': amount
        })
    
    # Write to CSV
    filename = f"subscriptions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    filepath = Path.home() / "Desktop" / filename
    
    with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['Date', 'Company', 'Sender', 'Recipient', 'Subject', 'Amount']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"✅ Exported {len(csv_data)} subscription emails to:")
    print(f"   {filepath}")
    print(f"\nYou can now:")
    print("• Open in Excel/Numbers for analysis")
    print("• Sort by Company to see all emails from each service")
    print("• Filter by Recipient to see subscriptions per email account")
    print("• Sum the Amount column to calculate costs")
    
    conn.close()

if __name__ == "__main__":
    export_to_csv()
