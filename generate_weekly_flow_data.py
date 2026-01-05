#!/usr/bin/env python3
"""
Generate weekly flow analysis data for ICU dashboard
Matches the R report style with clean visualizations
"""

import pandas as pd
import json
from datetime import datetime
import numpy as np

def generate_weekly_flow_data():
    """Process master registry to create weekly flow analysis data"""
    
    # Read master registry
    df = pd.read_csv('./data/processed/master_registry.csv')
    print(f"Loaded {len(df)} records")
    
    # Convert dates
    df['ICU_admit_date'] = pd.to_datetime(df['ICU_admit_date'], format='%d/%m/%Y', errors='coerce')
    df['ICU_discharge_date'] = pd.to_datetime(df['ICU_discharge_date'], format='%d/%m/%Y', errors='coerce')
    df['hospital_admit_date'] = pd.to_datetime(df['hospital_admit_date'], format='%d/%m/%Y', errors='coerce')
    df['BRI_hospital_discharge_date'] = pd.to_datetime(df['BRI_hospital_discharge_date'], format='%d/%m/%Y', errors='coerce')
    
    # Create time periods
    df['admit_week'] = df['ICU_admit_date'].dt.to_period('W').astype(str)
    df['discharge_week'] = df['ICU_discharge_date'].dt.to_period('W').astype(str)
    df['admit_date'] = df['ICU_admit_date'].dt.date.astype(str)
    df['discharge_date'] = df['ICU_discharge_date'].dt.date.astype(str)
    
    # === DAILY FLOW DATA ===
    daily_admits = df.groupby(['admit_date', 'icu_ward']).size().reset_index(name='count')
    daily_discharges = df.groupby(['discharge_date', 'icu_ward']).size().reset_index(name='count')
    
    print(f"\nDaily data:")
    print(f"  Admissions: {len(daily_admits)} day-unit records")
    print(f"  Date range: {daily_admits['admit_date'].min()} to {daily_admits['admit_date'].max()}")
    
    # === WEEKLY FLOW DATA ===
    weekly_admits = df.groupby(['admit_week', 'icu_ward']).size().reset_index(name='count')
    weekly_discharges = df.groupby(['discharge_week', 'icu_ward']).size().reset_index(name='count')
    
    print(f"\nWeekly data:")
    print(f"  Admissions: {len(weekly_admits)} week-unit records")
    
    # === LENGTH OF STAY DISTRIBUTIONS ===
    # Store full distributions for histogram rendering
    # IMPORTANT: Store individual patient data with dates for filtering
    los_distributions = {}
    
    for col, name in [
        ('ICU_LOS_wholeday', 'icu_los'),
        ('hospital_LOS_pre_ICU_wholeday', 'pre_icu_hospital_los'),
        ('hospital_LOS_post_ICU_wholeday', 'post_icu_hospital_los'),
        ('hospital_LOS_total_wholeday', 'total_hospital_los')
    ]:
        values = df[col].dropna()
        if len(values) > 0:
            # Create histogram bins (0-70 days, 1-day bins)
            bins = list(range(0, 71))
            hist, bin_edges = np.histogram(values, bins=bins)
            
            # Calculate statistics
            mean = float(values.mean())
            std = float(values.std())
            median = float(values.median())
            
            # Calculate confidence interval (95%)
            se = std / np.sqrt(len(values))
            ci_lower = mean - 1.96 * se
            ci_upper = mean + 1.96 * se
            
            # Create patient-level data with dates for filtering
            patient_los_data = []
            for idx in values.index:
                if pd.notna(df.loc[idx, 'ICU_admit_date']):
                    patient_los_data.append({
                        'los': float(df.loc[idx, col]),
                        'admit_date': df.loc[idx, 'ICU_admit_date'].strftime('%Y-%m-%d'),
                        'unit': str(df.loc[idx, 'icu_ward']) if pd.notna(df.loc[idx, 'icu_ward']) else 'Unknown'
                    })
            
            los_distributions[name] = {
                'histogram': {
                    'bins': [int(b) for b in bin_edges[:-1]],  # Left edges
                    'counts': [int(c) for c in hist]
                },
                'statistics': {
                    'mean': round(mean, 3),
                    'std': round(std, 3),
                    'median': round(median, 3),
                    'n': int(len(values)),
                    'ci_lower': round(ci_lower, 3),
                    'ci_upper': round(ci_upper, 3)
                },
                # Patient-level data for client-side filtering
                'patient_data': patient_los_data
            }
            
            print(f"\n{name}:")
            print(f"  Mean: {mean:.2f} ± {std:.2f}")
            print(f"  95% CI: [{ci_lower:.2f}, {ci_upper:.2f}]")
            print(f"  n = {len(values)}")
    
    # === DISCHARGE ANALYSIS ===
    discharge_methods = df['discharge_method'].value_counts().to_dict()
    discharge_destinations = df['BRI_discharge_destination'].value_counts().to_dict()
    
    print(f"\nDischarge categories:")
    print(f"  Methods: {len(discharge_methods)}")
    print(f"  Destinations: {len(discharge_destinations)}")
    
    # === OCCUPANCY CALCULATION ===
    # Calculate daily occupancy for each unit
    all_dates = pd.date_range(
        start=df['ICU_admit_date'].min(),
        end=df['ICU_admit_date'].max(),
        freq='D'
    )
    
    occupancy_data = []
    for date in all_dates:
        for unit in df['icu_ward'].dropna().unique():
            # Count patients in ICU on this date
            unit_data = df[df['icu_ward'] == unit]
            in_icu = unit_data[
                (unit_data['ICU_admit_date'] <= date) & 
                (unit_data['ICU_discharge_date'] >= date)
            ]
            occupancy_data.append({
                'date': date.strftime('%Y-%m-%d'),
                'unit': str(unit),
                'occupancy': int(len(in_icu))
            })
    
    print(f"\nOccupancy data: {len(occupancy_data)} day-unit records")
    
    # === COMPILE OUTPUT ===
    output = {
        'daily_admissions': daily_admits.to_dict('records'),
        'daily_discharges': daily_discharges.to_dict('records'),
        'weekly_admissions': weekly_admits.to_dict('records'),
        'weekly_discharges': weekly_discharges.to_dict('records'),
        'occupancy': occupancy_data,
        'los_distributions': los_distributions,
        'discharge_methods': discharge_methods,
        'discharge_destinations': discharge_destinations,
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'total_records': int(len(df)),
            'units': sorted([str(u) for u in df['icu_ward'].dropna().unique()]),
            'date_range': {
                'start': df['ICU_admit_date'].min().strftime('%Y-%m-%d'),
                'end': df['ICU_admit_date'].max().strftime('%Y-%m-%d')
            }
        }
    }
    
    # Save to file
    with open('docs/data/aggregated/master/weekly_flow_data.json', 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\n✓ Created docs/data/aggregated/master/weekly_flow_data.json")
    return output

if __name__ == '__main__':
    generate_weekly_flow_data()
