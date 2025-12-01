"""
Test that same patient ID always gets same anonymous ID
"""

from anonymise_patients import anonymise_patient_data
import pandas as pd

# Create data with duplicate patient
data = pd.DataFrame({
    'hospital_number': ['H1000001', 'H1000002', 'H1000001'],  # Note duplicate
    'icu_unit': ['A600', 'C604', 'WICU'],
    'diagnosis': ['Sepsis', 'MI', 'Pneumonia']
})

data.to_csv('data/raw/test_duplicate.csv', index=False)

# Anonymise
df_anon = anonymise_patient_data(
    'data/raw/test_duplicate.csv',
    'hospital_number'
)

print("\nTest: Same hospital number should get same anonymous ID")
print(df_anon[['anonymous_patient_id', 'icu_unit', 'diagnosis']])

# Check if rows 0 and 2 have same anonymous_patient_id
if df_anon.iloc[0]['anonymous_patient_id'] == df_anon.iloc[2]['anonymous_patient_id']:
    print("\n✓ SUCCESS: Same patient gets consistent anonymous ID")
else:
    print("\n✗ FAILED: Inconsistent anonymisation")
