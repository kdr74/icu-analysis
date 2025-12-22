"""
Force update ages for ALL records matching GICU discharge file
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from shared.enhanced_anonymiser import EnhancedPatientAnonymiser

def calculate_age(dob, admit_date):
    """Calculate age at admission"""
    try:
        if pd.isna(dob) or pd.isna(admit_date):
            return None
        
        if isinstance(dob, str):
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    dob_dt = datetime.strptime(dob, fmt)
                    break
                except:
                    continue
            else:
                return None
        else:
            dob_dt = pd.to_datetime(dob)
        
        if isinstance(admit_date, str):
            for fmt in ['%d/%m/%Y', '%Y-%m-%d', '%d-%m-%Y']:
                try:
                    admit_dt = datetime.strptime(admit_date, fmt)
                    break
                except:
                    continue
            else:
                return None
        else:
            admit_dt = pd.to_datetime(admit_date)
        
        age = admit_dt.year - dob_dt.year
        if (admit_dt.month, admit_dt.day) < (dob_dt.month, dob_dt.day):
            age -= 1
        
        return age if age >= 0 and age < 150 else None
    except:
        return None

print("=" * 70)
print("FORCE UPDATING AGES FROM GICU DISCHARGE FILE")
print("=" * 70)

# Load files
registry = pd.read_csv('data/processed/master_registry.csv', low_memory=False)
gicu_dis = pd.read_csv('data/raw/master/gicu_discharges_summary.csv')

print(f"\nRegistry: {len(registry):,} records")
print(f"  Records with age: {registry['age_at_admission'].notna().sum():,}")
print(f"  Records without age: {registry['age_at_admission'].isna().sum():,}")

print(f"\nGICU Discharge: {len(gicu_dis):,} records")
print(f"  Records with DOB: {gicu_dis['DOB'].notna().sum():,}")

# Map GICU to anonymous IDs
anonymiser = EnhancedPatientAnonymiser()
gicu_anon_ids = {}
for hosp_num in gicu_dis['hospital_number'].dropna().unique():
    anon_id, _ = anonymiser.get_anonymous_id(hosp_num)
    gicu_anon_ids[hosp_num] = anon_id

gicu_dis['anonymous_patient_id'] = gicu_dis['hospital_number'].map(gicu_anon_ids)

# Calculate ages in GICU file
print("\nCalculating ages...")
gicu_dis['calculated_age'] = gicu_dis.apply(
    lambda row: calculate_age(row.get('DOB'), row.get('ICU_admit_date')),
    axis=1
)
print(f"  Calculated {gicu_dis['calculated_age'].notna().sum():,} ages")

# Create lookup: match_key -> age
age_lookup = {}
for _, row in gicu_dis.iterrows():
    if pd.notna(row['anonymous_patient_id']) and pd.notna(row['ICU_admit_date']) and pd.notna(row['calculated_age']):
        key = f"{row['anonymous_patient_id']}_{row['ICU_admit_date']}"
        age_lookup[key] = row['calculated_age']

print(f"  Created lookup with {len(age_lookup):,} entries")

# Update registry - FORCE UPDATE even if age exists
updated = 0
for idx, row in registry.iterrows():
    if pd.notna(row.get('anonymous_patient_id')) and pd.notna(row.get('ICU_admit_date')):
        key = f"{row['anonymous_patient_id']}_{row['ICU_admit_date']}"
        if key in age_lookup:
            registry.at[idx, 'age_at_admission'] = age_lookup[key]
            updated += 1

print(f"\n✓ Updated {updated:,} records with age data")
print(f"  Total records with age now: {registry['age_at_admission'].notna().sum():,}")

if registry['age_at_admission'].notna().sum() > 0:
    ages = registry['age_at_admission'].dropna()
    print(f"\nAge statistics:")
    print(f"  Count: {len(ages):,} ({len(ages)/len(registry)*100:.1f}%)")
    print(f"  Range: {ages.min():.0f} - {ages.max():.0f}")
    print(f"  Mean: {ages.mean():.1f}")
    print(f"  Median: {ages.median():.1f}")

# Save
registry.to_csv('data/processed/master_registry.csv', index=False)
print(f"\n✓ Registry saved")

print("\n" + "=" * 70)
print("UPDATE COMPLETE")
print("=" * 70)
