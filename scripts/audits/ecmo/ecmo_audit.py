'''
ECMO usage and outcomes
'''

import sys
sys.path.append('scripts')
sys.path.append('scripts/audits')
from audit_template import AuditTemplate
import pandas as pd

class EcmoAudit(AuditTemplate):
    """ECMO usage and outcomes"""
    
    def __init__(self):
        super().__init__('ecmo')
    
    def generate_statistics(self):
        """Calculate ecmo-specific statistics"""
        
        if self.audit_data is None:
            return {}
        
        merged = self.merge_with_master()
        
        stats = {
            'metadata': {
                'audit_type': 'ecmo',
                'generated': pd.Timestamp.now().isoformat(),
                'total_patients': len(merged)
            }
        }
        
        # TODO: Add specific calculations for ecmo
        
        return stats


def run_ecmo_audit(filepath, identifier_column='hospital_number', 
                          duplicate_action='skip'):
    """Run ecmo audit"""
    
    audit = EcmoAudit()
    audit.process_audit_file(filepath, identifier_column, duplicate_action=duplicate_action)
    audit.save_audit_data()
    
    stats = audit.generate_statistics()
    audit.save_statistics(stats)
    
    print("\n" + "=" * 70)
    print("ECMO AUDIT COMPLETE")
    print("=" * 70)
    
    return audit


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        identifier_column = sys.argv[2] if len(sys.argv) > 2 else 'hospital_number'
        duplicate_action = sys.argv[3] if len(sys.argv) > 3 else 'skip'
        
        run_ecmo_audit(filepath, identifier_column, duplicate_action)
    else:
        print("Usage: python ecmo_audit.py <filepath> [identifier_column] [duplicate_action]")
