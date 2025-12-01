"""
Test that dashboard can load and all required files are present
"""

from pathlib import Path
import json

print("=" * 70)
print("DASHBOARD DEPLOYMENT TEST")
print("=" * 70)

# Check required files
required_files = [
    'docs/index.html',
    'docs/dashboard.js',
    'docs/README.md',
    'data/aggregated/complete_statistics.json',
    'data/aggregated/monthly_admissions.json',
    'data/aggregated/unit_distribution.json',
    'data/aggregated/outcome_statistics.json',
    'data/aggregated/diagnosis_distribution.json',
    'data/aggregated/length_of_stay.json',
    'data/aggregated/admission_sources.json',
    'data/aggregated/specialties.json'
]

missing = []
for file_path in required_files:
    if Path(file_path).exists():
        print(f"✓ {file_path}")
    else:
        print(f"✗ {file_path} MISSING")
        missing.append(file_path)

# Validate JSON files
print("\n" + "-" * 70)
print("VALIDATING JSON FILES")
print("-" * 70)

json_files = [f for f in required_files if f.endswith('.json')]
for json_file in json_files:
    path = Path(json_file)
    if path.exists():
        try:
            with open(path, 'r') as f:
                data = json.load(f)
            print(f"✓ {json_file} - valid JSON")
        except json.JSONDecodeError as e:
            print(f"✗ {json_file} - INVALID JSON: {e}")
            missing.append(json_file)

# Check data structure
print("\n" + "-" * 70)
print("CHECKING DATA STRUCTURE")
print("-" * 70)

stats_path = Path('data/aggregated/complete_statistics.json')
if stats_path.exists():
    with open(stats_path, 'r') as f:
        stats = json.load(f)
    
    required_keys = [
        'metadata',
        'monthly_admissions',
        'unit_distribution',
        'diagnosis_distribution',
        'outcome_statistics',
        'length_of_stay',
        'admission_sources',
        'specialties'
    ]
    
    for key in required_keys:
        if key in stats:
            print(f"✓ {key} present")
        else:
            print(f"✗ {key} MISSING")
            missing.append(f"complete_statistics.json:{key}")

# Summary
print("\n" + "=" * 70)
if missing:
    print("DEPLOYMENT TEST FAILED")
    print("=" * 70)
    print(f"\n{len(missing)} issues found:")
    for item in missing:
        print(f"  - {item}")
    print("\nFix these issues before deploying.")
else:
    print("DEPLOYMENT TEST PASSED")
    print("=" * 70)
    print("\n✓ All required files present")
    print("✓ All JSON files valid")
    print("✓ Data structure correct")
    print("\nDashboard ready for deployment!")
    print("\nTo deploy:")
    print("1. git add docs/ data/aggregated/")
    print("2. git commit -m 'Deploy dashboard'")
    print("3. git push")
    print("4. Enable GitHub Pages in repository settings")
    print(f"5. Access at: https://yourusername.github.io/icu-analysis/")
