#!/usr/bin/env python3
"""
Test the dry-run feature for scanners
This verifies that the --dry-run option works correctly
"""

import subprocess
import sys
from pathlib import Path

def test_dry_run():
    """Test dry-run feature for various scanners"""
    print("🧪 TESTING DRY-RUN FEATURE")
    print("=" * 60)
    
    scanners = [
        ("working_scanner", "Working Scanner"),
        ("advanced_subscription_scanner", "Advanced Scanner"),
        ("simple_scanner", "Simple Scanner")
    ]
    
    for scanner_file, scanner_name in scanners:
        print(f"\n📋 Testing {scanner_name}...")
        
        # Check if scanner exists
        if not Path(f"{scanner_file}.py").exists():
            print(f"   ⚠️  Scanner not found: {scanner_file}.py")
            continue
        
        # Run with dry-run
        cmd = [sys.executable, f"{scanner_file}.py", "--days", "365", "--dry-run"]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                output = result.stdout
                
                # Check for dry-run indicators
                if "DRY RUN" in output:
                    print(f"   ✅ Dry-run mode detected")
                    
                    # Extract statistics
                    for line in output.split('\n'):
                        if "Total emails" in line:
                            print(f"   {line.strip()}")
                        elif "Subscription" in line and "emails" in line:
                            print(f"   {line.strip()}")
                        elif "Percentage" in line:
                            print(f"   {line.strip()}")
                else:
                    print(f"   ⚠️  No dry-run output detected")
            else:
                print(f"   ❌ Error: {result.stderr}")
                
        except subprocess.TimeoutExpired:
            print(f"   ❌ Timeout - scanner took too long")
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n✅ Dry-run testing complete!")
    print("\nDry-run allows you to:")
    print("• See how many emails would be processed")
    print("• Estimate processing time")
    print("• Verify scanner is working before full scan")
    print("• No actual processing or file creation")

if __name__ == "__main__":
    test_dry_run()
