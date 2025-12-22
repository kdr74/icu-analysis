"""
Standardize column names across different data sources
Maps variations to consistent standard names
"""

import pandas as pd
from pathlib import Path

# Standard column mapping
COLUMN_STANDARDIZATION = {
    # ICU ward/unit
    'Unit': 'icu_ward',
    'unit': 'icu_ward',
    'ICU_unit': 'icu_ward',
    'ward': 'icu_ward',
    
    # ICU admission date
    'Ward Attendance Start Date': 'ICU_admit_date',
    'ICU_admission_date': 'ICU_admit_date',
    'icu_admission_datetime': 'ICU_admit_date',
    'admission_date': 'ICU_admit_date',
    
    # ICU discharge date
    'Ward Attendance End Date': 'ICU_discharge_date',
    'ICU_discharge_datetime': 'ICU_discharge_date',
    'discharge_date': 'ICU_discharge_date',
    
    # Hospital admission
    'Hospital Admission Date': 'hospital_admit_date',
    'hosp_admission_date': 'hospital_admit_date',
    
    # Hospital discharge
    'Hospital Discharge Date': 'BRI_hospital_discharge_date',
    'hosp_discharge_date': 'BRI_hospital_discharge_date',
    
    # Consultant
    'Consultant': 'consultant',
    'CONSULTANT': 'consultant',
    
    # Discharge method
    'Discharge Method': 'discharge_method',
    
    # Discharge destination
    'Discharge Destination': 'BRI_discharge_destination',
    
    # Patient classification
    'Patient Classification': 'patient_classification',
    
    # Hours in ward
    'Hours in Ward': 'hours_on_ward_sls',
    
    # Specialty
    'Specialty': 'specialty',
    'SPECIALTY': 'specialty',
}

def standardize_master_registry():
    """Standardize column names in master registry and remove duplicates"""
    
    print("=" * 70)
    print("STANDARDIZING MASTER REGISTRY COLUMNS")
    print("=" * 70)
    
    # Load master registry
    registry_path = Path('data/processed/master_registry.csv')
    if not registry_path.exists():
        print("\n❌ Master registry not found")
        return
    
    df = pd.read_csv(registry_path)
    
    print(f"\nOriginal columns: {len(df.columns)}")
    print(f"Original records: {len(df):,}")
    
    # Apply standardization
    df = df.rename(columns=COLUMN_STANDARDIZATION)
    
    print(f"\nAfter renaming: {len(df.columns)} columns")
    
    # Remove duplicate columns (keep first occurrence)
    df = df.loc[:, ~df.columns.duplicated()]
    
    print(f"After removing duplicates: {len(df.columns)} columns")
    
    # Show what was removed
    original_cols = set(pd.read_csv(registry_path).columns)
    final_cols = set(df.columns)
    removed = original_cols - final_cols
    
    if removed:
        print(f"\n✓ Removed {len(removed)} duplicate columns:")
        for col in sorted(removed):
            print(f"  - {col}")
    
    # Save cleaned registry
    df.to_csv(registry_path, index=False)
    
    print(f"\n✓ Cleaned registry saved: {registry_path}")
    print(f"\nFinal columns ({len(df.columns)}):")
    for col in df.columns:
        print(f"  - {col}")
    
    print("\n" + "=" * 70)
    print("STANDARDIZATION COMPLETE")
    print("=" * 70)
    
    return df

if __name__ == "__main__":
    standardize_master_registry()
