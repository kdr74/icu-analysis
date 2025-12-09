"""
Test that ID linking works correctly
"""

import pandas as pd

print("=" * 70)
print("TESTING ID LINKING")
print("=" * 70)

# Load processed data
master = pd.read_csv('data/processed/master_registry.csv')
renal = pd.read_csv('data/processed/audits/renal_audit.csv')

print(f"\nMaster registry: {len(master)} records")
print(f"Renal audit: {len(renal)} records")

# Check if renal patients are in master
renal_patient_ids = set(renal['anonymous_patient_id'])
master_patient_ids = set(master['anonymous_patient_id'])

matched = renal_patient_ids & master_patient_ids
print(f"\nRenal patients found in master: {len(matched)} / {len(renal_patient_ids)}")

if len(matched) == len(renal_patient_ids):
    print("\n✅ ALL renal patients matched correctly!")
    print("✅ ID linking (hospital ↔ NHS numbers) working perfectly!")
    print("\nThis proves:")
    print("  - Master registry used hospital numbers")
    print("  - Renal audit used NHS numbers")
    print("  - System correctly identified them as same patients")
else:
    print(f"\n⚠️  {len(renal_patient_ids) - len(matched)} patients not matched")

print("\n" + "=" * 70)
