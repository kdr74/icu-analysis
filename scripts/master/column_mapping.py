"""
Column mapping for automatic standardization
Import this in processing scripts
"""

# Standard column mapping - applies to all files
STANDARD_COLUMN_MAP = {
    # ICU ward/unit
    'Unit': 'icu_ward',
    'unit': 'icu_ward',
    'ICU_unit': 'icu_ward',
    'ward': 'icu_ward',
    
    # ICU admission date
    'Ward Attendance Start Date': 'ICU_admit_date',
    'ICU_admission_date': 'ICU_admit_date',
    'icu_admission_datetime': 'ICU_admit_date',
    
    # ICU discharge date
    'Ward Attendance End Date': 'ICU_discharge_date',
    'ICU_discharge_datetime': 'ICU_discharge_date',
    
    # Hospital admission
    'Hospital Admission Date': 'hospital_admit_date',
    
    # Hospital discharge
    'Hospital Discharge Date': 'BRI_hospital_discharge_date',
    
    # Consultant
    'Consultant': 'consultant',
    'CONSULTANT': 'consultant',
    
    # Discharge method
    'Discharge Method': 'discharge_method',
    
    # Discharge destination
    'Discharge Destination': 'BRI_discharge_destination',
    
    # Patient classification
    'Patient Classification': 'patient_classification',
    
    # Hours in ward
    'Hours in Ward': 'hours_on_ward_sls',
    
    # Specialty
    'Specialty': 'specialty',
    'SPECIALTY': 'specialty',
    
    # Trust number
    'Trust Number': 'hospital_number',
}

def apply_standard_mapping(df):
    """Apply standard column mapping and remove duplicates"""
    # Rename columns
    df = df.rename(columns=STANDARD_COLUMN_MAP)
    
    # Remove duplicate columns (keep first)
    df = df.loc[:, ~df.columns.duplicated()]
    
    return df
