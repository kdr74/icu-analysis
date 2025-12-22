"""
Generate comprehensive dashboard data with age groups and statistics
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
from datetime import datetime

def categorize_age(age):
    """Categorize age into groups"""
    if pd.isna(age):
        return 'Unknown'
    age = int(age)
    if age < 16:
        return '<16'
    elif age < 18:
        return '16-18'
    elif age < 30:
        return '18-30'
    elif age < 40:
        return '30-40'
    elif age < 50:
        return '40-50'
    elif age < 60:
        return '50-60'
    elif age < 70:
        return '60-70'
    elif age < 80:
        return '70-80'
    elif age < 90:
        return '80-90'
    else:
        return '90+'

def categorize_discharge(destination, died_in_icu):
    """Categorize discharge destination"""
    if pd.isna(destination):
        return 'Unknown'
    
    dest_str = str(destination).lower()
    
    if died_in_icu == 'Yes' or 'died' in dest_str or 'death' in dest_str:
        return 'Died'
    if 'usual place of residence' in dest_str:
        return 'Home'
    if 'temporary' in dest_str:
        return 'Temporary Residence'
    if 'nhs' in dest_str and ('other provider' in dest_str or 'hospital' in dest_str):
        return 'Other NHS Provider'
    if any(x in dest_str for x in ['care home', 'hospice', 'non-nhs']):
        return 'Other NHS Provider'
    
    return 'Unknown'

def calculate_statistics(values):
    """Calculate comprehensive statistics"""
    values = [v for v in values if pd.notna(v) and v >= 0]
    if not values:
        return None
    
    return {
        'mean': float(round(np.mean(values), 2)),
        'median': float(round(np.median(values), 2)),
        'std': float(round(np.std(values), 2)),
        'q25': float(round(np.percentile(values, 25), 2)),
        'q75': float(round(np.percentile(values, 75), 2)),
        'min': float(round(min(values), 2)),
        'max': float(round(max(values), 2)),
        'count': int(len(values))
    }

def generate_enhanced_data():
    print("=" * 70)
    print("GENERATING ENHANCED DASHBOARD DATA")
    print("=" * 70)
    
    # Load data
    df = pd.read_csv('data/processed/master_registry.csv', low_memory=False)
    print(f"\nLoaded {len(df):,} records")
    
    # Convert dates
    df['ICU_admit_date'] = pd.to_datetime(df['ICU_admit_date'], format='%d/%m/%Y', errors='coerce')
    df['year_month'] = df['ICU_admit_date'].dt.to_period('M').astype(str)
    
    # Add age groups
    if 'age_at_admission' in df.columns:
        df['age_group'] = df['age_at_admission'].apply(categorize_age)
        print(f"✓ Categorized ages into groups")
    
    # Add discharge categories
    if 'BRI_discharge_destination' in df.columns and 'ICU_death' in df.columns:
        df['discharge_category'] = df.apply(
            lambda row: categorize_discharge(row['BRI_discharge_destination'], row['ICU_death']),
            axis=1
        )
        print(f"✓ Categorized discharge destinations")
    
    # Create aggregated records for dashboard
    records = []
    for _, row in df.iterrows():
        if pd.notna(row.get('ICU_admit_date')):
            record = {
                'year_month': row.get('year_month', 'Unknown'),
                'icu_ward': str(row.get('icu_ward', 'Unknown')),
                'specialty': str(row.get('specialty', 'Unknown')),
                'patient_classification': str(row.get('patient_classification', 'Unknown')),
                'discharge_category': row.get('discharge_category', 'Unknown'),
                'icu_death': str(row.get('ICU_death', 'Unknown')),
                'los': float(row['ICU_LOS_wholeday']) if pd.notna(row.get('ICU_LOS_wholeday')) else 0,
                'age_group': row.get('age_group', 'Unknown'),
                'age': float(row['age_at_admission']) if pd.notna(row.get('age_at_admission')) else None,
                'admit_type': str(row.get('admit_type', 'Unknown')),
                'readmission': str(row.get('readmission', 'Unknown')),
                'nature_of_surgery': str(row.get('nature_of_surgery', 'Unknown'))
            }
            records.append(record)
    
    # Generate filter options
    filter_options = {
        'units': sorted([u for u in df['icu_ward'].dropna().unique() if str(u) != 'nan']),
        'specialties': sorted([s for s in df['specialty'].dropna().unique() if str(s) != 'nan']),
        'patient_classifications': sorted([p for p in df['patient_classification'].dropna().unique() if str(p) != 'nan']),
        'age_groups': ['<16', '16-18', '18-30', '30-40', '40-50', '50-60', '60-70', '70-80', '80-90', '90+'],
        'admit_types': sorted([str(a) for a in df['admit_type'].dropna().unique() if str(a) != 'nan' and str(a) != 'Unknown']),
        'outcomes': ['Yes', 'No']
    }
    
    # Calculate summary statistics
    stats = {
        'los_overall': calculate_statistics(df['ICU_LOS_wholeday'].dropna()),
        'age_overall': calculate_statistics(df['age_at_admission'].dropna()) if 'age_at_admission' in df.columns else None,
        'los_by_outcome': {},
        'los_by_age_group': {},
        'mortality_by_age_group': {}
    }
    
    # LOS by outcome
    if 'ICU_death' in df.columns:
        for outcome in ['Yes', 'No']:
            outcome_df = df[df['ICU_death'] == outcome]
            stats['los_by_outcome'][outcome] = calculate_statistics(outcome_df['ICU_LOS_wholeday'].dropna())
    
    # Statistics by age group
    if 'age_group' in df.columns:
        for age_group in filter_options['age_groups']:
            age_df = df[df['age_group'] == age_group]
            if len(age_df) > 0:
                stats['los_by_age_group'][age_group] = calculate_statistics(age_df['ICU_LOS_wholeday'].dropna())
                
                if 'ICU_death' in age_df.columns:
                    deaths = int((age_df['ICU_death'] == 'Yes').sum())  # Convert to int
                    total = int(len(age_df))  # Convert to int
                    if total >= 5:  # Small cell suppression
                        stats['mortality_by_age_group'][age_group] = {
                            'rate': float(round((deaths / total) * 100, 2)),
                            'deaths': deaths,
                            'total': total
                        }
    
    # Save output
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
        'filter_options': filter_options,
        'statistics': stats
    }
    
    output_path = Path('data/aggregated/master/dashboard_data.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"\n✓ Enhanced data saved: {output_path}")
    print(f"\nAge groups distribution:")
    if 'age_group' in df.columns:
        print(df['age_group'].value_counts().sort_index())
    
    print("\n" + "=" * 70)
    print("DATA GENERATION COMPLETE")
    print("=" * 70)

if __name__ == "__main__":
    generate_enhanced_data()
