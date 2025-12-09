'''
ICU-acquired bloodstream infections
'''

import sys
sys.path.append('scripts')
sys.path.append('scripts/audits')
from audit_template import AuditTemplate
import pandas as pd

class IcuBsiAudit(AuditTemplate):
    """ICU-acquired bloodstream infections"""
    
    def __init__(self):
        super().__init__('icu_bsi')
    
    def generate_statistics(self):
        """Calculate icu_bsi-specific statistics"""
        
        if self.audit_data is None:
            return {}
        
        merged = self.merge_with_master()
        
        stats = {
            'metadata': {
                'audit_type': 'icu_bsi',
                'generated': pd.Timestamp.now().isoformat(),
                'total_patients': len(merged)
            }
        }
        
        # TODO: Add specific calculations for icu_bsi
        
        return stats


def run_icu_bsi_audit(filepath, identifier_column='hospital_number', 
                          duplicate_action='skip'):
    """Run icu_bsi audit"""
    
    audit = IcuBsiAudit()
    audit.process_audit_file(filepath, identifier_column, duplicate_action=duplicate_action)
    audit.save_audit_data()
    
    stats = audit.generate_statistics()
    audit.save_statistics(stats)
    
    print("\n" + "=" * 70)
    print("ICU BSI AUDIT COMPLETE")
    print("=" * 70)
    
    return audit


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        identifier_column = sys.argv[2] if len(sys.argv) > 2 else 'hospital_number'
        duplicate_action = sys.argv[3] if len(sys.argv) > 3 else 'skip'
        
        run_icu_bsi_audit(filepath, identifier_column, duplicate_action)
    else:
        print("Usage: python icu_bsi_audit.py <filepath> [identifier_column] [duplicate_action]")
