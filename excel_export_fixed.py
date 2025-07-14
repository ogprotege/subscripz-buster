#!/usr/bin/env python3
"""
Fixed Excel exporter that works with Subscription objects from advanced scanner
"""

import pandas as pd
from datetime import datetime
from pathlib import Path
from collections import defaultdict
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils.dataframe import dataframe_to_rows

# Import the scanner and data structures
from advanced_subscription_scanner import AdvancedSubscriptionScanner
from common_structures import format_currency

class FixedExcelExporter:
    """Excel exporter that properly handles Subscription objects"""
    
    def __init__(self, subscriptions=None):
        self.subscriptions = subscriptions or {}
    
    def export_to_excel(self, subscriptions, filename: str = None):
        """Export subscription data to Excel with multiple analysis sheets"""
        self.subscriptions = subscriptions
        
        if not self.subscriptions:
            print("No data to export.")
            return None
            
        if not filename:
            filename = f"subscriptions_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        filepath = Path.home() / "Desktop" / filename
        
        # Create workbook
        wb = Workbook()
        wb.remove(wb.active)  # Remove default sheet
        
        # 1. Summary Dashboard
        self._create_summary_sheet(wb)
        
        # 2. All Subscriptions
        self._create_subscriptions_sheet(wb)
        
        # 3. Duplicate Analysis
        self._create_duplicates_sheet(wb)
        
        # 4. Account Breakdown
        self._create_account_sheet(wb)
        
        # 5. Timeline Analysis
        self._create_timeline_sheet(wb)
        
        # Save workbook
        wb.save(filepath)
        print(f"\n✅ Excel report saved to: {filepath}")
        return filepath
    
    def _create_summary_sheet(self, wb):
        """Create summary dashboard"""
        ws = wb.create_sheet("Summary Dashboard")
        
        # Title
        ws['A1'] = "Subscription Analysis Summary"
        ws['A1'].font = Font(size=16, bold=True)
        ws['A2'] = f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Count subscriptions by status
        status_counts = defaultdict(int)
        for data in self.subscriptions.values():
            status_counts[data.status] += 1
        
        # Key metrics
        row = 4
        ws['A4'] = "KEY METRICS"
        ws['A4'].font = Font(bold=True)
        
        metrics = [
            ("Total Unique Subscriptions", len(self.subscriptions)),
            ("Active Subscriptions", status_counts.get('active', 0)),
            ("Cancelled Subscriptions", status_counts.get('cancelled', 0)),
            ("Trial Subscriptions", status_counts.get('trial', 0)),
            ("Payment Issues", status_counts.get('failed', 0) + status_counts.get('past_due', 0)),
            ("Inactive Subscriptions", status_counts.get('inactive', 0)),
        ]
        
        for metric, value in metrics:
            row += 1
            ws[f'A{row}'] = metric
            ws[f'B{row}'] = value
        
        # Financial summary
        row += 2
        ws[f'A{row}'] = "FINANCIAL SUMMARY"
        ws[f'A{row}'].font = Font(bold=True)
        
        total_monthly = 0
        total_cancelled_savings = 0
        
        for company, data in self.subscriptions.items():
            if data.avg_amount and data.avg_amount > 0:
                if data.status == 'active':
                    if data.frequency == 'annual':
                        total_monthly += data.avg_amount / 12
                    else:
                        total_monthly += data.avg_amount
                elif data.status == 'cancelled':
                    if data.frequency == 'annual':
                        total_cancelled_savings += data.avg_amount / 12
                    else:
                        total_cancelled_savings += data.avg_amount
        
        financial_metrics = [
            ("Estimated Monthly Active", format_currency(total_monthly)),
            ("Estimated Annual Active", format_currency(total_monthly * 12)),
            ("Monthly Cancelled Savings", format_currency(total_cancelled_savings)),
            ("Annual Cancelled Savings", format_currency(total_cancelled_savings * 12)),
        ]
        
        for metric, value in financial_metrics:
            row += 1
            ws[f'A{row}'] = metric
            ws[f'B{row}'] = value
        
        # Format columns
        ws.column_dimensions['A'].width = 30
        ws.column_dimensions['B'].width = 15
    
    def _create_subscriptions_sheet(self, wb):
        """Create detailed subscriptions list"""
        ws = wb.create_sheet("All Subscriptions")
        
        # Prepare data
        rows = []
        for company, data in self.subscriptions.items():
            # Calculate monthly amount based on frequency
            monthly_amount = 0
            if data.avg_amount:
                if data.frequency == 'annual':
                    monthly_amount = data.avg_amount / 12
                elif data.frequency == 'quarterly':
                    monthly_amount = data.avg_amount / 3
                else:
                    monthly_amount = data.avg_amount
            
            # Get primary sender email
            sender_email = 'Unknown'
            if data.emails:
                sender_email = data.emails[0].sender
            elif hasattr(data, 'metadata') and data.metadata and 'full_senders' in data.metadata:
                senders = data.metadata.get('full_senders', [])
                if senders:
                    sender_email = list(senders)[0]
            
            rows.append({
                'Company': company,
                'Status': data.status.upper(),
                'Accounts': ', '.join(sorted(data.accounts)),
                'Account Count': len(data.accounts),
                'Sender Email': sender_email,
                'Monthly Cost': monthly_amount,
                'Annual Cost': monthly_amount * 12,
                'Frequency': data.frequency or 'unknown',
                'Email Count': data.email_count,
                'First Seen': data.first_seen.strftime('%Y-%m-%d'),
                'Last Seen': data.last_seen.strftime('%Y-%m-%d'),
                'Days Since Last': (datetime.now() - data.last_seen).days,
            })
        
        # Create DataFrame and add to sheet
        df = pd.DataFrame(rows)
        df = df.sort_values('Monthly Cost', ascending=False)
        
        # Headers
        headers = list(df.columns)
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
            cell.font = Font(color="FFFFFF", bold=True)
        
        # Data
        for r_idx, row in enumerate(dataframe_to_rows(df, index=False, header=False), 2):
            for c_idx, value in enumerate(row, 1):
                cell = ws.cell(row=r_idx, column=c_idx, value=value)
                
                # Color code by status
                if c_idx == 2:  # Status column
                    if value == 'ACTIVE':
                        cell.fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                    elif value == 'CANCELLED':
                        cell.fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                    elif value in ['FAILED', 'PAST_DUE']:
                        cell.fill = PatternFill(start_color="FFEB9C", end_color="FFEB9C", fill_type="solid")
                
                # Format currency
                if c_idx in [5, 6]:  # Amount columns
                    cell.number_format = '"$"#,##0.00'
        
        # Auto-fit columns
        for column in ws.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            ws.column_dimensions[column_letter].width = adjusted_width
    
    def _create_duplicates_sheet(self, wb):
        """Create duplicate analysis sheet"""
        ws = wb.create_sheet("Duplicate Analysis")
        
        # Find duplicates (services on multiple accounts)
        duplicates = []
        for company, data in self.subscriptions.items():
            if len(data.accounts) > 1:
                monthly_waste = 0
                if data.avg_amount:
                    if data.frequency == 'annual':
                        monthly_waste = (data.avg_amount / 12) * (len(data.accounts) - 1)
                    else:
                        monthly_waste = data.avg_amount * (len(data.accounts) - 1)
                
                duplicates.append({
                    'company': company,
                    'accounts': data.accounts,
                    'count': len(data.accounts),
                    'monthly_waste': monthly_waste,
                    'status': data.status,
                    'last_seen': data.last_seen
                })
        
        if not duplicates:
            ws['A1'] = "No duplicate subscriptions found!"
            return
        
        ws['A1'] = "Duplicate Subscription Analysis"
        ws['A1'].font = Font(size=14, bold=True)
        
        # Sort by waste amount
        duplicates.sort(key=lambda x: x['monthly_waste'], reverse=True)
        
        # Headers
        row = 3
        headers = ['Service', 'Accounts', 'Count', 'Monthly Waste', 'Annual Waste', 'Status', 'Last Seen']
        for col, header in enumerate(headers, 1):
            cell = ws.cell(row=row, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
        
        # Data
        total_monthly_waste = 0
        row = 4
        for dup in duplicates:
            ws[f'A{row}'] = dup['company']
            ws[f'B{row}'] = ', '.join(sorted(dup['accounts']))
            ws[f'C{row}'] = dup['count']
            ws[f'D{row}'] = dup['monthly_waste']
            ws[f'D{row}'].number_format = '"$"#,##0.00'
            ws[f'E{row}'] = dup['monthly_waste'] * 12
            ws[f'E{row}'].number_format = '"$"#,##0.00'
            ws[f'F{row}'] = dup['status'].upper()
            ws[f'G{row}'] = dup['last_seen'].strftime('%Y-%m-%d')
            
            total_monthly_waste += dup['monthly_waste']
            row += 1
        
        # Total waste summary
        row += 1
        ws[f'A{row}'] = "TOTAL MONTHLY DUPLICATE WASTE:"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        ws[f'D{row}'] = total_monthly_waste
        ws[f'D{row}'].number_format = '"$"#,##0.00'
        ws[f'D{row}'].font = Font(size=12, bold=True, color="FF0000")
        
        row += 1
        ws[f'A{row}'] = "TOTAL ANNUAL DUPLICATE WASTE:"
        ws[f'A{row}'].font = Font(size=12, bold=True)
        ws[f'D{row}'] = total_monthly_waste * 12
        ws[f'D{row}'].number_format = '"$"#,##0.00'
        ws[f'D{row}'].font = Font(size=12, bold=True, color="FF0000")
    
    def _create_account_sheet(self, wb):
        """Create account breakdown sheet"""
        ws = wb.create_sheet("By Account")
        
        # Aggregate by account
        account_data = defaultdict(lambda: {
            'subscriptions': [],
            'total_monthly': 0,
            'active_count': 0,
            'cancelled_count': 0
        })
        
        for company, data in self.subscriptions.items():
            monthly_amount = 0
            if data.avg_amount:
                if data.frequency == 'annual':
                    monthly_amount = data.avg_amount / 12
                else:
                    monthly_amount = data.avg_amount
            
            for account in data.accounts:
                acc = account_data[account]
                acc['subscriptions'].append({
                    'company': company,
                    'amount': monthly_amount,
                    'status': data.status,
                    'last_seen': data.last_seen
                })
                
                if data.status == 'active':
                    acc['total_monthly'] += monthly_amount
                    acc['active_count'] += 1
                elif data.status == 'cancelled':
                    acc['cancelled_count'] += 1
        
        # Create summary
        row = 1
        ws['A1'] = "Subscription Breakdown by Email Account"
        ws['A1'].font = Font(size=14, bold=True)
        
        row = 3
        
        for account, acc_data in sorted(account_data.items(), 
                                      key=lambda x: x[1]['total_monthly'], 
                                      reverse=True):
            # Account header
            ws[f'A{row}'] = account
            ws[f'A{row}'].font = Font(bold=True, size=12)
            ws[f'B{row}'] = f"Total Monthly: ${acc_data['total_monthly']:.2f}"
            ws[f'C{row}'] = f"({acc_data['active_count']} active, {acc_data['cancelled_count']} cancelled)"
            row += 1
            
            # Subscription details
            for sub in sorted(acc_data['subscriptions'], 
                            key=lambda x: x['amount'], 
                            reverse=True):
                ws[f'B{row}'] = sub['company']
                ws[f'C{row}'] = sub['amount']
                ws[f'C{row}'].number_format = '"$"#,##0.00'
                ws[f'D{row}'] = sub['status'].upper()
                ws[f'E{row}'] = sub['last_seen'].strftime('%Y-%m-%d')
                
                # Color code
                if sub['status'] == 'active':
                    ws[f'D{row}'].fill = PatternFill(start_color="C6EFCE", end_color="C6EFCE", fill_type="solid")
                elif sub['status'] == 'cancelled':
                    ws[f'D{row}'].fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
                
                row += 1
            
            row += 1  # Space between accounts
    
    def _create_timeline_sheet(self, wb):
        """Create timeline analysis sheet"""
        ws = wb.create_sheet("Timeline Analysis")
        
        ws['A1'] = "Subscription Activity Timeline"
        ws['A1'].font = Font(size=14, bold=True)
        
        # Categorize by last activity
        categories = {
            'Active (< 30 days)': [],
            'Recent (30-90 days)': [],
            'Inactive (90-180 days)': [],
            'Dormant (180-365 days)': [],
            'Ancient (> 365 days)': []
        }
        
        now = datetime.now()
        
        for company, data in self.subscriptions.items():
            days_ago = (now - data.last_seen).days
            monthly_amount = 0
            if data.avg_amount:
                if data.frequency == 'annual':
                    monthly_amount = data.avg_amount / 12
                else:
                    monthly_amount = data.avg_amount
            
            item = {
                'company': company,
                'last_date': data.last_seen,
                'days_ago': days_ago,
                'amount': monthly_amount,
                'status': data.status,
                'accounts': len(data.accounts)
            }
            
            if days_ago < 30:
                categories['Active (< 30 days)'].append(item)
            elif days_ago < 90:
                categories['Recent (30-90 days)'].append(item)
            elif days_ago < 180:
                categories['Inactive (90-180 days)'].append(item)
            elif days_ago < 365:
                categories['Dormant (180-365 days)'].append(item)
            else:
                categories['Ancient (> 365 days)'].append(item)
        
        row = 3
        
        for category, items in categories.items():
            if not items:
                continue
                
            # Category header
            ws[f'A{row}'] = category
            ws[f'A{row}'].font = Font(bold=True, size=12)
            ws[f'B{row}'] = f"({len(items)} subscriptions)"
            row += 1
            
            # Headers
            headers = ['Company', 'Last Activity', 'Days Ago', 'Monthly Cost', 'Status', 'Accounts']
            for col, header in enumerate(headers, 1):
                cell = ws.cell(row=row, column=col, value=header)
                cell.font = Font(bold=True)
                cell.fill = PatternFill(start_color="D9D9D9", end_color="D9D9D9", fill_type="solid")
            row += 1
            
            # Items
            for item in sorted(items, key=lambda x: x['days_ago']):
                ws[f'A{row}'] = item['company']
                ws[f'B{row}'] = item['last_date'].strftime('%Y-%m-%d')
                ws[f'C{row}'] = item['days_ago']
                ws[f'D{row}'] = item['amount']
                ws[f'D{row}'].number_format = '"$"#,##0.00'
                ws[f'E{row}'] = item['status'].upper()
                ws[f'F{row}'] = item['accounts']
                
                # Highlight potentially forgotten subscriptions
                if item['days_ago'] > 180 and item['status'] == 'active':
                    for col in range(1, 7):
                        ws.cell(row=row, column=col).fill = PatternFill(
                            start_color="FFEB9C", end_color="FFEB9C", fill_type="solid"
                        )
                
                row += 1
            
            row += 1  # Space between categories


def main():
    """Run the advanced scanner and export to Excel"""
    print("🚀 Advanced Subscription Scanner with Fixed Excel Export")
    print("=" * 60)
    
    # Run the scanner
    scanner = AdvancedSubscriptionScanner()
    subscriptions = scanner.scan_emails(days_back=7300)  # 20 years
    
    # Display results
    scanner.display_results()
    
    # Export to Excel
    print("\n📊 Generating Excel report...")
    exporter = FixedExcelExporter()
    filepath = exporter.export_to_excel(subscriptions)
    
    if filepath:
        print(f"\n✨ Complete! Open the Excel file to see:")
        print("  • Summary dashboard with key metrics")
        print("  • All subscriptions with amounts and status")
        print("  • Duplicate analysis with waste calculations")
        print("  • Breakdown by email account")
        print("  • Timeline showing inactive subscriptions")


if __name__ == "__main__":
    main()
