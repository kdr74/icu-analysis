"""
Data Processing Pipeline for ICU Patient Database
Merges multiple data sources into master patient registry
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from anonymise_patients import PatientAnonymiser
import json

class ICUDataProcessor:
    """Processes and merges ICU patient data from multiple sources"""
    
    def __init__(self):
        self.anonymiser = PatientAnonymiser()
        self.master_registry = None
        self.processing_log = []
        
    def load_data_file(self, filepath, identifier_column):
        """
        Load a data file (CSV or Excel) and identify the patient identifier column.
        
        Parameters:
        - filepath: path to data file
        - identifier_column: name of column containing hospital_number or nhs_number
        
        Returns:
        - DataFrame with loaded data
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        print(f"\nLoading: {filepath.name}")
        
        # Load based on file type
        if filepath.suffix == '.csv':
            df = pd.read_csv(filepath)
        elif filepath.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format: {filepath.suffix}")
        
        print(f"  Rows: {len(df)}")
        print(f"  Columns: {len(df.columns)}")
        
        # Verify identifier column exists
        if identifier_column not in df.columns:
            raise ValueError(f"Column '{identifier_column}' not found in {filepath.name}")
        
        self.processing_log.append({
            'timestamp': datetime.now().isoformat(),
            'file': str(filepath),
            'rows': len(df),
            'identifier_column': identifier_column
        })
        
        return df
    
    def standardise_columns(self, df, column_mapping):
        """
        Standardise column names to match master registry schema.
        
        Parameters:
        - df: DataFrame to standardise
        - column_mapping: dict mapping source columns to standard names
          Example: {'hosp_num': 'hospital_number', 'dob': 'date_of_birth'}
        
        Returns:
        - DataFrame with standardised column names
        """
        # Rename columns according to mapping
        df = df.rename(columns=column_mapping)
        
        return df
    
    def parse_dates(self, df, date_columns):
        """
        Parse date and datetime columns to standard format.
        
        Parameters:
        - df: DataFrame
        - date_columns: dict of {column_name: 'date'|'datetime'}
        
        Returns:
        - DataFrame with parsed dates
        """
        for col, dtype in date_columns.items():
            if col in df.columns:
                if dtype == 'date':
                    df[col] = pd.to_datetime(df[col], errors='coerce').dt.date
                elif dtype == 'datetime':
                    df[col] = pd.to_datetime(df[col], errors='coerce')
        
        return df
    
    def validate_data(self, df):
        """
        Perform data quality checks.
        
        Returns:
        - DataFrame with issues flagged
        - List of validation issues found
        """
        issues = []
        
        # Check for required columns
        required_cols = ['anonymous_patient_id', 'admission_datetime']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            issues.append(f"Missing required columns: {missing_cols}")
        
        # Check admission before discharge
        if 'admission_datetime' in df.columns and 'discharge_datetime' in df.columns:
            invalid_dates = df[df['discharge_datetime'] < df['admission_datetime']]
            if len(invalid_dates) > 0:
                issues.append(f"Found {len(invalid_dates)} records where discharge before admission")
                print(f"  WARNING: {len(invalid_dates)} records with discharge before admission")
        
        # Check for null patient IDs
        if 'anonymous_patient_id' in df.columns:
            null_ids = df['anonymous_patient_id'].isna().sum()
            if null_ids > 0:
                issues.append(f"Found {null_ids} records with null patient IDs")
                print(f"  WARNING: {null_ids} records with null patient IDs")
        
        # Check ICU unit values
        if 'icu_unit' in df.columns:
            valid_units = ['A600', 'C604', 'WICU']
            invalid_units = df[~df['icu_unit'].isin(valid_units + [np.nan])]
            if len(invalid_units) > 0:
                issues.append(f"Found {len(invalid_units)} records with invalid ICU unit")
                print(f"  WARNING: {len(invalid_units)} records with invalid ICU unit")
                print(f"  Invalid values: {invalid_units['icu_unit'].unique().tolist()}")
        
        if not issues:
            print("  ✓ Data validation passed")
        
        return df, issues
    
    def merge_with_master(self, new_data, merge_strategy='update'):
        """
        Merge new data with existing master registry.
        
        Parameters:
        - new_data: DataFrame with new records
        - merge_strategy: 'update' (update existing) or 'append' (only add new)
        
        Returns:
        - Updated master registry
        """
        if self.master_registry is None:
            print("  Creating new master registry")
            self.master_registry = new_data.copy()
            return self.master_registry
        
        print(f"  Merging with existing registry ({len(self.master_registry)} records)")
        
        # Identify new vs existing records
        existing_ids = set(self.master_registry['anonymous_patient_id'])
        new_ids = set(new_data['anonymous_patient_id'])
        
        truly_new = new_ids - existing_ids
        overlapping = new_ids & existing_ids
        
        print(f"  - New patients: {len(truly_new)}")
        print(f"  - Existing patients: {len(overlapping)}")
        
        if merge_strategy == 'update':
            # Update existing records with new data
            for patient_id in overlapping:
                # Get existing and new record
                existing_idx = self.master_registry[
                    self.master_registry['anonymous_patient_id'] == patient_id
                ].index[0]
                new_record = new_data[
                    new_data['anonymous_patient_id'] == patient_id
                ].iloc[0]
                
                # Update non-null values
                for col in new_data.columns:
                    if col in self.master_registry.columns:
                        if pd.notna(new_record[col]):
                            self.master_registry.at[existing_idx, col] = new_record[col]
        
        # Add truly new records
        new_records = new_data[new_data['anonymous_patient_id'].isin(truly_new)]
        self.master_registry = pd.concat([self.master_registry, new_records], ignore_index=True)
        
        print(f"  Updated registry: {len(self.master_registry)} total records")
        
        return self.master_registry
    
    def process_file(self, filepath, identifier_column, column_mapping=None, 
                     date_columns=None, merge_strategy='update'):
        """
        Complete processing workflow for a single file.
        
        Parameters:
        - filepath: path to data file
        - identifier_column: column with hospital/NHS number
        - column_mapping: optional dict to rename columns
        - date_columns: optional dict of date columns to parse
        - merge_strategy: 'update' or 'append'
        
        Returns:
        - Updated master registry
        """
        print("\n" + "=" * 70)
        print(f"PROCESSING: {Path(filepath).name}")
        print("=" * 70)
        
        # Load data
        df = self.load_data_file(filepath, identifier_column)
        
        # Standardise column names if mapping provided
        if column_mapping:
            print("  Standardising column names...")
            df = self.standardise_columns(df, column_mapping)
        
        # Parse dates if specified
        if date_columns:
            print("  Parsing date columns...")
            df = self.parse_dates(df, date_columns)
        
        # Anonymise
        print("  Anonymising patient identifiers...")
        df = self.anonymiser.anonymise_dataframe(df, identifier_column)
        
        # Validate
        print("  Validating data quality...")
        df, issues = self.validate_data(df)
        
        # Merge with master
        print("  Merging with master registry...")
        self.master_registry = self.merge_with_master(df, merge_strategy)
        
        return self.master_registry
    
    def save_master_registry(self, output_path='data/processed/master_registry.csv'):
        """Save master registry to file"""
        if self.master_registry is None:
            print("No data to save")
            return
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.master_registry.to_csv(output_path, index=False)
        print(f"\n✓ Master registry saved: {output_path}")
        print(f"  Total records: {len(self.master_registry)}")
        print(f"  Unique patients: {self.master_registry['anonymous_patient_id'].nunique()}")
        
        # Save processing log
        log_path = output_path.parent / 'processing_log.json'
        with open(log_path, 'w') as f:
            json.dump(self.processing_log, f, indent=2)
        print(f"  Processing log: {log_path}")
    
    def get_summary_statistics(self):
        """Generate summary statistics of master registry"""
        if self.master_registry is None:
            return None
        
        stats = {
            'total_records': len(self.master_registry),
            'unique_patients': self.master_registry['anonymous_patient_id'].nunique(),
            'date_range': {
                'earliest_admission': str(self.master_registry['admission_datetime'].min()),
                'latest_admission': str(self.master_registry['admission_datetime'].max())
            }
        }
        
        # Unit distribution
        if 'icu_unit' in self.master_registry.columns:
            stats['unit_distribution'] = self.master_registry['icu_unit'].value_counts().to_dict()
        
        # Outcome distribution
        if 'icu_outcome' in self.master_registry.columns:
            stats['icu_outcome_distribution'] = self.master_registry['icu_outcome'].value_counts().to_dict()
        
        return stats


def example_single_file_processing():
    """Example: Process a single data file"""
    processor = ICUDataProcessor()
    
    # Process file
    processor.process_file(
        filepath='data/raw/patient_data.csv',
        identifier_column='hospital_number',
        date_columns={
            'date_of_birth': 'date',
            'admission_datetime': 'datetime',
            'discharge_datetime': 'datetime'
        }
    )
    
    # Save
    processor.save_master_registry()
    
    # Print summary
    stats = processor.get_summary_statistics()
    print("\n" + "=" * 70)
    print("SUMMARY STATISTICS")
    print("=" * 70)
    print(json.dumps(stats, indent=2))


def example_multiple_file_processing():
    """Example: Process multiple data files and merge"""
    processor = ICUDataProcessor()
    
    # File 1: Main admissions database
    processor.process_file(
        filepath='data/raw/admissions_export.xlsx',
        identifier_column='hospital_number',
        column_mapping={
            'hosp_num': 'hospital_number',
            'dob': 'date_of_birth',
            'admit_dt': 'admission_datetime',
            'dc_dt': 'discharge_datetime'
        },
        date_columns={
            'date_of_birth': 'date',
            'admission_datetime': 'datetime',
            'discharge_datetime': 'datetime'
        }
    )
    
    # File 2: Outcomes data (using NHS numbers)
    processor.process_file(
        filepath='data/raw/outcomes_data.csv',
        identifier_column='nhs_number',
        column_mapping={
            'nhs_num': 'nhs_number'
        },
        merge_strategy='update'
    )
    
    # Save merged registry
    processor.save_master_registry()


if __name__ == "__main__":
    print("\nICU Data Processing Pipeline")
    print("-" * 70)
    print("\nThis script is ready to use. Example usage:\n")
    print("from scripts.process_patient_data import ICUDataProcessor")
    print("\nprocessor = ICUDataProcessor()")
    print("processor.process_file(")
    print("    filepath='data/raw/your_file.xlsx',")
    print("    identifier_column='hospital_number',")
    print("    date_columns={'admission_datetime': 'datetime'}")
    print(")")
    print("processor.save_master_registry()")
    print()
