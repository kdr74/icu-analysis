"""
Duplicate detection and handling for ICU data processing
"""

import pandas as pd
from pathlib import Path

class DuplicateDetector:
    """Detect duplicate admissions in patient data"""
    
    def __init__(self, master_registry_path='data/processed/master_registry.csv'):
        self.master_registry_path = Path(master_registry_path)
        self.master_registry = None
        
        if self.master_registry_path.exists():
            self.master_registry = pd.read_csv(master_registry_path)
            # Parse dates for comparison
            for col in ['admission_datetime', 'icu_admission_datetime']:
                if col in self.master_registry.columns:
                    self.master_registry[col] = pd.to_datetime(
                        self.master_registry[col], errors='coerce'
                    )
    
    def find_duplicates(self, new_data):
        """
        Find duplicate records between new data and existing master registry
        
        Returns:
        - duplicates: DataFrame of duplicate records
        - new_only: DataFrame of truly new records
        """
        
        if self.master_registry is None or len(self.master_registry) == 0:
            # No existing data, everything is new
            return pd.DataFrame(), new_data
        
        # Parse dates in new data
        for col in ['admission_datetime', 'icu_admission_datetime']:
            if col in new_data.columns:
                new_data[col] = pd.to_datetime(new_data[col], errors='coerce')
        
        # Try to use icu_admission_datetime first, fall back to admission_datetime
        date_col = 'icu_admission_datetime' if 'icu_admission_datetime' in new_data.columns else 'admission_datetime'
        
        duplicates = []
        new_only = []
        
        for idx, new_row in new_data.iterrows():
            is_duplicate = False
            
            # Find all records for this patient in master registry
            patient_records = self.master_registry[
                self.master_registry['anonymous_patient_id'] == new_row['anonymous_patient_id']
            ]
            
            if len(patient_records) > 0 and date_col in new_row:
                new_admission = new_row[date_col]
                
                for _, existing_row in patient_records.iterrows():
                    if date_col not in existing_row:
                        continue
                        
                    existing_admission = existing_row[date_col]
                    
                    # Check if admission datetimes are within 1 hour of each other
                    if pd.notna(new_admission) and pd.notna(existing_admission):
                        time_diff = abs((new_admission - existing_admission).total_seconds())
                        
                        # If within 1 hour, consider it a duplicate
                        if time_diff < 3600:  # 3600 seconds = 1 hour
                            is_duplicate = True
                            duplicates.append({
                                'anonymous_patient_id': new_row['anonymous_patient_id'],
                                'admission_datetime': new_admission,
                                'existing_admission': existing_admission,
                                'time_difference_minutes': time_diff / 60,
                                'new_data_index': idx
                            })
                            break
            
            if not is_duplicate:
                new_only.append(new_row)
        
        duplicates_df = pd.DataFrame(duplicates)
        new_only_df = pd.DataFrame(new_only)
        
        return duplicates_df, new_only_df
    
    def generate_duplicate_report(self, duplicates_df, output_path='reports/duplicates_detected.csv'):
        """Generate a report of detected duplicates"""
        
        if len(duplicates_df) == 0:
            return None
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        duplicates_df.to_csv(output_path, index=False)
        
        return output_path

