"""
Generate realistic test ICU data for system testing
Creates 200 patients with varied clinical scenarios
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# Set seed for reproducibility
np.random.seed(42)
random.seed(42)

def random_datetime(start_date, end_date):
    """Generate random datetime between two dates"""
    time_between = end_date - start_date
    days_between = time_between.days
    random_days = random.randrange(days_between)
    random_seconds = random.randrange(24 * 60 * 60)
    return start_date + timedelta(days=random_days, seconds=random_seconds)

def generate_master_registry():
    """Generate master patient registry with 200 patients"""
    
    print("Generating master patient registry (200 patients)...")
    
    # Date range
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    # Patient identifiers
    hospital_numbers = [f"H{1000000 + i}" for i in range(200)]
    nhs_numbers = [f"NHS{9000000000 + i}" for i in range(200)]
    
    # Units
    units = ['A600', 'C604', 'WICU']
    
    # Diagnoses
    diagnoses = [
        'Sepsis', 'Pneumonia', 'COPD exacerbation', 'Acute Kidney Injury',
        'Myocardial Infarction', 'Stroke', 'Cardiac Arrest', 'Multi-organ Failure',
        'Diabetic Ketoacidosis', 'Trauma', 'Post-operative', 'Pancreatitis',
        'Respiratory Failure', 'Heart Failure', 'Liver Failure', 'GI Bleed',
        'Pulmonary Embolism', 'Arrhythmia', 'Overdose', 'Burns'
    ]
    
    # Specialties
    specialties = [
        'General Medicine', 'Cardiology', 'Respiratory', 'Nephrology',
        'General Surgery', 'Cardiothoracic Surgery', 'Neurosurgery',
        'Trauma & Orthopaedics', 'Gastroenterology', 'Emergency Medicine'
    ]
    
    # Admission sources
    sources = ['ED', 'Theatre', 'Ward', 'Transfer from other hospital', 'Direct admission']
    
    # Postcodes (Bristol area)
    postcodes = ['BS1 4RP', 'BS2 8HW', 'BS3 1LT', 'BS4 3BD', 'BS5 6TY', 
                 'BS6 7PT', 'BS7 9HJ', 'BS8 2PR', 'BS9 3NL', 'BS10 5SD']
    
    data = []
    
    for i in range(200):
        # Hospital admission
        hosp_admission = random_datetime(start_date, end_date)
        
        # ICU admission (0-48 hours after hospital admission)
        hours_to_icu = random.randint(0, 48)
        icu_admission = hosp_admission + timedelta(hours=hours_to_icu)
        
        # ICU length of stay (1-30 days, most 3-7 days)
        icu_los = max(1, int(np.random.gamma(2, 2)))
        icu_los = min(icu_los, 30)
        
        icu_discharge = icu_admission + timedelta(days=icu_los)
        
        # Hospital discharge (0-14 days after ICU discharge)
        days_after_icu = random.randint(0, 14)
        hosp_discharge = icu_discharge + timedelta(days=days_after_icu)
        
        # ICU outcome (90% survival)
        icu_outcome = 'Survived' if random.random() < 0.9 else 'Died'
        
        # If died in ICU, hospital outcome is also died
        if icu_outcome == 'Died':
            hospital_outcome = 'Died'
            hosp_discharge = icu_discharge
        else:
            # 5% die after ICU discharge
            hospital_outcome = 'Survived' if random.random() < 0.95 else 'Died'
        
        # Age (20-95, weighted towards elderly)
        age = max(20, min(95, int(np.random.normal(65, 18))))
        
        # DOB (for testing DOB->age conversion)
        dob = hosp_admission - timedelta(days=age * 365.25)
        
        # Emergency vs Elective (80% emergency)
        admission_type = 'Emergency' if random.random() < 0.8 else 'Elective'
        
        # Diagnosis
        diagnosis = random.choice(diagnoses)
        if diagnosis in ['Myocardial Infarction', 'Cardiac Arrest', 'Heart Failure', 'Arrhythmia']:
            unit = 'C604' if random.random() < 0.7 else random.choice(units)
        else:
            unit = random.choice(units)
        
        data.append({
            'hospital_number': hospital_numbers[i],
            'nhs_number': nhs_numbers[i],
            'date_of_birth': dob.strftime('%Y-%m-%d'),
            'hospital_admission_datetime': hosp_admission.strftime('%Y-%m-%d %H:%M:%S'),
            'hospital_discharge_datetime': hosp_discharge.strftime('%Y-%m-%d %H:%M:%S'),
            'icu_admission_datetime': icu_admission.strftime('%Y-%m-%d %H:%M:%S'),
            'icu_discharge_datetime': icu_discharge.strftime('%Y-%m-%d %H:%M:%S'),
            'icu_unit': unit,
            'admission_source': random.choice(sources),
            'admission_type': admission_type,
            'primary_diagnosis': diagnosis,
            'specialty': random.choice(specialties),
            'icu_outcome': icu_outcome,
            'icu_discharge_destination': 'Ward' if icu_outcome == 'Survived' else 'Died',
            'hospital_outcome': hospital_outcome,
            'hospital_discharge_destination': random.choice(['Home', 'Rehab', 'Nursing home']) if hospital_outcome == 'Survived' else 'Died',
            'postcode': random.choice(postcodes)
        })
    
    df = pd.DataFrame(data)
    
    output_path = 'data/raw/master/TEST_master_data.xlsx'
    df.to_excel(output_path, index=False)
    
    print(f"✓ Created: {output_path}")
    print(f"  Records: {len(df)}")
    print(f"  Columns: {len(df.columns)}")
    print(f"  Date range: {df['hospital_admission_datetime'].min()} to {df['hospital_admission_datetime'].max()}")
    
    return df

def generate_id_link_file(master_df):
    """Generate ID link file from master data"""
    
    print("\nGenerating ID link file...")
    
    link_df = master_df[['hospital_number', 'nhs_number']].copy()
    
    output_path = 'data/raw/master/TEST_id_link_file.csv'
    link_df.to_csv(output_path, index=False)
    
    print(f"✓ Created: {output_path}")
    print(f"  Links: {len(link_df)}")
    
    return link_df

def generate_ventilation_audit(master_df):
    """Generate ventilation audit data"""
    
    print("\nGenerating ventilation audit data...")
    
    # 60% of patients were ventilated
    ventilated_patients = master_df.sample(n=120, random_state=42)
    
    data = []
    
    for _, patient in ventilated_patients.iterrows():
        icu_admission = pd.to_datetime(patient['icu_admission_datetime'])
        icu_discharge = pd.to_datetime(patient['icu_discharge_datetime'])
        icu_los = (icu_discharge - icu_admission).days
        
        # Ventilation days (usually less than ICU LOS)
        vent_days = max(1, min(icu_los, int(np.random.gamma(2, 1.5))))
        
        # Ventilation start (usually within first few hours)
        vent_start = icu_admission + timedelta(hours=random.randint(0, 6))
        
        # VAP (5% rate)
        vap_occurred = 'Yes' if random.random() < 0.05 else 'No'
        
        # If VAP, when did it occur (after 48 hours)
        if vap_occurred == 'Yes' and vent_days > 3:
            vap_day = random.randint(3, vent_days)
            vap_date = vent_start + timedelta(days=vap_day)
        else:
            vap_date = None
            if vap_occurred == 'Yes':
                vap_occurred = 'No'  # Can't have VAP if not ventilated long enough
        
        # Ventilation mode
        vent_modes = ['SIMV', 'PSV', 'CPAP', 'BiPAP', 'Volume Control']
        vent_mode = random.choice(vent_modes)
        
        data.append({
            'hospital_number': patient['hospital_number'],
            'ventilation_start_datetime': vent_start.strftime('%Y-%m-%d %H:%M:%S'),
            'ventilation_days': vent_days,
            'ventilation_mode': vent_mode,
            'vap_occurred': vap_occurred,
            'vap_date': vap_date.strftime('%Y-%m-%d') if vap_date else None,
            'successful_wean': 'Yes' if patient['icu_outcome'] == 'Survived' else 'No'
        })
    
    df = pd.DataFrame(data)
    
    output_path = 'data/raw/audits/ventilation/TEST_ventilation_audit.xlsx'
    df.to_excel(output_path, index=False)
    
    print(f"✓ Created: {output_path}")
    print(f"  Ventilated patients: {len(df)}")
    print(f"  VAP cases: {(df['vap_occurred'] == 'Yes').sum()}")
    
    return df

def generate_renal_audit(master_df):
    """Generate renal replacement therapy audit data"""
    
    print("\nGenerating renal audit data...")
    
    # 25% of patients needed RRT
    rrt_patients = master_df.sample(n=50, random_state=43)
    
    data = []
    
    for _, patient in rrt_patients.iterrows():
        icu_admission = pd.to_datetime(patient['icu_admission_datetime'])
        icu_discharge = pd.to_datetime(patient['icu_discharge_datetime'])
        icu_los = (icu_discharge - icu_admission).days
        
        # RRT start (usually 1-3 days after admission)
        rrt_start_day = random.randint(1, min(3, max(1, icu_los)))
        rrt_start = icu_admission + timedelta(days=rrt_start_day)
        
        # RRT days
        rrt_days = max(1, min(icu_los - rrt_start_day + 1, int(np.random.gamma(2, 2))))
        
        # RRT type
        rrt_types = ['CVVHDF', 'CVVH', 'Intermittent HD', 'SLED']
        rrt_type = random.choice(rrt_types)
        
        # Renal recovery (70% if survived)
        if patient['icu_outcome'] == 'Survived':
            renal_recovery = 'Yes' if random.random() < 0.7 else 'Partial'
        else:
            renal_recovery = 'No'
        
        # Complications (10% rate)
        complications = 'Yes' if random.random() < 0.1 else 'No'
        
        data.append({
            'nhs_number': patient['nhs_number'],
            'rrt_start_datetime': rrt_start.strftime('%Y-%m-%d %H:%M:%S'),
            'rrt_days': rrt_days,
            'rrt_type': rrt_type,
            'renal_recovery': renal_recovery,
            'rrt_complications': complications
        })
    
    df = pd.DataFrame(data)
    
    output_path = 'data/raw/audits/renal/TEST_renal_audit.xlsx'
    df.to_excel(output_path, index=False)
    
    print(f"✓ Created: {output_path}")
    print(f"  RRT patients: {len(df)}")
    print(f"  Renal recovery: {(df['renal_recovery'] == 'Yes').sum()}")
    
    return df

def generate_crbsi_audit(master_df):
    """Generate central line bloodstream infection audit"""
    
    print("\nGenerating CRBSI audit data...")
    
    # 85% of patients had central lines
    line_patients = master_df.sample(n=170, random_state=44)
    
    data = []
    
    for _, patient in line_patients.iterrows():
        icu_admission = pd.to_datetime(patient['icu_admission_datetime'])
        icu_discharge = pd.to_datetime(patient['icu_discharge_datetime'])
        icu_los = (icu_discharge - icu_admission).days
        
        # Line insertion (usually day 0-1)
        line_insert_hours = random.randint(0, 24)
        line_insert = icu_admission + timedelta(hours=line_insert_hours)
        
        # Line days
        line_days = max(1, min(icu_los, int(np.random.gamma(2, 2))))
        
        # Line type
        line_types = ['Internal Jugular', 'Subclavian', 'Femoral', 'PICC']
        line_type = random.choice(line_types)
        
        # CRBSI (2% rate)
        crbsi_occurred = 'Yes' if random.random() < 0.02 else 'No'
        
        # Insertion site
        insertion_sites = ['Right IJ', 'Left IJ', 'Right subclavian', 'Left subclavian', 
                          'Right femoral', 'Left femoral', 'Right PICC', 'Left PICC']
        insertion_site = random.choice(insertion_sites)
        
        data.append({
            'hospital_number': patient['hospital_number'],
            'line_inserted_datetime': line_insert.strftime('%Y-%m-%d %H:%M:%S'),
            'line_days': line_days,
            'line_type': line_type,
            'insertion_site': insertion_site,
            'crbsi_occurred': crbsi_occurred
        })
    
    df = pd.DataFrame(data)
    
    output_path = 'data/raw/audits/crbsi/TEST_crbsi_audit.xlsx'
    df.to_excel(output_path, index=False)
    
    print(f"✓ Created: {output_path}")
    print(f"  Patients with lines: {len(df)}")
    print(f"  CRBSI cases: {(df['crbsi_occurred'] == 'Yes').sum()}")
    
    return df

def generate_cardiac_audit(master_df):
    """Generate cardiac arrest / OHCA audit"""
    
    print("\nGenerating cardiac arrest audit data...")
    
    # Select cardiac arrest patients
    ca_patients = master_df[master_df['primary_diagnosis'] == 'Cardiac Arrest']
    
    if len(ca_patients) == 0:
        print("  (No cardiac arrest patients in test data)")
        return None
    
    data = []
    
    for _, patient in ca_patients.iterrows():
        # Arrest location
        arrest_locations = ['Out of hospital', 'ED', 'Ward', 'Theatre', 'Radiology']
        arrest_location = random.choice(arrest_locations)
        
        # Initial rhythm
        rhythms = ['VF', 'VT', 'PEA', 'Asystole']
        initial_rhythm = random.choice(rhythms)
        
        # ROSC achieved
        rosc = 'Yes' if patient['icu_outcome'] == 'Survived' else random.choice(['Yes', 'No'])
        
        # Time to ROSC (if achieved)
        if rosc == 'Yes':
            time_to_rosc = random.randint(5, 45)
        else:
            time_to_rosc = None
        
        # Neurological outcome (if survived)
        if patient['hospital_outcome'] == 'Survived':
            neuro_outcomes = ['Good (CPC 1-2)', 'Moderate (CPC 3)', 'Poor (CPC 4-5)']
            neuro_outcome = random.choice(neuro_outcomes)
        else:
            neuro_outcome = 'Died'
        
        data.append({
            'hospital_number': patient['hospital_number'],
            'arrest_location': arrest_location,
            'initial_rhythm': initial_rhythm,
            'rosc_achieved': rosc,
            'time_to_rosc_minutes': time_to_rosc,
            'neurological_outcome': neuro_outcome
        })
    
    df = pd.DataFrame(data)
    
    output_path = 'data/raw/audits/cardiac/TEST_cardiac_audit.xlsx'
    df.to_excel(output_path, index=False)
    
    print(f"✓ Created: {output_path}")
    print(f"  Cardiac arrest patients: {len(df)}")
    
    return df

def main():
    """Generate all test data"""
    
    print("=" * 70)
    print("GENERATING TEST DATA")
    print("=" * 70)
    print("\nCreating test dataset with 200 patients...")
    print("This data is for TESTING ONLY and can be completely deleted later.")
    print("")
    
    # Generate master registry
    master_df = generate_master_registry()
    
    # Generate ID link file
    generate_id_link_file(master_df)
    
    # Generate audit files
    generate_ventilation_audit(master_df)
    generate_renal_audit(master_df)
    generate_crbsi_audit(master_df)
    generate_cardiac_audit(master_df)
    
    print("\n" + "=" * 70)
    print("TEST DATA GENERATION COMPLETE")
    print("=" * 70)
    
    print("\n📁 Test files created:")
    print("  Master data:")
    print("    - data/raw/master/TEST_master_data.xlsx (200 patients)")
    print("    - data/raw/master/TEST_id_link_file.csv (200 ID links)")
    print("  Audit data:")
    print("    - data/raw/audits/ventilation/TEST_ventilation_audit.xlsx")
    print("    - data/raw/audits/renal/TEST_renal_audit.xlsx")
    print("    - data/raw/audits/crbsi/TEST_crbsi_audit.xlsx")
    print("    - data/raw/audits/cardiac/TEST_cardiac_audit.xlsx")
    
    print("\n✓ All test data files are prefixed with 'TEST_'")
    print("✓ Easy to identify and delete later")
    
    print("\n🚀 Ready to test! Run:")
    print("  python scripts/test_system_with_data.py")

if __name__ == "__main__":
    main()
