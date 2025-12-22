"""
Process GICU admissions summary with enhanced data fields
Merges with existing master registry, preventing duplicates
"""

import pandas as pd
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from shared.data_sanitizer import DataSanitizer
from shared.enhanced_anonymiser import EnhancedPatientAnonymiser

def process_gicu_admissions():
    print("=" * 70)
    print("PROCESSING GICU ADMISSIONS SUMMARY")
    print("=" * 70)
    
    # Load the file
    df = pd.read_csv('data/raw/master/gicu_admissions_summary.csv')
    
    print(f"\nLoaded {len(df):,} records")
    print(f"Original columns: {len(df.columns)}")
    
    # Remove unnamed columns
    df = df.loc[:, ~df.columns.str.contains('^Unnamed')]
    
    print(f"After removing unnamed columns: {len(df.columns)} columns")
    
    # Sanitize data (returns a tuple: df, report)
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
        print("ERROR: No identifier column found (hospital_number or NHS_number)")
        return
    
    # Check for existing master registry
    registry_path = Path('data/processed/master_registry.csv')
    
    if registry_path.exists():
        existing_df = pd.read_csv(registry_path)
        print(f"\nExisting registry: {len(existing_df):,} records")
        
        # Detect duplicates by matching:
        # - Same anonymous_patient_id
        # - Same ICU_admit_date
        
        # Create matching key
        df['match_key'] = df['anonymous_patient_id'].astype(str) + '_' + df['ICU_admit_date'].astype(str)
        existing_df['match_key'] = existing_df['anonymous_patient_id'].astype(str) + '_' + existing_df['ICU_admit_date'].astype(str)
        
        # Find duplicates
        duplicates = df['match_key'].isin(existing_df['match_key'])
        
        new_records = df[~duplicates].copy()
        duplicate_records = df[duplicates].copy()
        
        print(f"\nDuplicate admissions (already in registry): {len(duplicate_records):,}")
        print(f"New admissions to add: {len(new_records):,}")
        
        if len(new_records) > 0:
            # Get original columns before merging
            original_cols = set(existing_df.columns)
            
            # For new records, align columns with existing registry
            all_columns = set(existing_df.columns) | set(new_records.columns)
            all_columns.discard('match_key')
            
            # Add missing columns to both dataframes
            for col in all_columns:
                if col not in existing_df.columns:
                    existing_df[col] = None
                if col not in new_records.columns:
                    new_records[col] = None
            
            # Remove match_key from both
            existing_df = existing_df.drop(columns=['match_key'])
            new_records = new_records.drop(columns=['match_key'])
            
            # Combine
            combined_df = pd.concat([existing_df, new_records], ignore_index=True)
            
            print(f"\nCombined registry: {len(combined_df):,} records")
            print(f"Total unique patients: {combined_df['anonymous_patient_id'].nunique():,}")
            
            # Save
            combined_df.to_csv(registry_path, index=False)
            print(f"\n✓ Updated registry saved: {registry_path}")
            
            # Show new columns added
            new_cols = set(combined_df.columns) - original_cols
            if new_cols:
                print(f"\n✓ New columns added ({len(new_cols)}):")
                for col in sorted(new_cols):
                    print(f"  - {col}")
        else:
            print("\n✓ No new records to add - all admissions already in registry")
            
        if len(duplicate_records) > 0:
            print(f"\nℹ Note: {len(duplicate_records):,} duplicate records skipped")
            print("       (These admissions already exist in the registry)")
            
    else:
        # No existing registry - this is the first file
        df = df.drop(columns=['match_key']) if 'match_key' in df.columns else df
        df.to_csv(registry_path, index=False)
        print(f"\n✓ New registry created: {registry_path}")
        print(f"  Records: {len(df):,}")
        print(f"  Unique patients: {df['anonymous_patient_id'].nunique():,}")
    
    print("\n" + "=" * 70)
    print("PROCESSING COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    process_gicu_admissions()
