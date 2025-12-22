"""
Safe master registry processor - handles encoding issues
"""

import sys
sys.path.append('scripts/shared')
from enhanced_anonymiser import EnhancedPatientAnonymiser
from data_sanitizer import DataSanitizer
from duplicate_detector import DuplicateDetector
import pandas as pd
from pathlib import Path

def process_master_file_safe(filepath, identifier_column='hospital_number', 
                             duplicate_action='skip'):
    """Process master registry with encoding error handling"""
    
    print("\n" + "=" * 70)
    print("PROCESSING MASTER REGISTRY FILE (SAFE MODE)")
    print("=" * 70)
    print(f"\nFile: {Path(filepath).name}")
    
    # Try to read with different encodings and error handling
    filepath = Path(filepath)
    
    encodings_to_try = [
        ('utf-8', 'ignore'),
        ('utf-8', 'replace'),
        ('latin1', 'ignore'),
        ('cp1252', 'ignore'),
        ('iso-8859-1', 'ignore')
    ]
    
    df = None
    for encoding, errors in encodings_to_try:
        try:
            if filepath.suffix == '.csv':
                df = pd.read_csv(filepath, encoding=encoding, encoding_errors=errors)
            elif filepath.suffix in ['.xlsx', '.xls']:
                df = pd.read_excel(filepath)
            
            if df is not None:
                print(f"✓ Successfully loaded with encoding: {encoding} (errors={errors})")
                break
        except Exception as e:
            print(f"✗ Failed with {encoding}/{errors}: {str(e)[:50]}")
            continue
    
    if df is None:
        print("\n❌ Could not read file with any encoding")
        return
    
    print(f"Loaded: {len(df)} rows, {len(df.columns)} columns")
    print(f"\nColumns: {list(df.columns)}")
    
    # Initialize components
    anonymiser = EnhancedPatientAnonymiser()
    sanitizer = DataSanitizer()
    duplicate_detector = DuplicateDetector()
    
    # Check if identifier column exists
    if identifier_column not in df.columns:
        print(f"\n❌ Column '{identifier_column}' not found in file")
        print(f"Available columns: {list(df.columns)}")
        return
    
    # Sanitize
    df, _ = sanitizer.sanitize_dataframe(df)
    
    # Anonymise
    print(f"\n  Anonymising patient identifiers...")
    df = anonymiser.anonymise_dataframe(df, identifier_column)
    
    # Check for duplicates
    print(f"\n  Checking for duplicate records...")
    duplicates_df, new_only_df = duplicate_detector.find_duplicates(df)
    
    if len(duplicates_df) > 0:
        print(f"\n  ⚠️  WARNING: Found {len(duplicates_df)} duplicate records")
        
        # Generate report
        report_path = Path(f'reports/duplicates_master_{filepath.stem}.csv')
        report_path.parent.mkdir(parents=True, exist_ok=True)
        duplicates_df.to_csv(report_path, index=False)
        print(f"  ✓ Duplicate report saved: {report_path}")
        
        if duplicate_action == 'skip':
            print(f"\n  Action: SKIP - Excluding {len(duplicates_df)} duplicate records")
            df_to_save = new_only_df
        else:
            df_to_save = df
    else:
        print(f"\n  ✓ No duplicates detected - all {len(df)} records are new")
        df_to_save = df
    
    # Load existing registry if exists
    registry_path = Path('data/processed/master_registry.csv')
    if registry_path.exists():
        existing = pd.read_csv(registry_path)
        print(f"\n  Merging with existing registry ({len(existing)} records)...")
        combined = pd.concat([existing, df_to_save], ignore_index=True)
    else:
        combined = df_to_save
    
    # Save
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    combined.to_csv(registry_path, index=False)
    
    print(f"\n✓ Master registry saved: {registry_path}")
    print(f"  Total records: {len(combined)}")
    print(f"  Unique patients: {combined['anonymous_patient_id'].nunique()}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        identifier_column = sys.argv[2] if len(sys.argv) > 2 else 'hospital_number'
        duplicate_action = sys.argv[3] if len(sys.argv) > 3 else 'skip'
        
        process_master_file_safe(filepath, identifier_column, duplicate_action)
    else:
        print("Usage: python process_master_registry_safe.py <filepath> [identifier_column] [duplicate_action]")
