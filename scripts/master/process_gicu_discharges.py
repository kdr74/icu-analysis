"""
Process GICU discharges summary with DOB → age conversion
Merges with existing master registry, preventing duplicates
"""

import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
sys.path.append(str(Path(__file__).parent.parent))

from shared.data_sanitizer import DataSanitizer
from shared.enhanced_anonymiser import EnhancedPatientAnonymiser

def calculate_age_at_admission(dob, admit_date):
    """Calculate age at ICU admission from DOB"""
    try:
        if pd.isna(dob) or pd.isna(admit_date):
            return None
        
        # Parse dates - try different formats
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
        
        # Calculate age
        age = admit_dt.year - dob_dt.year
        
        # Adjust if birthday hasn't occurred yet this year
        if (admit_dt.month, admit_dt.day) < (dob_dt.month, dob_dt.day):
            age -= 1
        
        return age if age >= 0 and age < 150 else None
        
    except Exception as e:
        return None

def process_gicu_discharges():
    print("=" * 70)
    print("PROCESSING GICU DISCHARGES SUMMARY")
    print("=" * 70)
    
    # Load the file
    df = pd.read_csv('data/raw/master/gicu_discharges_summary.csv')
    
    print(f"\nLoaded {len(df):,} records")
    print(f"Original columns: {len(df.columns)}")
    
    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    print(f"After removing unnamed columns: {len(df.columns)} columns")
    
    # Calculate age from DOB BEFORE sanitizing (which might remove DOB)
    if 'DOB' in df.columns and 'ICU_admit_date' in df.columns:
        print("\n  Calculating age from DOB...")
        df['age_at_admission'] = df.apply(
            lambda row: calculate_age_at_admission(row['DOB'], row['ICU_admit_date']),
            axis=1
        )
        
        ages_calculated = df['age_at_admission'].notna().sum()
        print(f"  ✓ Calculated age for {ages_calculated:,} records")
        
        if ages_calculated > 0:
            print(f"    Age range: {df['age_at_admission'].min():.0f} - {df['age_at_admission'].max():.0f}")
            print(f"    Mean age: {df['age_at_admission'].mean():.1f}")
        
        # Remove DOB column for confidentiality
        df = df.drop(columns=['DOB'])
        print(f"  ✓ Removed DOB column (maintaining confidentiality)")
    
    # Sanitize data
    sanitizer = DataSanitizer()
    df, report = sanitizer.sanitize_dataframe(df)
    
    # Map to anonymous patient IDs
    anonymiser = EnhancedPatientAnonymiser()
    
    if 'hospital_number' in df.columns:
        df = anonymiser.anonymise_dataframe(df, 'hospital_number')
        print(f"Anonymised using hospital_number")
    elif 'NHS_number' in df.columns:
        df = anonymiser.anonymise_dataframe(df, 'NHS_number')
        print(f"Anonymised using NHS_number")
    else:
        print("ERROR: No identifier column found")
        return
    
    # Check for existing master registry
    registry_path = Path('data/processed/master_registry.csv')
    
    if registry_path.exists():
        existing_df = pd.read_csv(registry_path)
        print(f"\nExisting registry: {len(existing_df):,} records")
        
        # Detect duplicates
        df['match_key'] = df['anonymous_patient_id'].astype(str) + '_' + df['ICU_admit_date'].astype(str)
        existing_df['match_key'] = existing_df['anonymous_patient_id'].astype(str) + '_' + existing_df['ICU_admit_date'].astype(str)
        
        duplicates = df['match_key'].isin(existing_df['match_key'])
        
        new_records = df[~duplicates].copy()
        duplicate_records = df[duplicates].copy()
        
        print(f"\nDuplicate admissions (already in registry): {len(duplicate_records):,}")
        print(f"New admissions to add: {len(new_records):,}")
        
        if len(new_records) > 0:
            original_cols = set(existing_df.columns)
            
            # Align columns
            all_columns = set(existing_df.columns) | set(new_records.columns)
            all_columns.discard('match_key')
            
            for col in all_columns:
                if col not in existing_df.columns:
                    existing_df[col] = None
                if col not in new_records.columns:
                    new_records[col] = None
            
            existing_df = existing_df.drop(columns=['match_key'])
            new_records = new_records.drop(columns=['match_key'])
            
            combined_df = pd.concat([existing_df, new_records], ignore_index=True)
            
            print(f"\nCombined registry: {len(combined_df):,} records")
            print(f"Total unique patients: {combined_df['anonymous_patient_id'].nunique():,}")
            
            combined_df.to_csv(registry_path, index=False)
            print(f"\n✓ Updated registry saved: {registry_path}")
            
            new_cols = set(combined_df.columns) - original_cols
            if new_cols:
                print(f"\n✓ New columns added ({len(new_cols)}):")
                for col in sorted(new_cols):
                    print(f"  - {col}")
        else:
            print("\n✓ No new records to add - all admissions already in registry")
            
        if len(duplicate_records) > 0:
            print(f"\nℹ Note: {len(duplicate_records):,} duplicate records skipped")
            
    else:
        df = df.drop(columns=['match_key']) if 'match_key' in df.columns else df
        df.to_csv(registry_path, index=False)
        print(f"\n✓ New registry created: {registry_path}")
        print(f"  Records: {len(df):,}")
        print(f"  Unique patients: {df['anonymous_patient_id'].nunique():,}")
    
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    process_gicu_discharges()
