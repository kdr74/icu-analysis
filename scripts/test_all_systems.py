"""
Comprehensive test of all ICU analysis systems
"""

import sys
from pathlib import Path
import importlib

print("=" * 70)
print("COMPREHENSIVE SYSTEM TEST")
print("=" * 70)

# Track test results
tests_passed = 0
tests_failed = 0
errors = []

def test_section(name):
    """Print test section header"""
    print(f"\n{'─' * 70}")
    print(f"Testing: {name}")
    print('─' * 70)

def test_result(passed, message):
    """Record and print test result"""
    global tests_passed, tests_failed, errors
    if passed:
        print(f"  ✓ {message}")
        tests_passed += 1
    else:
        print(f"  ✗ {message}")
        tests_failed += 1
        errors.append(message)

# Test 1: Python packages
test_section("Python Package Imports")

try:
    import pandas as pd
    test_result(True, "pandas imported")
except Exception as e:
    test_result(False, f"pandas import failed: {e}")

try:
    import numpy as np
    test_result(True, "numpy imported")
except Exception as e:
    test_result(False, f"numpy import failed: {e}")

try:
    import plotly.express as px
    test_result(True, "plotly imported")
except Exception as e:
    test_result(False, f"plotly import failed: {e}")

try:
    import openpyxl
    test_result(True, "openpyxl imported")
except Exception as e:
    test_result(False, f"openpyxl import failed: {e}")

# Test 2: Directory structure
test_section("Directory Structure")

required_dirs = [
    'data/raw',
    'data/aggregated',
    'data/processed',
    'scripts',
    'docs',
    'visualisation'
]

for dir_path in required_dirs:
    path = Path(dir_path)
    if path.exists():
        test_result(True, f"{dir_path} exists")
    else:
        test_result(False, f"{dir_path} missing")
        path.mkdir(parents=True, exist_ok=True)
        print(f"    Created: {dir_path}")

# Test 3: Critical files exist
test_section("Required Files")

required_files = [
    '.gitignore',
    'README.md',
    'scripts/anonymise_patients.py',
    'scripts/generate_test_data.py',
    'scripts/process_patient_data.py',
    'scripts/validate_registry.py',
    'scripts/test_setup.py'
]

for file_path in required_files:
    path = Path(file_path)
    if path.exists():
        test_result(True, f"{file_path} exists")
    else:
        test_result(False, f"{file_path} missing")

# Test 4: Script imports
test_section("Script Imports")

try:
    from anonymise_patients import PatientAnonymiser
    test_result(True, "PatientAnonymiser class imported")
except Exception as e:
    test_result(False, f"PatientAnonymiser import failed: {e}")

try:
    from process_patient_data import ICUDataProcessor
    test_result(True, "ICUDataProcessor class imported")
except Exception as e:
    test_result(False, f"ICUDataProcessor import failed: {e}")

try:
    from validate_registry import RegistryValidator
    test_result(True, "RegistryValidator class imported")
except Exception as e:
    test_result(False, f"RegistryValidator import failed: {e}")

# Test 5: Anonymisation functionality
test_section("Anonymisation System")

try:
    from anonymise_patients import PatientAnonymiser
    anonymiser = PatientAnonymiser()
    
    # Test hash consistency
    id1_v1, hash1_v1 = anonymiser.get_anonymous_id("H1234567")
    id1_v2, hash1_v2 = anonymiser.get_anonymous_id("H1234567")
    id2, hash2 = anonymiser.get_anonymous_id("H9999999")
    
    if id1_v1 == id1_v2:
        test_result(True, "Same identifier produces same anonymous ID")
    else:
        test_result(False, "Inconsistent anonymous IDs for same identifier")
    
    if id1_v1 != id2:
        test_result(True, "Different identifiers produce different anonymous IDs")
    else:
        test_result(False, "Different identifiers produced same anonymous ID")
    
    if hash1_v1 == hash1_v2:
        test_result(True, "Hash function is deterministic")
    else:
        test_result(False, "Hash function is not deterministic")
    
except Exception as e:
    test_result(False, f"Anonymisation test failed: {e}")

# Test 6: Data processing
test_section("Data Processing")

try:
    from generate_test_data import generate_test_patient_data
    
    # Generate small test dataset
    df = generate_test_patient_data(n_patients=10, output_file='data/raw/system_test_data.csv')
    
    if len(df) == 10:
        test_result(True, "Test data generation (10 records)")
    else:
        test_result(False, f"Expected 10 records, got {len(df)}")
    
    # Test anonymisation
    from anonymise_patients import anonymise_patient_data
    df_anon = anonymise_patient_data(
        'data/raw/system_test_data.csv',
        'hospital_number',
        'data/processed/system_test_anon.csv'
    )
    
    if 'anonymous_patient_id' in df_anon.columns:
        test_result(True, "Anonymisation adds anonymous_patient_id column")
    else:
        test_result(False, "anonymous_patient_id column not created")
    
    if 'hospital_number' not in df_anon.columns:
        test_result(True, "Original identifier removed")
    else:
        test_result(False, "Original identifier still present")
    
except Exception as e:
    test_result(False, f"Data processing test failed: {e}")

# Test 7: Multi-file processing
test_section("Multi-File Processing")

try:
    from process_patient_data import ICUDataProcessor
    processor = ICUDataProcessor()
    
    # Process test file
    processor.process_file(
        'data/raw/system_test_data.csv',
        'hospital_number',
        date_columns={
            'admission_datetime': 'datetime',
            'discharge_datetime': 'datetime'
        }
    )
    
    if processor.master_registry is not None:
        test_result(True, "Master registry created")
    else:
        test_result(False, "Master registry is None")
    
    if len(processor.master_registry) == 10:
        test_result(True, f"Correct record count ({len(processor.master_registry)})")
    else:
        test_result(False, f"Expected 10 records, got {len(processor.master_registry)}")
    
    # Save registry
    processor.save_master_registry('data/processed/system_test_registry.csv')
    
    if Path('data/processed/system_test_registry.csv').exists():
        test_result(True, "Master registry saved successfully")
    else:
        test_result(False, "Master registry file not created")
    
except Exception as e:
    test_result(False, f"Multi-file processing test failed: {e}")

# Test 8: Validation system
test_section("Validation System")

try:
    from validate_registry import RegistryValidator
    validator = RegistryValidator('data/processed/system_test_registry.csv')
    
    test_result(True, "Validator initialized")
    
    # Run checks
    validator.check_required_columns()
    validator.check_date_logic()
    validator.check_categorical_values()
    
    test_result(True, "All validation checks executed")
    
except Exception as e:
    test_result(False, f"Validation test failed: {e}")

# Test 9: Plotly visualization
test_section("Visualization System")

try:
    import plotly.express as px
    
    # Create simple test chart
    test_data = pd.DataFrame({
        'unit': ['A600', 'C604', 'WICU'],
        'count': [10, 15, 12]
    })
    
    fig = px.bar(test_data, x='unit', y='count')
    fig.write_html('docs/system_test_chart.html')
    
    if Path('docs/system_test_chart.html').exists():
        test_result(True, "Plotly chart created and saved")
    else:
        test_result(False, "Plotly chart file not created")
    
except Exception as e:
    test_result(False, f"Visualization test failed: {e}")

# Test 10: .gitignore protection
test_section("Security - .gitignore")

try:
    with open('.gitignore', 'r') as f:
        gitignore_content = f.read()
    
    critical_patterns = [
        'data/raw/',
        '*.csv',
        '*.xlsx',
        'hashing_salt.txt',
        '*_master_registry.*'
    ]
    
    for pattern in critical_patterns:
        if pattern in gitignore_content:
            test_result(True, f".gitignore contains '{pattern}'")
        else:
            test_result(False, f".gitignore missing '{pattern}'")
    
except Exception as e:
    test_result(False, f".gitignore check failed: {e}")

# Final summary
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)
print(f"\nTotal tests run: {tests_passed + tests_failed}")
print(f"✓ Passed: {tests_passed}")
print(f"✗ Failed: {tests_failed}")

if tests_failed > 0:
    print("\nFailed tests:")
    for error in errors:
        print(f"  - {error}")
    print("\n⚠ Some tests failed. Review errors above.")
    sys.exit(1)
else:
    print("\n" + "🎉 " * 10)
    print("ALL SYSTEMS OPERATIONAL")
    print("🎉 " * 10)
    print("\nYour ICU analysis environment is fully functional:")
    print("✓ All packages installed")
    print("✓ Directory structure correct")
    print("✓ All scripts present and working")
    print("✓ Anonymisation system functional")
    print("✓ Data processing pipeline working")
    print("✓ Validation system operational")
    print("✓ Visualization system ready")
    print("✓ Security measures in place")
    print("\nReady for real data processing!")
    sys.exit(0)
