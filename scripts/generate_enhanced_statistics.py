"""
Generate enhanced statistics with simplified discharge destinations
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def categorize_discharge(destination, died_in_icu):
    """Categorize discharge destination into simplified categories"""
    if pd.isna(destination):
        return 'Unknown'
    
    dest_str = str(destination).lower()
    
    # Died
    if died_in_icu == 'Yes' or 'died' in dest_str or 'death' in dest_str:
        return 'Died'
    
    # Home
    if 'usual place of residence' in dest_str:
        return 'Home'
    
    # Temporary residence
    if 'temporary' in dest_str:
        return 'Temporary Residence'
    
    # Other NHS Provider
    if 'nhs' in dest_str and ('other provider' in dest_str or 'hospital' in dest_str):
        return 'Other NHS Provider'
    
    # Non-NHS (care homes, hospices, etc)
    if any(x in dest_str for x in ['care home', 'hospice', 'non-nhs']):
        return 'Other NHS Provider'  # Group with other providers
    
    return 'Unknown'

def generate_enhanced_statistics():
    """Generate comprehensive statistics for interactive dashboard"""
    
    print("=" * 70)
    print("GENERATING ENHANCED STATISTICS")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv('data/processed/master_registry.csv')
    
    print(f"\nLoaded {len(df):,} records")
    
    # Convert dates
    df['ICU_admit_date'] = pd.to_datetime(df['ICU_admit_date'], format='%d/%m/%Y', errors='coerce')
    df['year_month'] = df['ICU_admit_date'].dt.to_period('M').astype(str)
    
    # Add simplified discharge destination
    df['discharge_category'] = df.apply(
        lambda row: categorize_discharge(row['BRI_discharge_destination'], row['ICU_death']),
        axis=1
    )
    
    # Create detailed dataset for filtering
    records = []
    
    for _, row in df.iterrows():
        if pd.notna(row['ICU_admit_date']):
            record = {
                'year_month': row['year_month'],
                'icu_ward': str(row['icu_ward']) if pd.notna(row['icu_ward']) else 'Unknown',
                'specialty': str(row['specialty']) if pd.notna(row['specialty']) else 'Unknown',
                'patient_classification': str(row['patient_classification']) if pd.notna(row['patient_classification']) else 'Unknown',
                'discharge_category': row['discharge_category'],
                'icu_death': str(row['ICU_death']) if pd.notna(row['ICU_death']) else 'Unknown',
                'los': float(row['ICU_LOS_wholeday']) if pd.notna(row['ICU_LOS_wholeday']) else 0
            }
            records.append(record)
    
    # Create output data
    output_data = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'total_records': len(records),
            'date_range': {
                'start': str(df['ICU_admit_date'].min().date()) if df['ICU_admit_date'].notna().any() else None,
                'end': str(df['ICU_admit_date'].max().date()) if df['ICU_admit_date'].notna().any() else None
            }
        },
        'records': records,
        'filter_options': {
            'units': sorted([u for u in df['icu_ward'].dropna().unique() if str(u) != 'nan']),
            'specialties': sorted([s for s in df['specialty'].dropna().unique() if str(s) != 'nan']),
            'patient_classifications': sorted([p for p in df['patient_classification'].dropna().unique() if str(p) != 'nan']),
            'outcomes': ['Yes', 'No']
        }
    }
    
    # Save
    output_path = Path('data/aggregated/master/dashboard_data.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Enhanced statistics saved: {output_path}")
    print(f"\nDischarge categories:")
    print(df['discharge_category'].value_counts())
    
    print("\n" + "=" * 70)
    
    return output_data

if __name__ == "__main__":
    generate_enhanced_statistics()
