"""
Demonstration of processing multiple data files into master registry
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from process_patient_data import ICUDataProcessor
from validate_registry import RegistryValidator

print("=" * 70)
print("MULTI-FILE DATA PROCESSING DEMONSTRATION")
print("=" * 70)

# Generate test files simulating different data sources
print("\n[1/5] Generating test data files...")

np.random.seed(42)

# File 1: Main admissions data (with hospital numbers)
admissions = []
for i in range(30):
    admission_date = datetime(2024, 1, 1) + timedelta(days=np.random.randint(0, 180))
    admissions.append({
        'hospital_number': f"H{1000000 + i:07d}",
        'date_of_birth': (admission_date - timedelta(days=np.random.randint(18*365, 90*365))).strftime('%Y-%m-%d'),
        'admission_datetime': admission_date.strftime('%Y-%m-%d %H:%M:%S'),
        'discharge_datetime': (admission_date + timedelta(hours=np.random.randint(24, 480))).strftime('%Y-%m-%d %H:%M:%S'),
        'admission_source': np.random.choice(['ED', 'Theatre', 'Ward']),
        'icu_unit': np.random.choice(['A600', 'C604', 'WICU']),
        'primary_diagnosis': np.random.choice(['Sepsis', 'Respiratory Failure', 'Cardiac Arrest'])
    })

df1 = pd.DataFrame(admissions)
df1.to_csv('data/raw/test_admissions.csv', index=False)
print(f"  Created: test_admissions.csv ({len(df1)} records)")

# File 2: Outcomes data (with NHS numbers, overlapping patients)
outcomes = []
for i in range(20, 50):  # Overlaps with admissions file
    outcomes.append({
        'nhs_number': f"NHS{9000000000 + i:010d}",
        'hospital_number': f"H{1000000 + i:07d}",  # For linking demo
        'specialty': np.random.choice(['Medicine', 'Surgery', 'Cardiology']),
        'icu_outcome': np.random.choice(['Survived', 'Died'], p=[0.9, 0.1]),
        'icu_discharge_destination': np.random.choice(['Ward', 'HDU', 'Home', 'Deceased']),
        'hospital_outcome': np.random.choice(['Survived', 'Died'], p=[0.95, 0.05])
    })

df2 = pd.DataFrame(outcomes)
df2.to_excel('data/raw/test_outcomes.xlsx', index=False)
print(f"  Created: test_outcomes.xlsx ({len(df2)} records)")

# File 3: Additional admissions (later time period)
later_admissions = []
for i in range(50, 65):
    admission_date = datetime(2024, 7, 1) + timedelta(days=np.random.randint(0, 120))
    later_admissions.append({
        'hosp_num': f"H{1000000 + i:07d}",  # Different column name
        'admit_dt': admission_date.strftime('%Y-%m-%d %H:%M:%S'),
        'dc_dt': (admission_date + timedelta(hours=np.random.randint(24, 480))).strftime('%Y-%m-%d %H:%M:%S'),
        'unit': np.random.choice(['A600', 'C604', 'WICU']),
        'diagnosis': np.random.choice(['Pneumonia', 'Trauma', 'Stroke'])
    })

df3 = pd.DataFrame(later_admissions)
df3.to_csv('data/raw/test_later_admissions.csv', index=False)
print(f"  Created: test_later_admissions.csv ({len(df3)} records)")

# Process all files
print("\n[2/5] Processing files into master registry...")

processor = ICUDataProcessor()

# Process File 1
processor.process_file(
    filepath='data/raw/test_admissions.csv',
    identifier_column='hospital_number',
    date_columns={
        'date_of_birth': 'date',
        'admission_datetime': 'datetime',
        'discharge_datetime': 'datetime'
    }
)

# Process File 2 (different identifier type)
processor.process_file(
    filepath='data/raw/test_outcomes.xlsx',
    identifier_column='nhs_number',
    merge_strategy='update'
)

# Process File 3 (different column names)
processor.process_file(
    filepath='data/raw/test_later_admissions.csv',
    identifier_column='hosp_num',
    column_mapping={
        'hosp_num': 'hospital_number',
        'admit_dt': 'admission_datetime',
        'dc_dt': 'discharge_datetime',
        'unit': 'icu_unit',
        'diagnosis': 'primary_diagnosis'
    },
    date_columns={
        'admission_datetime': 'datetime',
        'discharge_datetime': 'datetime'
    }
)

# Save master registry
print("\n[3/5] Saving master registry...")
processor.save_master_registry('data/processed/test_master_registry.csv')

# Get statistics
stats = processor.get_summary_statistics()

print("\n[4/5] Master registry statistics:")
print(f"  Total records: {stats['total_records']}")
print(f"  Unique patients: {stats['unique_patients']}")
print(f"  Date range: {stats['date_range']['earliest_admission']} to {stats['date_range']['latest_admission']}")

if 'unit_distribution' in stats:
    print("\n  Unit distribution:")
    for unit, count in stats['unit_distribution'].items():
        print(f"    {unit}: {count}")

# Validate
print("\n[5/5] Validating master registry...")
validator = RegistryValidator('data/processed/test_master_registry.csv')
validator.run_all_checks()

print("\n" + "=" * 70)
print("DEMONSTRATION COMPLETE")
print("=" * 70)
print("\nWhat happened:")
print("✓ Generated 3 test data files with different formats")
print("✓ Processed each file with appropriate settings")
print("✓ Anonymised all patient identifiers")
print("✓ Merged data from all sources")
print("✓ Created master registry with unique patients")
print("✓ Validated data quality")
print("\nFiles created:")
print("- data/raw/test_admissions.csv")
print("- data/raw/test_outcomes.xlsx")
print("- data/raw/test_later_admissions.csv")
print("- data/processed/test_master_registry.csv")
print("- data/processed/processing_log.json")
print("- data/processed/validation_report.json")
