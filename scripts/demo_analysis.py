"""
Demonstration of analysis and aggregation workflow
"""

from analyse_registry import ICUAnalyser
import json

print("=" * 70)
print("ICU DATA ANALYSIS DEMONSTRATION")
print("=" * 70)

# Use the test registry we created earlier
print("\n[1/3] Loading test registry...")

try:
    analyser = ICUAnalyser('data/processed/test_master_registry.csv')
except FileNotFoundError:
    print("\nTest registry not found. Generating new test data...")
    from demo_multi_file_processing import *
    analyser = ICUAnalyser('data/processed/test_master_registry.csv')

print("\n[2/3] Generating statistics...")

# Individual statistics
print("\n" + "-" * 70)
print("Unit Distribution:")
print("-" * 70)
unit_dist = analyser.unit_distribution()
for unit, count in unit_dist.items():
    print(f"  {unit}: {count}")

print("\n" + "-" * 70)
print("Outcome Statistics:")
print("-" * 70)
outcomes = analyser.outcome_statistics(by_unit=True)
print(json.dumps(outcomes, indent=2))

print("\n" + "-" * 70)
print("Length of Stay Statistics (days):")
print("-" * 70)
los = analyser.length_of_stay_statistics(by_unit=True)
for unit, stats in los.items():
    print(f"\n  {unit}:")
    print(f"    Median: {stats['median']} days")
    print(f"    IQR: {stats['q25']} - {stats['q75']} days")
    print(f"    Count: {stats['count']}")

print("\n" + "-" * 70)
print("Diagnosis Distribution (Top 10):")
print("-" * 70)
diagnoses = analyser.diagnosis_distribution(top_n=10)
for diagnosis, count in diagnoses.items():
    print(f"  {diagnosis}: {count}")

print("\n[3/3] Saving aggregated data files...")
analyser.save_aggregated_data('data/aggregated')

print("\n" + "=" * 70)
print("DEMONSTRATION COMPLETE")
print("=" * 70)
print("\nWhat was created:")
print("✓ Complete statistics with small cell suppression")
print("✓ Monthly admission trends by unit")
print("✓ Unit distribution")
print("✓ Diagnosis distribution")
print("✓ Outcome statistics")
print("✓ Length of stay statistics")
print("✓ Admission sources")
print("✓ Specialty distribution")
print("✓ Discharge destinations")
print("\nFiles created in data/aggregated/:")
print("- complete_statistics.json (all data)")
print("- monthly_admissions.json")
print("- unit_distribution.json")
print("- diagnosis_distribution.json")
print("- outcome_statistics.json")
print("- length_of_stay.json")
print("- admission_sources.json")
print("- specialties.json")
print("- discharge_destinations.json")
print("\nThese files are safe to commit to GitHub and use in dashboard.")
