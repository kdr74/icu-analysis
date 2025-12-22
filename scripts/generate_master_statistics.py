"""
Generate comprehensive statistics from master registry
"""

import pandas as pd
import json
from pathlib import Path
from datetime import datetime

def generate_master_statistics():
    """Generate statistics for master registry"""
    
    print("=" * 70)
    print("GENERATING MASTER REGISTRY STATISTICS")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv('data/processed/master_registry.csv')
    
    print(f"\nLoaded {len(df):,} records")
    print(f"Unique patients: {df['anonymous_patient_id'].nunique():,}")
    
    # Convert dates
    df['ICU_admit_date'] = pd.to_datetime(df['ICU_admit_date'], format='%d/%m/%Y', errors='coerce')
    
    stats = {
        'metadata': {
            'generated': datetime.now().isoformat(),
            'total_admissions': len(df),
            'unique_patients': int(df['anonymous_patient_id'].nunique())
        },
        'by_unit': {},
        'by_specialty': {},
        'outcomes': {},
        'length_of_stay': {},
        'monthly_trends': {}
    }
    
    # By ICU unit
    if 'icu_ward' in df.columns:
        unit_counts = df['icu_ward'].value_counts()
        for unit, count in unit_counts.items():
            if pd.notna(unit):
                stats['by_unit'][str(unit)] = int(count)
    
    # By specialty
    if 'specialty' in df.columns:
        specialty_counts = df['specialty'].value_counts().head(20)
        for spec, count in specialty_counts.items():
            if pd.notna(spec) and count >= 5:  # Small cell suppression
                stats['by_specialty'][str(spec)] = int(count)
    
    # ICU outcomes
    if 'ICU_death' in df.columns:
        deaths = (df['ICU_death'] == 'Yes').sum()
        stats['outcomes']['icu_deaths'] = int(deaths) if deaths >= 5 else '<5'
        stats['outcomes']['icu_survivors'] = int(len(df) - deaths)
        if deaths >= 5:
            stats['outcomes']['icu_mortality_percent'] = round((deaths / len(df)) * 100, 2)
    
    # Length of stay
    if 'ICU_LOS_wholeday' in df.columns:
        los_data = df['ICU_LOS_wholeday'].dropna()
        stats['length_of_stay']['median_days'] = float(los_data.median())
        stats['length_of_stay']['mean_days'] = round(float(los_data.mean()), 1)
        stats['length_of_stay']['min_days'] = int(los_data.min())
        stats['length_of_stay']['max_days'] = int(los_data.max())
    
    # Monthly trends (last 12 months)
    if 'ICU_admit_date' in df.columns:
        df_dated = df[df['ICU_admit_date'].notna()].copy()
        df_dated['year_month'] = df_dated['ICU_admit_date'].dt.to_period('M')
        monthly = df_dated.groupby('year_month').size().tail(12)
        
        for period, count in monthly.items():
            stats['monthly_trends'][str(period)] = int(count)
    
    # Save statistics
    output_path = Path('data/aggregated/master/master_statistics.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(stats, f, indent=2)
    
    print(f"\n✓ Statistics saved: {output_path}")
    
    # Print summary
    print("\n" + "=" * 70)
    print("STATISTICS SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal admissions: {stats['metadata']['total_admissions']:,}")
    print(f"Unique patients: {stats['metadata']['unique_patients']:,}")
    
    print(f"\nBy ICU Unit:")
    for unit, count in stats['by_unit'].items():
        print(f"  {unit}: {count:,}")
    
    print(f"\nTop specialties:")
    for spec, count in list(stats['by_specialty'].items())[:10]:
        print(f"  {spec}: {count:,}")
    
    if stats['outcomes']:
        print(f"\nOutcomes:")
        for key, val in stats['outcomes'].items():
            print(f"  {key}: {val}")
    
    if stats['length_of_stay']:
        print(f"\nLength of stay:")
        for key, val in stats['length_of_stay'].items():
            print(f"  {key}: {val}")
    
    print("\n" + "=" * 70)
    
    return stats

if __name__ == "__main__":
    generate_master_statistics()
