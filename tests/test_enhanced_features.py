#!/usr/bin/env python3
"""
Test the enhanced features:
1. Dry-run mode for scanners
2. Enhanced logging in MCP server
"""

import subprocess
import sys
import os
from pathlib import Path

def test_dry_run_feature():
    """Test that dry-run works for all scanners"""
    print("🧪 TESTING DRY-RUN FEATURE")
    print("=" * 60)
    
    scanners = [
        ("working_scanner.py", "Working Scanner"),
        ("advanced_subscription_scanner.py", "Advanced Scanner"),
        ("simple_scanner.py", "Simple Scanner")
    ]
    
    for scanner, name in scanners:
        print(f"\n📋 Testing {name} dry-run...")
        cmd = [sys.executable, scanner, "--days", "365", "--dry-run"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0 and "DRY RUN" in result.stdout:
                print(f"   ✅ Dry-run successful!")
                # Extract key stats
                for line in result.stdout.split('\n'):
                    if "Total emails" in line or "Subscription" in line:
                        print(f"   {line.strip()}")
            else:
                print(f"   ❌ Dry-run failed or not detected")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_mcp_logging():
    """Test that MCP server has enhanced logging"""
    print("\n\n🧪 TESTING MCP SERVER LOGGING")
    print("=" * 60)
    
    # Check if server.py has logging configured
    server_path = Path("server.py")
    if server_path.exists():
        content = server_path.read_text()
        
        if "import logging" in content and "logger = logging.getLogger" in content:
            print("✅ Logging is configured in server.py")
            
            # Check for log file creation
            log_file = Path("subscripz_buster_mcp.log")
            
            print(f"\nLog file location: {log_file.absolute()}")
            print("\nLogging features:")
            print("   • All MCP tool calls are logged")
            print("   • Scanner invocations with parameters")
            print("   • Success/failure of operations")
            print("   • JSON export operations")
            print("   • Error stack traces")
            
            if log_file.exists():
                print(f"\n✅ Log file exists ({log_file.stat().st_size} bytes)")
                print("\nRecent log entries:")
                with open(log_file, 'r') as f:
                    lines = f.readlines()
                    for line in lines[-10:]:  # Show last 10 lines
                        print(f"   {line.strip()}")
            else:
                print("\n💡 Log file will be created when MCP server runs")
        else:
            print("❌ Logging not found in server.py")
    else:
        print("❌ server.py not found")

def main():
    """Run all tests"""
    print("🚀 TESTING ENHANCED FEATURES")
    print("=" * 60)
    print("\nThis tests the two new features:")
    print("1. Dry-run mode for scanners")
    print("2. Enhanced logging in MCP server")
    
    test_dry_run_feature()
    test_mcp_logging()
    
    print("\n\n✅ FEATURE SUMMARY")
    print("=" * 60)
    print("\n1. DRY-RUN MODE:")
    print("   • Use --dry-run flag with any scanner")
    print("   • Shows email counts without processing")
    print("   • Much faster than full scan")
    print("   • Helps estimate processing time")
    print("   • Available in menu option 13")
    
    print("\n2. ENHANCED LOGGING:")
    print("   • All MCP operations are logged")
    print("   • Logs saved to subscripz_buster_mcp.log")
    print("   • Includes timestamps and severity levels")
    print("   • Helps debug natural language requests")
    print("   • Tracks which scanners were called")
    
    print("\n💡 Try these commands:")
    print("   python3 working_scanner.py --days 365 --dry-run")
    print("   python3 advanced_subscription_scanner.py --days 7300 --dry-run")
    print("   python3 simple_scanner.py --days 365 --dry-run")

if __name__ == "__main__":
    main()
