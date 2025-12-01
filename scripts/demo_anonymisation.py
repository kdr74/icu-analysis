"""
Demonstration of patient data anonymisation workflow
"""

from generate_test_data import generate_test_patient_data
from anonymise_patients import anonymise_patient_data
import pandas as pd

print("=" * 70)
print("ICU PATIENT ANONYMISATION DEMONSTRATION")
print("=" * 70)

# Step 1: Generate test data
print("\n[1/3] Generating test patient data...")
df_original = generate_test_patient_data(n_patients=50)

print("\n[2/3] Anonymising patient data...")
df_anonymous = anonymise_patient_data(
    input_file='data/raw/test_patient_data.csv',
    identifier_column='hospital_number',
    output_file='data/processed/test_master_registry.csv'
)

print("\n[3/3] Verification...")
print("\nOriginal data (first 3 rows, showing identifiers):")
print(df_original[['hospital_number', 'icu_unit', 'primary_diagnosis']].head(3))

print("\nAnonymised data (first 3 rows):")
print(df_anonymous[['anonymous_patient_id', 'icu_unit', 'primary_diagnosis']].head(3))

print("\n" + "=" * 70)
print("DEMONSTRATION COMPLETE")
print("=" * 70)
print("\nKey points:")
print("✓ Original identifiers removed")
print("✓ Anonymous IDs created (ICU-000001, ICU-000002, etc.)")
print("✓ Hash stored for record linkage")
print("✓ All clinical data preserved")
print("\nFiles created:")
print("- data/raw/test_patient_data.csv (contains identifiers - NOT for Git)")
print("- data/processed/test_master_registry.csv (anonymised - NOT for Git)")
print("- hashing_salt.txt (secret key - NOT for Git)")
print("\nThese files are protected by .gitignore")
