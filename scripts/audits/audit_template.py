"""
Base template for all ICU audits with duplicate detection
"""

import sys
sys.path.append('scripts/shared')
from enhanced_anonymiser import EnhancedPatientAnonymiser
from data_sanitizer import DataSanitizer
from duplicate_detector import DuplicateDetector
import pandas as pd
from pathlib import Path
import json

class AuditTemplate:
    """Base class for ICU audits with duplicate detection"""
    
    def __init__(self, audit_name):
        self.audit_name = audit_name
        self.anonymiser = EnhancedPatientAnonymiser()
        self.sanitizer = DataSanitizer()
        self.duplicate_detector = DuplicateDetector()
        self.audit_data = None
        self.master_registry = None
        self.duplicates_found = []
        
        # Load master registry
        master_path = Path('data/processed/master_registry.csv')
        if master_path.exists():
            self.master_registry = pd.read_csv(master_path)
            print(f"Loaded master registry: {len(self.master_registry)} records")
        else:
            print("Warning: Master registry not found")
    
    def process_audit_file(self, filepath, identifier_column, column_mapping=None, 
                          duplicate_action='skip'):
        """Process an audit data file with duplicate detection"""
        
        print("\n" + "=" * 70)
        print(f"{self.audit_name.upper()} AUDIT PROCESSING")
        print("=" * 70)
        print(f"\nFile: {Path(filepath).name}")
        print(f"Duplicate handling: {duplicate_action.upper()}")
        
        # Load
        filepath = Path(filepath)
        if filepath.suffix == '.csv':
            df = pd.read_csv(filepath)
        elif filepath.suffix in ['.xlsx', '.xls']:
            df = pd.read_excel(filepath)
        else:
            raise ValueError(f"Unsupported file format")
        
        print(f"Loaded: {len(df)} rows, {len(df.columns)} columns")
        
        # Sanitize
        df, _ = self.sanitizer.sanitize_dataframe(df)
        
        # Apply column mapping
        if column_mapping:
            df = df.rename(columns=column_mapping)
        
        # Anonymise
        print(f"\n  Anonymising patient identifiers...")
        df = self.anonymiser.anonymise_dataframe(df, identifier_column)
        
        # Check for duplicates
        print(f"\n  Checking for duplicate records...")
        existing_audit_path = Path(f'data/processed/audits/{self.audit_name}_audit.csv')
        
        if existing_audit_path.exists():
            existing_audit = pd.read_csv(existing_audit_path)
            original_master = self.duplicate_detector.master_registry
            self.duplicate_detector.master_registry = existing_audit
            
            duplicates_df, new_only_df = self.duplicate_detector.find_duplicates(df)
            
            self.duplicate_detector.master_registry = original_master
        else:
            duplicates_df = pd.DataFrame()
            new_only_df = df
        
        if len(duplicates_df) > 0:
            print(f"\n  ⚠️  WARNING: Found {len(duplicates_df)} duplicate audit records")
            
            report_path = Path(f'reports/audits/duplicates_{self.audit_name}_{Path(filepath).stem}.csv')
            report_path.parent.mkdir(parents=True, exist_ok=True)
            duplicates_df.to_csv(report_path, index=False)
            print(f"  ✓ Duplicate report saved: {report_path}")
            
            if duplicate_action == 'skip':
                print(f"  Action: SKIP - Excluding {len(duplicates_df)} duplicates")
                df = new_only_df
            elif duplicate_action == 'warn':
                print(f"  Action: WARN - Including duplicates with warning")
            
            self.duplicates_found.extend(duplicates_df.to_dict('records'))
        else:
            print(f"  ✓ No duplicates detected")
        
        self.audit_data = df
        
        print(f"\n  Processed {len(df)} records")
        print(f"  Unique patients: {df['anonymous_patient_id'].nunique()}")
        
        return df
    
    def merge_with_master(self):
        """Merge audit data with master registry"""
        if self.master_registry is None or self.audit_data is None:
            return self.audit_data
        
        merged = self.audit_data.merge(
            self.master_registry,
            on='anonymous_patient_id',
            how='left',
            suffixes=('', '_master')
        )
        
        print(f"\n  Merged with master registry")
        return merged
    
    def generate_statistics(self):
        """Override this in specific audit classes"""
        raise NotImplementedError("Implement in specific audit class")
    
    def save_audit_data(self):
        """Save processed audit data"""
        if self.audit_data is None:
            return
        
        output_path = Path(f'data/processed/audits/{self.audit_name}_audit.csv')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.exists():
            existing = pd.read_csv(output_path)
            combined = pd.concat([existing, self.audit_data], ignore_index=True)
            combined.to_csv(output_path, index=False)
            print(f"\n✓ Audit data updated: {output_path}")
        else:
            self.audit_data.to_csv(output_path, index=False)
            print(f"\n✓ Audit data saved: {output_path}")
    
    def save_statistics(self, stats):
        """Save audit statistics as JSON"""
        output_path = Path(f'data/aggregated/audits/{self.audit_name}_statistics.json')
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"✓ Statistics saved: {output_path}")

