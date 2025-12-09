'''
Length of stay by patient groups
'''

import sys
sys.path.append('scripts')
sys.path.append('scripts/audits')
from audit_template import AuditTemplate
import pandas as pd

class LengthOfStayAudit(AuditTemplate):
    """Length of stay by patient groups"""
    
    def __init__(self):
        super().__init__('length_of_stay')
    
    def generate_statistics(self):
        """Calculate length_of_stay-specific statistics"""
        
        if self.audit_data is None:
            return {}
        
        merged = self.merge_with_master()
        
        stats = {
            'metadata': {
                'audit_type': 'length_of_stay',
                'generated': pd.Timestamp.now().isoformat(),
                'total_patients': len(merged)
            }
        }
        
        # TODO: Add specific calculations for length_of_stay
        
        return stats


def run_length_of_stay_audit(filepath, identifier_column='hospital_number', 
                          duplicate_action='skip'):
    """Run length_of_stay audit"""
    
    audit = LengthOfStayAudit()
    audit.process_audit_file(filepath, identifier_column, duplicate_action=duplicate_action)
    audit.save_audit_data()
    
    stats = audit.generate_statistics()
    audit.save_statistics(stats)
    
    print("\n" + "=" * 70)
    print("LENGTH OF STAY AUDIT COMPLETE")
    print("=" * 70)
    
    return audit


if __name__ == "__main__":
    if len(sys.argv) > 1:
        filepath = sys.argv[1]
        identifier_column = sys.argv[2] if len(sys.argv) > 2 else 'hospital_number'
        duplicate_action = sys.argv[3] if len(sys.argv) > 3 else 'skip'
        
        run_length_of_stay_audit(filepath, identifier_column, duplicate_action)
    else:
        print("Usage: python length_of_stay_audit.py <filepath> [identifier_column] [duplicate_action]")
