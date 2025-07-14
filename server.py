"""
subscripz-buster: MCP Server with Standardized JSON Output
This MCP server uses the standardized scanner infrastructure for consistent data handling.
"""

import os
import json
import tempfile
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from mcp.server.fastmcp import FastMCP
import subprocess
import sys

# Set up logging
# Use a log file in the project directory instead of trying to write to root
log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'subscripz_buster_mcp.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file_path),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('subscripz-buster-mcp')

# Import common structures for data handling
try:
    from common_structures import ScanResults, format_currency
    COMMON_STRUCTURES_AVAILABLE = True
except ImportError:
    COMMON_STRUCTURES_AVAILABLE = False

mcp = FastMCP(
    "subscripz-buster",
    description="Universal subscription hunter that scans Apple Mail for all your subscriptions"
)

# Store the latest scan results for use across tools
latest_scan_results = None

def run_scanner(scanner_name: str, days_back: int = 365, output_json: bool = True) -> Optional[ScanResults]:
    """
    Run a scanner script and optionally get JSON results.
    This provides consistent data output from any scanner.
    """
    global latest_scan_results
    
    logger.info(f"Running scanner: {scanner_name} with days_back={days_back}, output_json={output_json}")
    
    # Build command
    cmd = [sys.executable, f"{scanner_name}.py", "--days", str(days_back)]
    
    # Add JSON output if requested
    json_file = None
    if output_json and COMMON_STRUCTURES_AVAILABLE:
        # Create temporary file for JSON output
        fd, json_file = tempfile.mkstemp(suffix='.json')
        os.close(fd)
        cmd.extend(["--output-json", json_file])
        logger.debug(f"JSON output will be saved to: {json_file}")
    
    # Add quiet flag to reduce console output when using JSON
    if output_json:
        cmd.append("--quiet")
    
    logger.debug(f"Command: {' '.join(cmd)}")
    
    try:
        # Run the scanner
        logger.info(f"Executing scanner subprocess...")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        logger.info(f"Scanner completed with return code: {result.returncode}")
        
        # Get console output
        output = result.stdout
        if result.stderr:
            logger.warning(f"Scanner stderr: {result.stderr}")
            output += f"\n\nErrors:\n{result.stderr}"
        
        # Load JSON results if available
        if json_file and os.path.exists(json_file):
            try:
                logger.info(f"Loading JSON results from: {json_file}")
                with open(json_file, 'r') as f:
                    scan_data = json.load(f)
                    
                # Log summary statistics
                if isinstance(scan_data, dict):
                    logger.info(f"Scan found {scan_data.get('unique_subscriptions_count', 0)} subscriptions")
                    logger.info(f"Total emails scanned: {scan_data.get('total_emails_scanned', 0)}")
                    
                # Convert back to ScanResults object if possible
                if COMMON_STRUCTURES_AVAILABLE:
                    # This is simplified - in production you'd properly deserialize
                    latest_scan_results = scan_data
                    
                # Clean up temp file
                os.unlink(json_file)
                logger.debug(f"Cleaned up temp file: {json_file}")
            except Exception as e:
                logger.error(f"Error loading JSON results: {str(e)}")
                output += f"\n\nError loading JSON results: {str(e)}"
        
        return output
        
    except Exception as e:
        logger.error(f"Error running scanner: {str(e)}", exc_info=True)
        return f"Error running scanner: {str(e)}"

@mcp.tool()
def scan_all_subscriptions(days_back: int = 365) -> str:
    """
    Scan all your email accounts for subscriptions.
    Uses the working scanner with normalized database support.
    
    Args:
        days_back: How many days of history to scan (default: 365)
    """
    logger.info(f"MCP Tool called: scan_all_subscriptions(days_back={days_back})")
    return run_scanner("working_scanner", days_back, output_json=True)

@mcp.tool()
def comprehensive_scan(days_back: int = 1825) -> str:
    """
    Run a comprehensive scan showing ALL subscriptions.
    Shows complete categorized results and saves detailed JSON.
    
    Args:
        days_back: How many days of history to scan (default: 1825 = 5 years)
    """
    logger.info(f"MCP Tool called: comprehensive_scan(days_back={days_back})")
    return run_scanner("comprehensive_scanner", days_back, output_json=True)

@mcp.tool()
def advanced_scan(days_back: int = 7300) -> str:
    """
    Run advanced scan with 100+ keywords and spam filtering.
    Provides the most thorough detection of subscriptions.
    
    Args:
        days_back: How many days of history to scan (default: 7300 = 20 years)
    """
    logger.info(f"MCP Tool called: advanced_scan(days_back={days_back})")
    return run_scanner("advanced_subscription_scanner", days_back, output_json=True)

@mcp.tool()
def find_duplicate_subscriptions() -> str:
    """
    Find subscriptions you're paying for multiple times across different accounts.
    This tool specifically focuses on identifying duplicates and calculating waste.
    """
    logger.info("MCP Tool called: find_duplicate_subscriptions()")
    
    # If we have recent scan results, use them
    if latest_scan_results and isinstance(latest_scan_results, dict):
        logger.debug("Using cached scan results for duplicate analysis")
        duplicates = latest_scan_results.get('duplicate_subscriptions', [])
        
        if not duplicates:
            return "✅ Good news! No duplicate subscriptions found across your accounts."
        
        output = f"⚠️  Found {len(duplicates)} duplicate subscriptions!\n"
        output += "=" * 60 + "\n\n"
        
        total_waste = 0
        for dup in duplicates:
            output += f"🔄 {dup['company']}\n"
            output += f"   On {len(dup['accounts'])} accounts: {', '.join(dup['accounts'])}\n"
            if dup.get('monthly_waste', 0) > 0:
                output += f"   💸 Monthly waste: {format_currency(dup['monthly_waste'])}\n"
                total_waste += dup['monthly_waste']
            output += "\n"
        
        if total_waste > 0:
            output += f"\n💰 Total monthly waste: {format_currency(total_waste)}\n"
            output += f"💰 Annual waste: {format_currency(total_waste * 12)}\n"
        
        return output
    else:
        # Fall back to running duplicate finder
        return run_scanner("duplicate_finder", 365, output_json=False)

@mcp.tool()
def financial_summary() -> str:
    """
    Get a quick financial summary of your subscriptions.
    Shows total costs, top spenders, and potential savings.
    """
    # If we have recent scan results, use them
    if latest_scan_results and isinstance(latest_scan_results, dict):
        financial = latest_scan_results.get('financial_summary', {})
        
        output = "💰 SUBSCRIPTION FINANCIAL SUMMARY\n"
        output += "=" * 60 + "\n\n"
        
        output += f"Monthly total: {format_currency(financial.get('monthly_total', 0))}\n"
        output += f"Annual total: {format_currency(financial.get('annual_total', 0))}\n\n"
        
        if financial.get('duplicate_monthly_waste', 0) > 0:
            output += f"Duplicate monthly waste: {format_currency(financial['duplicate_monthly_waste'])}\n"
            output += f"Potential annual savings: {format_currency(financial['duplicate_annual_waste'])}\n"
        
        # Add subscription count
        if 'unique_subscriptions' in latest_scan_results:
            output += f"\nTotal subscriptions: {len(latest_scan_results['unique_subscriptions'])}\n"
            
            # Count by status
            status_counts = {}
            for sub in latest_scan_results['unique_subscriptions']:
                status = sub.get('status', 'unknown')
                status_counts[status] = status_counts.get(status, 0) + 1
            
            output += "\nBy status:\n"
            for status, count in sorted(status_counts.items(), key=lambda x: x[1], reverse=True):
                output += f"  {status}: {count}\n"
        
        return output
    else:
        # Fall back to running financial summary
        return run_scanner("financial_summary", 365, output_json=False)

@mcp.tool()
def export_to_excel(filename: str = "subscriptions_report.xlsx") -> str:
    """
    Export all subscription data to an Excel file with multiple analysis sheets.
    Includes summary, all subscriptions, duplicates, and provider analysis.
    
    Args:
        filename: Output filename (default: subscriptions_report.xlsx)
    """
    # Run the Excel export scanner
    cmd = [sys.executable, "subscription_scanner_excel.py"]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            output = result.stdout
            if f"Exported to {filename}" in output or "Excel file saved" in output:
                return f"✅ Successfully exported comprehensive subscription report to {filename}\n\nThe Excel file includes:\n• Summary dashboard\n• All subscriptions\n• Duplicate analysis\n• Account breakdown\n• Payment issues\n• Timeline analysis"
            else:
                return output
        else:
            return f"Error: {result.stderr}"
            
    except Exception as e:
        return f"Error exporting to Excel: {str(e)}"

@mcp.tool()
def export_to_csv(days_back: int = 365) -> str:
    """
    Export subscription data to CSV for custom analysis.
    Creates a simple CSV with all subscription emails.
    
    Args:
        days_back: How many days of history to export (default: 365)
    """
    return run_scanner("export_to_csv", days_back, output_json=False)

@mcp.tool()
def find_inactive_subscriptions(months_inactive: int = 6) -> str:
    """
    Find subscriptions you haven't heard from in months.
    These might be services you're still paying for but not using.
    
    Args:
        months_inactive: How many months of inactivity to check (default: 6)
    """
    # If we have scan results, analyze them
    if latest_scan_results and isinstance(latest_scan_results, dict):
        inactive = []
        cutoff_days = months_inactive * 30
        
        for sub in latest_scan_results.get('unique_subscriptions', []):
            if sub.get('days_since_last', 0) > cutoff_days and sub.get('status') != 'cancelled':
                inactive.append(sub)
        
        if not inactive:
            return f"✅ No subscriptions have been inactive for more than {months_inactive} months."
        
        output = f"⚠️  Found {len(inactive)} potentially forgotten subscriptions:\n"
        output += f"(No emails in the last {months_inactive} months)\n"
        output += "=" * 60 + "\n\n"
        
        for sub in sorted(inactive, key=lambda x: x.get('days_since_last', 0), reverse=True):
            months_ago = sub['days_since_last'] // 30
            output += f"❓ {sub['company']}\n"
            output += f"   Last seen: {months_ago} months ago\n"
            if sub.get('avg_amount'):
                output += f"   Amount: {format_currency(sub['avg_amount'])}"
                if sub.get('frequency'):
                    output += f" ({sub['frequency']})"
                output += "\n"
            output += f"   Status: {sub.get('status', 'unknown')}\n\n"
        
        return output
    else:
        # Need to run a scan first
        return "Please run scan_all_subscriptions first to find inactive subscriptions."

@mcp.tool()
def analyze_spending_by_category() -> str:
    """
    Analyze subscription spending by category.
    Groups subscriptions into categories like streaming, software, news, etc.
    """
    if not latest_scan_results:
        return "Please run scan_all_subscriptions first to analyze spending."
    
    # Define categories
    categories = {
        'Streaming': ['netflix', 'hulu', 'disney', 'hbo', 'paramount', 'peacock', 'youtube', 'spotify', 'apple music'],
        'Software': ['adobe', 'microsoft', 'notion', 'evernote', 'dropbox', 'slack', 'zoom', 'figma'],
        'News & Media': ['nytimes', 'wsj', 'economist', 'medium', 'substack', 'washington post'],
        'Gaming': ['xbox', 'playstation', 'steam', 'epic', 'nintendo', 'twitch'],
        'Fitness': ['peloton', 'strava', 'myfitnesspal', 'headspace', 'calm'],
        'Other': []
    }
    
    category_spending = {cat: 0 for cat in categories}
    category_counts = {cat: 0 for cat in categories}
    
    # Categorize subscriptions
    for sub in latest_scan_results.get('unique_subscriptions', []):
        company_lower = sub['company'].lower()
        categorized = False
        
        for category, keywords in categories.items():
            if category != 'Other':
                for keyword in keywords:
                    if keyword in company_lower:
                        if sub.get('avg_amount') and sub.get('status') == 'active':
                            amount = sub['avg_amount']
                            if sub.get('frequency') == 'annual':
                                amount = amount / 12
                            category_spending[category] += amount
                        category_counts[category] += 1
                        categorized = True
                        break
                if categorized:
                    break
        
        if not categorized:
            if sub.get('avg_amount') and sub.get('status') == 'active':
                amount = sub['avg_amount']
                if sub.get('frequency') == 'annual':
                    amount = amount / 12
                category_spending['Other'] += amount
            category_counts['Other'] += 1
    
    output = "📊 SUBSCRIPTION SPENDING BY CATEGORY\n"
    output += "=" * 60 + "\n\n"
    
    total_spending = sum(category_spending.values())
    
    for category in sorted(category_spending.keys(), key=lambda x: category_spending[x], reverse=True):
        if category_counts[category] > 0:
            spending = category_spending[category]
            percentage = (spending / total_spending * 100) if total_spending > 0 else 0
            
            output += f"{category}:\n"
            output += f"  Count: {category_counts[category]} subscriptions\n"
            output += f"  Monthly: {format_currency(spending)}\n"
            output += f"  Annual: {format_currency(spending * 12)}\n"
            output += f"  Percentage: {percentage:.1f}%\n\n"
    
    output += f"TOTAL MONTHLY: {format_currency(total_spending)}\n"
    output += f"TOTAL ANNUAL: {format_currency(total_spending * 12)}\n"
    
    return output

@mcp.tool()
def search_subscription(company_name: str) -> str:
    """
    Search for a specific subscription by company name.
    Shows detailed information about emails from that company.
    
    Args:
        company_name: Name of the company to search for
    """
    if not latest_scan_results:
        return "Please run scan_all_subscriptions first to search for subscriptions."
    
    search_lower = company_name.lower()
    found = []
    
    for sub in latest_scan_results.get('unique_subscriptions', []):
        if search_lower in sub['company'].lower():
            found.append(sub)
    
    if not found:
        return f"No subscriptions found matching '{company_name}'"
    
    output = f"🔍 Found {len(found)} subscription(s) matching '{company_name}':\n"
    output += "=" * 60 + "\n\n"
    
    for sub in found:
        output += f"📌 {sub['company']}\n"
        output += f"   📧 Emails: {sub['email_count']}\n"
        output += f"   👤 Accounts: {', '.join(sub['accounts'])}\n"
        
        if sub.get('avg_amount'):
            output += f"   💰 Amount: {format_currency(sub['avg_amount'])}"
            if sub.get('frequency'):
                output += f" ({sub['frequency']})"
            output += "\n"
        
        output += f"   📅 First seen: {sub['first_seen']}\n"
        output += f"   📅 Last seen: {sub['last_seen']} ({sub.get('days_since_last', 0)} days ago)\n"
        output += f"   🚦 Status: {sub['status']}\n"
        
        if sub.get('recent_subject'):
            output += f"   📝 Recent email: {sub['recent_subject'][:60]}...\n"
        
        output += "\n"
    
    return output

if __name__ == "__main__":
    mcp.run()
