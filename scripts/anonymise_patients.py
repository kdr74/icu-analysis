"""
Patient Data Anonymisation Script
Generates consistent anonymous patient IDs from hospital/NHS numbers
"""

import hashlib
import secrets
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

class PatientAnonymiser:
    """Handles patient identifier anonymisation with consistent hashing"""
    
    def __init__(self, salt_file='hashing_salt.txt'):
        """
        Initialise anonymiser with a secret salt for hashing.
        Salt is generated once and stored locally (never committed to Git).
        """
        self.salt_file = Path(salt_file)
        self.salt = self._get_or_create_salt()
        self.mapping = {}  # Track anonymous_id assignments
        self.next_id = 1
        
    def _get_or_create_salt(self):
        """Get existing salt or create new one"""
        if self.salt_file.exists():
            with open(self.salt_file, 'r') as f:
                return f.read().strip()
        else:
            # Generate cryptographically secure random salt
            salt = secrets.token_hex(32)
            with open(self.salt_file, 'w') as f:
                f.write(salt)
            print(f"Created new hashing salt: {self.salt_file}")
            return salt
    
    def _create_hash(self, identifier):
        """
        Create SHA-256 hash of identifier with salt.
        Same identifier always produces same hash.
        """
        # Normalise identifier (remove spaces, uppercase)
        identifier = str(identifier).strip().upper().replace(' ', '')
        
        # Combine with salt and hash
        combined = f"{identifier}{self.salt}"
        hash_object = hashlib.sha256(combined.encode())
        return hash_object.hexdigest()
    
    def get_anonymous_id(self, identifier):
        """
        Convert hospital/NHS number to anonymous patient ID.
        Returns: tuple of (anonymous_id, hash)
        """
        hash_value = self._create_hash(identifier)
        
        # Check if we've seen this hash before
        if hash_value in self.mapping:
            return self.mapping[hash_value], hash_value
        
        # Create new anonymous ID
        anonymous_id = f"ICU-{self.next_id:06d}"
        self.mapping[hash_value] = anonymous_id
        self.next_id += 1
        
        return anonymous_id, hash_value
    
    def anonymise_dataframe(self, df, identifier_column):
        """
        Anonymise a dataframe by replacing identifier column.
        
        Parameters:
        - df: pandas DataFrame
        - identifier_column: name of column containing hospital/NHS numbers
        
        Returns:
        - DataFrame with anonymous_patient_id and patient_id_hash columns
        """
        if identifier_column not in df.columns:
            raise ValueError(f"Column '{identifier_column}' not found in dataframe")
        
        print(f"Anonymising {len(df)} records...")
        
        # Create anonymous IDs and hashes
        results = df[identifier_column].apply(self.get_anonymous_id)
        df['anonymous_patient_id'] = results.apply(lambda x: x[0])
        df['patient_id_hash'] = results.apply(lambda x: x[1])
        
        # Remove original identifier
        df = df.drop(columns=[identifier_column])
        
        print(f"Created {len(self.mapping)} unique anonymous patient IDs")
        
        return df
    
    def save_mapping_stats(self, output_file='data/aggregated/anonymisation_stats.json'):
        """Save statistics about anonymisation (not the actual mapping)"""
        stats = {
            'total_unique_patients': len(self.mapping),
            'last_anonymous_id': f"ICU-{self.next_id - 1:06d}",
            'timestamp': datetime.now().isoformat()
        }
        
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(stats, f, indent=2)
        
        print(f"Anonymisation stats saved to: {output_file}")


def anonymise_patient_data(input_file, identifier_column, output_file=None):
    """
    Main function to anonymise patient data file.
    
    Parameters:
    - input_file: path to CSV/Excel file with patient data
    - identifier_column: name of column with hospital/NHS numbers
    - output_file: where to save anonymised data (optional)
    
    Returns:
    - Anonymised DataFrame
    """
    print("=" * 60)
    print("ICU PATIENT DATA ANONYMISATION")
    print("=" * 60)
    
    # Load data
    input_path = Path(input_file)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}")
    
    print(f"\nLoading data from: {input_file}")
    
    if input_path.suffix == '.csv':
        df = pd.read_csv(input_file)
    elif input_path.suffix in ['.xlsx', '.xls']:
        df = pd.read_excel(input_file)
    else:
        raise ValueError("File must be .csv, .xlsx, or .xls")
    
    print(f"Loaded {len(df)} rows, {len(df.columns)} columns")
    print(f"Columns: {', '.join(df.columns)}")
    
    # Anonymise
    anonymiser = PatientAnonymiser()
    df_anon = anonymiser.anonymise_dataframe(df, identifier_column)
    
    # Save if output file specified
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if output_path.suffix == '.csv':
            df_anon.to_csv(output_file, index=False)
        elif output_path.suffix in ['.xlsx', '.xls']:
            df_anon.to_excel(output_file, index=False)
        
        print(f"\nAnonymised data saved to: {output_file}")
        anonymiser.save_mapping_stats()
    
    print("\n" + "=" * 60)
    print("ANONYMISATION COMPLETE")
    print("=" * 60)
    print("\nREMINDER: Original file contains identifiable data.")
    print("Keep it secure. Do not commit to Git.")
    
    return df_anon


# Example usage
if __name__ == "__main__":
    print("\nPatient Anonymisation Script")
    print("-" * 60)
    print("\nThis script is ready to use. Example usage:\n")
    print("from scripts.anonymise_patients import anonymise_patient_data")
    print("\ndf = anonymise_patient_data(")
    print("    input_file='data/raw/patient_data.csv',")
    print("    identifier_column='hospital_number',")
    print("    output_file='data/processed/master_registry.csv'")
    print(")\n")
