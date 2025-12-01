"""
Comprehensive validation checks for master patient registry
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

class RegistryValidator:
    """Validates master patient registry data quality"""
    
    def __init__(self, registry_path):
        """Load registry for validation"""
        self.registry_path = Path(registry_path)
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {registry_path}")
        
        self.df = pd.read_csv(registry_path)
        self.issues = []
        self.warnings = []
        
    def check_required_columns(self):
        """Verify all required columns are present"""
        required = [
            'anonymous_patient_id',
            'patient_id_hash',
            'admission_datetime'
        ]
        
        missing = [col for col in required if col not in self.df.columns]
        
        if missing:
            self.issues.append({
                'check': 'required_columns',
                'severity': 'ERROR',
                'message': f"Missing required columns: {missing}"
            })
            return False
        
        return True
    
    def check_duplicate_patients(self):
        """Check for duplicate patient IDs"""
        duplicates = self.df['anonymous_patient_id'].duplicated().sum()
        
        if duplicates > 0:
            self.warnings.append({
                'check': 'duplicate_patients',
                'severity': 'WARNING',
                'message': f"Found {duplicates} duplicate patient records",
                'detail': 'Multiple admissions per patient are expected'
            })
        
        return duplicates
    
    def check_date_logic(self):
        """Verify date fields are logical"""
        date_issues = 0
        
        # Parse dates
        if 'admission_datetime' in self.df.columns:
            self.df['admission_datetime'] = pd.to_datetime(
                self.df['admission_datetime'], errors='coerce'
            )
        
        if 'discharge_datetime' in self.df.columns:
            self.df['discharge_datetime'] = pd.to_datetime(
                self.df['discharge_datetime'], errors='coerce'
            )
        
        # Check discharge after admission
        if 'admission_datetime' in self.df.columns and 'discharge_datetime' in self.df.columns:
            invalid = self.df[
                self.df['discharge_datetime'] < self.df['admission_datetime']
            ]
            
            if len(invalid) > 0:
                date_issues += len(invalid)
                self.issues.append({
                    'check': 'date_logic',
                    'severity': 'ERROR',
                    'message': f"{len(invalid)} records with discharge before admission",
                    'patient_ids': invalid['anonymous_patient_id'].tolist()[:5]
                })
        
        # Check for future dates
        now = pd.Timestamp.now()
        if 'admission_datetime' in self.df.columns:
            future_admissions = self.df[self.df['admission_datetime'] > now]
            if len(future_admissions) > 0:
                date_issues += len(future_admissions)
                self.warnings.append({
                    'check': 'future_dates',
                    'severity': 'WARNING',
                    'message': f"{len(future_admissions)} records with future admission dates"
                })
        
        return date_issues
    
    def check_categorical_values(self):
        """Verify categorical fields have valid values"""
        issues_found = 0
        
        # ICU units
        if 'icu_unit' in self.df.columns:
            valid_units = ['A600', 'C604', 'WICU']
            invalid = self.df[
                ~self.df['icu_unit'].isin(valid_units) & 
                self.df['icu_unit'].notna()
            ]
            
            if len(invalid) > 0:
                issues_found += len(invalid)
                self.issues.append({
                    'check': 'icu_unit_values',
                    'severity': 'ERROR',
                    'message': f"{len(invalid)} records with invalid ICU unit",
                    'invalid_values': invalid['icu_unit'].unique().tolist()
                })
        
        # Outcomes
        if 'icu_outcome' in self.df.columns:
            valid_outcomes = ['Survived', 'Died']
            invalid = self.df[
                ~self.df['icu_outcome'].isin(valid_outcomes) & 
                self.df['icu_outcome'].notna()
            ]
            
            if len(invalid) > 0:
                issues_found += len(invalid)
                self.warnings.append({
                    'check': 'icu_outcome_values',
                    'severity': 'WARNING',
                    'message': f"{len(invalid)} records with non-standard outcome values",
                    'invalid_values': invalid['icu_outcome'].unique().tolist()
                })
        
        return issues_found
    
    def check_completeness(self):
        """Check data completeness (null values)"""
        completeness = {}
        
        for col in self.df.columns:
            null_count = self.df[col].isna().sum()
            null_pct = (null_count / len(self.df)) * 100
            completeness[col] = {
                'null_count': int(null_count),
                'null_percentage': round(null_pct, 2)
            }
            
            # Flag high null rates
            if null_pct > 50 and col not in ['hospital_outcome', 'hospital_discharge_destination']:
                self.warnings.append({
                    'check': 'completeness',
                    'severity': 'WARNING',
                    'message': f"Column '{col}' is {null_pct:.1f}% null"
                })
        
        return completeness
    
    def run_all_checks(self):
        """Run all validation checks"""
        print("\n" + "=" * 70)
        print("MASTER REGISTRY VALIDATION")
        print("=" * 70)
        print(f"\nRegistry: {self.registry_path}")
        print(f"Records: {len(self.df)}")
        print(f"Columns: {len(self.df.columns)}")
        
        # Run checks
        print("\nRunning validation checks...")
        
        self.check_required_columns()
        self.check_duplicate_patients()
        self.check_date_logic()
        self.check_categorical_values()
        completeness = self.check_completeness()
        
        # Report results
        print("\n" + "-" * 70)
        print("VALIDATION RESULTS")
        print("-" * 70)
        
        if not self.issues:
            print("\n✓ No critical issues found")
        else:
            print(f"\n✗ Found {len(self.issues)} critical issues:")
            for issue in self.issues:
                print(f"\n  ERROR: {issue['message']}")
                if 'patient_ids' in issue:
                    print(f"  Example patient IDs: {issue['patient_ids']}")
        
        if self.warnings:
            print(f"\n⚠ Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"\n  WARNING: {warning['message']}")
        
        # Completeness summary
        print("\n" + "-" * 70)
        print("DATA COMPLETENESS")
        print("-" * 70)
        
        high_null = {k: v for k, v in completeness.items() if v['null_percentage'] > 20}
        if high_null:
            print("\nColumns with >20% null values:")
            for col, stats in high_null.items():
                print(f"  {col}: {stats['null_percentage']}% null")
        else:
            print("\n✓ All columns have good completeness (<20% null)")
        
        # Save validation report
        report = {
            'timestamp': datetime.now().isoformat(),
            'registry_path': str(self.registry_path),
            'record_count': len(self.df),
            'unique_patients': int(self.df['anonymous_patient_id'].nunique()),
            'issues': self.issues,
            'warnings': self.warnings,
            'completeness': completeness
        }
        
        report_path = self.registry_path.parent / 'validation_report.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n✓ Validation report saved: {report_path}")
        
        return len(self.issues) == 0


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        registry_path = sys.argv[1]
    else:
        registry_path = 'data/processed/master_registry.csv'
    
    validator = RegistryValidator(registry_path)
    passed = validator.run_all_checks()
    
    sys.exit(0 if passed else 1)
