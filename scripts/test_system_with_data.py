"""
Test the complete system with generated test data
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and report results"""
    print("\n" + "=" * 70)
    print(description)
    print("=" * 70)
    print(f"Running: {cmd}\n")
    
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode == 0:
        print(f"\n✓ {description} - SUCCESS")
        return True
    else:
        print(f"\n✗ {description} - FAILED")
        return False

def main():
    print("=" * 70)
    print("SYSTEM TEST WITH TEST DATA")
    print("=" * 70)
    print("\nThis will test all components with the generated test data.")
    print("All test files are prefixed with 'TEST_' for easy deletion later.\n")
    
    input("Press Enter to begin testing...")
    
    # Test 1: Process master registry
    success = run_command(
        "python scripts/master/process_master_registry.py data/raw/master/TEST_master_data.xlsx hospital_number",
        "TEST 1: Process Master Registry"
    )
    
    if not success:
        print("\n❌ Master registry processing failed. Check errors above.")
        return
    
    # Test 2: Process ventilation audit
    success = run_command(
        "python scripts/audits/ventilation/ventilation_audit.py data/raw/audits/ventilation/TEST_ventilation_audit.xlsx hospital_number",
        "TEST 2: Process Ventilation Audit"
    )
    
    # Test 3: Process renal audit (uses NHS numbers to test ID linking)
    success = run_command(
        "python scripts/audits/renal/renal_audit.py data/raw/audits/renal/TEST_renal_audit.xlsx nhs_number",
        "TEST 3: Process Renal Audit (tests NHS number linking)"
    )
    
    # Test 4: Process CRBSI audit
    success = run_command(
        "python scripts/audits/crbsi/crbsi_audit.py data/raw/audits/crbsi/TEST_crbsi_audit.xlsx hospital_number",
        "TEST 4: Process CRBSI Audit"
    )
    
    # Test 5: Process cardiac audit
    success = run_command(
        "python scripts/audits/cardiac/cardiac_audit.py data/raw/audits/cardiac/TEST_cardiac_audit.xlsx hospital_number",
        "TEST 5: Process Cardiac Audit"
    )
    
    # Summary
    print("\n" + "=" * 70)
    print("SYSTEM TEST COMPLETE")
    print("=" * 70)
    
    print("\n✅ All tests completed!")
    
    print("\n📊 Check your results:")
    print("  Master registry:")
    print("    - data/processed/master_registry.csv")
    print("  Audit data:")
    print("    - data/processed/audits/ventilation_audit.csv")
    print("    - data/processed/audits/renal_audit.csv")
    print("    - data/processed/audits/crbsi_audit.csv")
    print("    - data/processed/audits/cardiac_audit.csv")
    
    print("\n🔍 Verify data protection:")
    print("  1. Check no patient names:")
    print("     head -20 data/processed/master_registry.csv")
    print("  2. Check postcodes are areas only (e.g., BS2 not BS2 8HW)")
    print("  3. Check ages not DOBs")
    print("  4. Check anonymous IDs (ICU-000001, etc.)")
    
    print("\n🗑️  When ready to delete test data, run:")
    print("     python scripts/delete_test_data.py")

if __name__ == "__main__":
    main()
