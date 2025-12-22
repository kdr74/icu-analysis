"""
Merge additional data from GICU files into existing master registry records
Uses anonymizer to map hospital numbers to anonymous IDs
"""

import pandas as pd
import numpy as np
from datetime import datetime
import sys
from pathlib import Path
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
print("MERGING ADDITIONAL DATA FROM GICU FILES")
print("=" * 70)

# Load master registry
registry = pd.read_csv('data/processed/master_registry.csv', low_memory=False)
print(f"\nMaster registry: {len(registry):,} records")
print(f"Current columns: {len(registry.columns)}")

# Load GICU files
gicu_admissions = pd.read_csv('data/raw/master/gicu_admissions_summary.csv')
gicu_discharges = pd.read_csv('data/raw/master/gicu_discharges_summary.csv')

# Remove unnamed columns
gicu_admissions = gicu_admissions.loc[:, ~gicu_admissions.columns.str.contains('^Unnamed')]
gicu_discharges = gicu_discharges.loc[:, ~gicu_discharges.columns.str.contains('^Unnamed')]

print(f"\nGICU admissions: {len(gicu_admissions):,} records")
print(f"GICU discharges: {len(gicu_discharges):,} records")

# Combine GICU files
gicu_combined = pd.concat([gicu_admissions, gicu_discharges], ignore_index=True)
print(f"Combined GICU: {len(gicu_combined):,} records")

# Use anonymizer to get anonymous IDs for GICU hospital numbers
print("\nMapping GICU records to anonymous IDs...")
anonymiser = EnhancedPatientAnonymiser()

gicu_anon_ids = {}
for hosp_num in gicu_combined['hospital_number'].dropna().unique():
    anon_id, _ = anonymiser.get_anonymous_id(hosp_num)
    gicu_anon_ids[hosp_num] = anon_id

gicu_combined['anonymous_patient_id'] = gicu_combined['hospital_number'].map(gicu_anon_ids)
mapped = gicu_combined['anonymous_patient_id'].notna().sum()
print(f"✓ Mapped {mapped:,} GICU records to anonymous IDs")

# Calculate age for GICU records
print("\nCalculating ages from DOB...")
gicu_combined['age_at_admission'] = gicu_combined.apply(
    lambda row: calculate_age(row.get('DOB'), row.get('ICU_admit_date')),
    axis=1
)
ages_calculated = gicu_combined['age_at_admission'].notna().sum()
print(f"✓ Calculated age for {ages_calculated:,} GICU records")

# Create matching key: anonymous_patient_id + ICU_admit_date
registry['match_key'] = registry['anonymous_patient_id'].astype(str) + '_' + registry['ICU_admit_date'].astype(str)
gicu_combined['match_key'] = gicu_combined['anonymous_patient_id'].astype(str) + '_' + gicu_combined['ICU_admit_date'].astype(str)

# Find matches
matches = registry['match_key'].isin(gicu_combined['match_key'])
print(f"\nFound {matches.sum():,} matching records to update")

# Columns to exclude from merge
exclude_cols = ['NHS_number', 'DOB', 'hospital_number', 'match_key', 'anonymous_patient_id', 'patient_id_hash']
gicu_data_cols = [col for col in gicu_combined.columns if col not in exclude_cols]

print(f"\nMerging {len(gicu_data_cols)} data columns...")

# Update matched records
updated_fields = {}
updates_made = 0

for idx, row in registry[matches].iterrows():
    match_key = row['match_key']
    gicu_matches = gicu_combined[gicu_combined['match_key'] == match_key]
    
    if len(gicu_matches) == 0:
        continue
    
    # Use first match
    gicu_match = gicu_matches.iloc[0]
    
    for col in gicu_data_cols:
        # Add column if it doesn't exist
        if col not in registry.columns:
            registry[col] = None
        
        # Update if registry has no value and GICU has one
        registry_val = row.get(col)
        gicu_val = gicu_match.get(col)
        
        if pd.isna(registry_val) and pd.notna(gicu_val):
            registry.at[idx, col] = gicu_val
            if col not in updated_fields:
                updated_fields[col] = 0
            updated_fields[col] += 1
            updates_made += 1

# Remove match_key
registry = registry.drop(columns=['match_key'])

print(f"\nTotal updates made: {updates_made:,}")
print(f"\nTop 20 updated fields:")
print(f"{'Field':<45} {'Records Updated':>20}")
print("-" * 67)
for field, count in sorted(updated_fields.items(), key=lambda x: x[1], reverse=True)[:20]:
    if count > 0:
        print(f"{field:<45} {count:>20,}")

print(f"\n✓ Registry now has {len(registry.columns)} columns")

# Show age statistics
if 'age_at_admission' in registry.columns:
    ages = registry['age_at_admission'].dropna()
    print(f"\nAge data:")
    print(f"  Records with age: {len(ages):,} ({(len(ages)/len(registry)*100):.1f}%)")
    if len(ages) > 0:
        print(f"  Age range: {ages.min():.0f} - {ages.max():.0f}")
        print(f"  Mean age: {ages.mean():.1f}")
        print(f"  Median age: {ages.median():.1f}")

# Save
registry.to_csv('data/processed/master_registry.csv', index=False)
print(f"\n✓ Updated registry saved")

print("\n" + "=" * 70)
print("MERGE COMPLETE")
print("=" * 70)
