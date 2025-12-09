"""
Enhanced patient anonymiser with hospital/NHS number linking
Always checks the ID mapping file before assigning anonymous IDs
"""

import hashlib
import secrets
import json
import pandas as pd
from pathlib import Path

class EnhancedPatientAnonymiser:
    """
    Anonymiser that automatically checks ID mapping file
    Ensures same patient gets same ID regardless of identifier type
    """
    
    def __init__(self, 
                 salt_file='hashing_salt.txt', 
                 mapping_file='data/processed/id_mapping.json',
                 link_file='data/raw/master/id_link_file.csv'):
        
        self.salt_file = Path(salt_file)
        self.mapping_file = Path(mapping_file)
        self.link_file = Path(link_file)
        
        # Load or create salt
        self.salt = self._get_or_create_salt()
        
        # Load existing mapping
        self.mapping = self._load_mapping()
        
        # Load ID link file if available
        self.id_links = self._load_id_links()
        
        # Get next available ID
        self.next_id = self._get_next_id()
        
        print(f"Anonymiser initialized:")
        print(f"  - Existing mappings: {len(self.mapping)}")
        print(f"  - ID links loaded: {len(self.id_links)}")
    
    def _get_or_create_salt(self):
        """Get existing salt or create new one"""
        if self.salt_file.exists():
            with open(self.salt_file, 'r') as f:
                return f.read().strip()
        else:
            salt = secrets.token_hex(32)
            self.salt_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.salt_file, 'w') as f:
                f.write(salt)
            print(f"Created new hashing salt: {self.salt_file}")
            return salt
    
    def _load_mapping(self):
        """Load existing ID mapping"""
        if self.mapping_file.exists():
            with open(self.mapping_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_mapping(self):
        """Save ID mapping to file"""
        self.mapping_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.mapping_file, 'w') as f:
            json.dump(self.mapping, f, indent=2)
    
    def _load_id_links(self):
        """
        Load hospital number <-> NHS number links
        Returns dict: {hosp_num_hash: nhs_num_hash, nhs_num_hash: hosp_num_hash}
        """
        if not self.link_file.exists():
            print(f"  Warning: ID link file not found: {self.link_file}")
            print(f"  Patients will be matched by individual identifiers only")
            return {}
        
        try:
            df = pd.read_csv(self.link_file)
            
            # Validate required columns
            if 'hospital_number' not in df.columns or 'nhs_number' not in df.columns:
                print(f"  Error: Link file must have 'hospital_number' and 'nhs_number' columns")
                return {}
            
            links = {}
            
            for _, row in df.iterrows():
                hosp_num = str(row['hospital_number']).strip()
                nhs_num = str(row['nhs_number']).strip()
                
                # Skip if either is missing
                if pd.isna(hosp_num) or pd.isna(nhs_num) or hosp_num == '' or nhs_num == '':
                    continue
                
                # Create hashes
                hosp_hash = self._create_hash(hosp_num)
                nhs_hash = self._create_hash(nhs_num)
                
                # Bidirectional linking
                links[hosp_hash] = nhs_hash
                links[nhs_hash] = hosp_hash
            
            print(f"  Loaded {len(df)} ID links from: {self.link_file}")
            return links
            
        except Exception as e:
            print(f"  Error loading ID link file: {e}")
            return {}
    
    def _get_next_id(self):
        """Determine next available ID number"""
        if not self.mapping:
            return 1
        
        ids = []
        for anon_id in self.mapping.values():
            if anon_id.startswith('ICU-'):
                num = int(anon_id.replace('ICU-', ''))
                ids.append(num)
        
        return max(ids) + 1 if ids else 1
    
    def _create_hash(self, identifier):
        """Create SHA-256 hash of identifier with salt"""
        # Normalize: uppercase, remove spaces
        identifier = str(identifier).strip().upper().replace(' ', '')
        combined = f"{identifier}{self.salt}"
        hash_object = hashlib.sha256(combined.encode())
        return hash_object.hexdigest()
    
    def get_anonymous_id(self, identifier):
        """
        Get anonymous ID for an identifier
        Checks ID links to ensure linked identifiers get same ID
        """
        hash_value = self._create_hash(identifier)
        
        # Check if this hash has a linked partner
        linked_hash = self.id_links.get(hash_value)
        
        # Check if we've seen this hash before
        if hash_value in self.mapping:
            return self.mapping[hash_value], hash_value
        
        # Check if we've seen the linked hash before
        if linked_hash and linked_hash in self.mapping:
            # Use the same ID as the linked identifier
            anon_id = self.mapping[linked_hash]
            self.mapping[hash_value] = anon_id
            self._save_mapping()
            return anon_id, hash_value
        
        # Create new anonymous ID
        anonymous_id = f"ICU-{self.next_id:06d}"
        self.mapping[hash_value] = anonymous_id
        
        # Also map the linked hash if it exists
        if linked_hash:
            self.mapping[linked_hash] = anonymous_id
        
        self.next_id += 1
        self._save_mapping()
        
        return anonymous_id, hash_value
    
    def anonymise_dataframe(self, df, identifier_column):
        """Anonymise a dataframe by replacing identifier column"""
        if identifier_column not in df.columns:
            raise ValueError(f"Column '{identifier_column}' not found in dataframe")
        
        print(f"  Anonymising {len(df)} records using column: {identifier_column}")
        
        # Create anonymous IDs
        results = df[identifier_column].apply(self.get_anonymous_id)
        df['anonymous_patient_id'] = results.apply(lambda x: x[0])
        df['patient_id_hash'] = results.apply(lambda x: x[1])
        
        # Remove original identifier
        df = df.drop(columns=[identifier_column])
        
        unique_patients = df['anonymous_patient_id'].nunique()
        print(f"  Created/matched {unique_patients} unique anonymous patient IDs")
        
        return df

