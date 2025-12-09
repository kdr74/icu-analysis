"""
Data sanitizer - removes patient names and sensitive information
Runs automatically on all data before processing
"""

import pandas as pd
import re

class DataSanitizer:
    """Remove sensitive columns and data from patient files"""
    
    # Forbidden column names (case-insensitive)
    FORBIDDEN_COLUMNS = [
        'name', 'patient_name', 'surname', 'forename', 'first_name', 'last_name',
        'full_name', 'patient_surname', 'patient_forename', 'firstname', 'lastname',
        'middle_name', 'maiden_name', 'preferred_name', 'known_as',
        'address', 'street', 'house_number', 'flat_number', 'address_line_1', 
        'address_line_2', 'full_address', 'patient_address',
        'phone', 'telephone', 'mobile', 'contact_number', 'phone_number',
        'email', 'email_address', 'patient_email',
        'next_of_kin', 'nok_name', 'relative_name', 'contact_name',
        'gp_name', 'gp_address', 'gp_practice'
    ]
    
    def __init__(self):
        self.removed_columns = []
        self.modified_columns = []
    
    def sanitize_dataframe(self, df):
        """
        Remove sensitive columns and sanitize data
        Returns cleaned dataframe and report of changes
        """
        print("\n  Sanitizing data...")
        
        df_clean = df.copy()
        
        # 1. Remove forbidden columns
        df_clean = self._remove_forbidden_columns(df_clean)
        
        # 2. Process postcode column if present
        df_clean = self._sanitize_postcode(df_clean)
        
        # 3. Convert DOB to age if present
        df_clean = self._convert_dob_to_age(df_clean)
        
        # 4. Check for names in free text fields
        df_clean = self._check_free_text_fields(df_clean)
        
        # Generate report
        report = self._generate_sanitization_report()
        
        return df_clean, report
    
    def _remove_forbidden_columns(self, df):
        """Remove columns containing sensitive information"""
        columns_to_remove = []
        
        for col in df.columns:
            col_lower = str(col).lower().strip()
            
            # Check if column name matches forbidden list
            if col_lower in self.FORBIDDEN_COLUMNS:
                columns_to_remove.append(col)
            
            # Also check for partial matches
            elif any(forbidden in col_lower for forbidden in 
                    ['name', 'address', 'phone', 'email']):
                # Except for specific allowed cases
                if col_lower not in ['postcode', 'home_postcode', 'postcode_area']:
                    columns_to_remove.append(col)
        
        if columns_to_remove:
            print(f"    ⚠️  Removing {len(columns_to_remove)} sensitive columns:")
            for col in columns_to_remove:
                print(f"       - {col}")
            
            df = df.drop(columns=columns_to_remove)
            self.removed_columns.extend(columns_to_remove)
        else:
            print(f"    ✓ No forbidden column names detected")
        
        return df
    
    def _sanitize_postcode(self, df):
        """Keep only first part of postcode (e.g., BS2 8HW → BS2)"""
        postcode_columns = [col for col in df.columns 
                           if 'postcode' in str(col).lower()]
        
        for col in postcode_columns:
            if col in df.columns:
                print(f"    Processing postcode column: {col}")
                
                # Extract first part of UK postcode
                df[f'{col}_area'] = df[col].apply(self._extract_postcode_area)
                
                # Remove full postcode column
                df = df.drop(columns=[col])
                
                self.modified_columns.append(f"{col} → {col}_area (first part only)")
                print(f"       Converted to postcode area only")
        
        return df
    
    def _extract_postcode_area(self, postcode):
        """Extract first part of UK postcode"""
        if pd.isna(postcode):
            return None
        
        postcode = str(postcode).strip().upper().replace(' ', '')
        
        # UK postcode pattern: 1-2 letters + 1-2 numbers
        match = re.match(r'^([A-Z]{1,2}\d{1,2})', postcode)
        
        if match:
            return match.group(1)
        
        return None
    
    def _convert_dob_to_age(self, df):
        """Convert date of birth to age at admission"""
        dob_columns = [col for col in df.columns 
                      if any(x in str(col).lower() for x in ['dob', 'date_of_birth', 'birth_date'])]
        
        for dob_col in dob_columns:
            if dob_col in df.columns:
                print(f"    Converting DOB to age: {dob_col}")
                
                # Need admission date to calculate age
                admission_col = None
                for col in df.columns:
                    if 'admission' in str(col).lower() and ('date' in str(col).lower() or 'time' in str(col).lower()):
                        admission_col = col
                        break
                
                if admission_col:
                    # Convert to datetime
                    df[dob_col] = pd.to_datetime(df[dob_col], errors='coerce')
                    df[admission_col] = pd.to_datetime(df[admission_col], errors='coerce')
                    
                    # Calculate age at admission
                    df['age_at_admission'] = (
                        (df[admission_col] - df[dob_col]).dt.days / 365.25
                    ).round(0).astype('Int64')
                    
                    # Remove DOB column
                    df = df.drop(columns=[dob_col])
                    
                    self.modified_columns.append(f"{dob_col} → age_at_admission")
                    print(f"       Converted to age_at_admission")
                else:
                    # No admission date available, just remove DOB
                    df = df.drop(columns=[dob_col])
                    self.removed_columns.append(dob_col)
                    print(f"       Removed (no admission date to calculate age)")
        
        return df
    
    def _check_free_text_fields(self, df):
        """Warn if free text fields might contain names"""
        text_columns = df.select_dtypes(include=['object']).columns
        
        suspicious_columns = []
        
        for col in text_columns:
            # Skip if already identified as problematic
            if col in self.removed_columns:
                continue
            
            # Sample some values
            sample = df[col].dropna().head(10)
            
            # Very basic check for potential names
            for value in sample:
                value_str = str(value)
                # Check if value looks like a name (capitalized words)
                if re.search(r'\b[A-Z][a-z]+ [A-Z][a-z]+\b', value_str):
                    suspicious_columns.append(col)
                    break
        
        if suspicious_columns:
            print(f"    ⚠️  Warning: These columns might contain names:")
            for col in suspicious_columns:
                print(f"       - {col} (review manually)")
        
        return df
    
    def _generate_sanitization_report(self):
        """Generate report of sanitization actions"""
        report = {
            'removed_columns': self.removed_columns,
            'modified_columns': self.modified_columns
        }
        return report

