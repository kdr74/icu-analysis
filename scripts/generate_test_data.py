"""
Generate realistic test ICU patient data for testing anonymisation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def generate_test_patient_data(n_patients=50, output_file='data/raw/test_patient_data.csv'):
    """Generate realistic test ICU patient data"""
    
    np.random.seed(42)
    
    # Generate data
    data = []
    
    units = ['A600', 'C604', 'WICU']
    admission_sources = ['Emergency Department', 'Theatre', 'Ward', 'Transfer']
    diagnoses = [
        'Sepsis', 'Respiratory Failure', 'Cardiac Arrest', 
        'Post-operative', 'Trauma', 'Pneumonia', 'Myocardial Infarction',
        'Stroke', 'Multi-organ Failure', 'Diabetic Ketoacidosis'
    ]
    specialties = ['General Medicine', 'Cardiology', 'Surgery', 'Trauma', 'Respiratory']
    icu_outcomes = ['Survived', 'Died']
    discharge_destinations = ['Ward', 'HDU', 'Home', 'Deceased', 'Transfer']
    hospital_outcomes = ['Survived', 'Died']
    hospital_discharge = ['Home', 'Rehabilitation', 'Care Home', 'Deceased', 'Transfer']
    
    base_date = datetime(2024, 1, 1)
    
    for i in range(n_patients):
        # Generate identifiers (simulating hospital numbers)
        hospital_number = f"H{1000000 + i:07d}"
        
        # Generate dates
        admission_date = base_date + timedelta(days=np.random.randint(0, 365))
        los_hours = np.random.randint(12, 480)  # 12 hours to 20 days
        discharge_date = admission_date + timedelta(hours=los_hours)
        
        # Generate DOB (patients aged 18-90)
        age = np.random.randint(18, 91)
        dob = admission_date - timedelta(days=age*365)
        
        # Outcomes (90% survival rate)
        icu_outcome = np.random.choice(icu_outcomes, p=[0.9, 0.1])
        
        if icu_outcome == 'Died':
            icu_discharge_dest = 'Deceased'
            hosp_outcome = 'Died'
            hosp_discharge = 'Deceased'
        else:
            icu_discharge_dest = np.random.choice(['Ward', 'HDU', 'Home', 'Transfer'])
            hosp_outcome = np.random.choice(hospital_outcomes, p=[0.95, 0.05])
            hosp_discharge = np.random.choice(['Home', 'Rehabilitation', 'Care Home', 'Transfer'])
        
        data.append({
            'hospital_number': hospital_number,
            'date_of_birth': dob.strftime('%Y-%m-%d'),
            'admission_datetime': admission_date.strftime('%Y-%m-%d %H:%M:%S'),
            'discharge_datetime': discharge_date.strftime('%Y-%m-%d %H:%M:%S'),
            'admission_source': np.random.choice(admission_sources),
            'icu_unit': np.random.choice(units),
            'primary_diagnosis': np.random.choice(diagnoses),
            'specialty': np.random.choice(specialties),
            'icu_outcome': icu_outcome,
            'icu_discharge_destination': icu_discharge_dest,
            'hospital_outcome': hosp_outcome,
            'hospital_discharge_destination': hosp_discharge
        })
    
    df = pd.DataFrame(data)
    
    # Save
    df.to_csv(output_file, index=False)
    print(f"Generated {n_patients} test patient records")
    print(f"Saved to: {output_file}")
    print(f"\nColumns: {', '.join(df.columns)}")
    print(f"\nFirst 3 hospital numbers: {df['hospital_number'].head(3).tolist()}")
    
    return df

if __name__ == "__main__":
    generate_test_patient_data()
