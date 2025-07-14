#!/usr/bin/env python3
"""
Quick financial summary of subscriptions
"""

import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import re

def financial_summary():
    """Generate a quick financial summary"""
    db_path = Path.home() / "Library" / "Mail" / "V10" / "MailData" / "Envelope Index"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print("💰 SUBSCRIPTION FINANCIAL SUMMARY")
    print("=" * 60)
    
    cutoff = int((datetime.now() - timedelta(days=1825)).timestamp())  # 5 years
    
    # Get all subscription emails
    query = f"""
    SELECT 
        s.subject,
        m.date_received,
        a.address as sender
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
    AND s.subject LIKE '%$%'
    ORDER BY m.date_received DESC
    """
    
    cursor.execute(query)
    results = cursor.fetchall()
    
    # Process amounts by company and time period
    company_amounts = defaultdict(list)
    monthly_totals = defaultdict(float)
    yearly_data = defaultdict(lambda: defaultdict(float))
    
    for subject, date_recv, sender in results:
        # Extract company
        company = 'Unknown'
        if sender and '@' in sender:
            domain = sender.split('@')[1].split('.')[0]
            company = domain.title()
        
        # Extract all amounts from subject
        amounts = re.findall(r'\$\s*([\d,]+\.?\d*)', subject)
        for amount_str in amounts:
            try:
                amount = float(amount_str.replace(',', ''))
                if 0.01 <= amount <= 10000:  # Reasonable range
                    company_amounts[company].append(amount)
                    
                    # Track by month
                    date = datetime.fromtimestamp(date_recv)
                    month_key = date.strftime('%Y-%m')
                    monthly_totals[month_key] += amount
                    
                    # Track by year
                    year = date.year
                    yearly_data[year][company] += amount
            except:
                pass
    
    # Calculate statistics
    print("\n📊 OVERALL STATISTICS")
    print("-" * 40)
    
    total_companies = len(company_amounts)
    all_amounts = []
    for amounts in company_amounts.values():
        all_amounts.extend(amounts)
    
    if all_amounts:
        print(f"Total payment records: {len(all_amounts)}")
        print(f"Total amount tracked: ${sum(all_amounts):,.2f}")
        print(f"Average payment: ${sum(all_amounts)/len(all_amounts):.2f}")
        print(f"Unique services: {total_companies}")
    
    # Top spending by company
    print("\n💸 TOP 20 SERVICES BY TOTAL SPENDING")
    print("-" * 40)
    
    company_totals = []
    for company, amounts in company_amounts.items():
        total = sum(amounts)
        count = len(amounts)
        avg = total / count if count > 0 else 0
        company_totals.append((company, total, count, avg))
    
    company_totals.sort(key=lambda x: x[1], reverse=True)
    
    for i, (company, total, count, avg) in enumerate(company_totals[:20], 1):
        print(f"{i:2d}. {company:20s} ${total:8.2f} ({count:3d} payments, avg ${avg:.2f})")
    
    # Yearly breakdown
    print("\n📅 SPENDING BY YEAR")
    print("-" * 40)
    
    for year in sorted(yearly_data.keys(), reverse=True):
        year_total = sum(yearly_data[year].values())
        print(f"{year}: ${year_total:,.2f}")
    
    # Recent activity
    print("\n🕐 RECENT ACTIVITY (Last 6 months)")
    print("-" * 40)
    
    six_months_ago = datetime.now() - timedelta(days=180)
    recent_months = []
    
    for month_key in sorted(monthly_totals.keys(), reverse=True):
        month_date = datetime.strptime(month_key, '%Y-%m')
        if month_date >= datetime(six_months_ago.year, six_months_ago.month, 1):
            recent_months.append((month_key, monthly_totals[month_key]))
    
    for month, total in recent_months[:6]:
        print(f"{month}: ${total:,.2f}")
    
    if recent_months:
        recent_avg = sum(t for _, t in recent_months[:6]) / len(recent_months[:6])
        print(f"\nAverage monthly spending (last 6 months): ${recent_avg:,.2f}")
        print(f"Projected annual spending: ${recent_avg * 12:,.2f}")
    
    # Payment patterns
    print("\n📈 PAYMENT AMOUNT DISTRIBUTION")
    print("-" * 40)
    
    if all_amounts:
        ranges = [
            (0, 5, "$0-5"),
            (5, 10, "$5-10"),
            (10, 25, "$10-25"),
            (25, 50, "$25-50"),
            (50, 100, "$50-100"),
            (100, 500, "$100-500"),
            (500, float('inf'), "$500+")
        ]
        
        for min_amt, max_amt, label in ranges:
            count = sum(1 for amt in all_amounts if min_amt < amt <= max_amt)
            if count > 0:
                pct = (count / len(all_amounts)) * 100
                print(f"{label:12s}: {count:4d} payments ({pct:5.1f}%)")
    
    conn.close()

if __name__ == "__main__":
    financial_summary()
