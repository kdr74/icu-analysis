"""
Generate human-readable summary report from aggregated data
"""

import json
from pathlib import Path
from datetime import datetime

def generate_markdown_report(aggregated_dir='data/aggregated', 
                            output_file='docs/analysis_summary.md'):
    """
    Generate a markdown summary report from aggregated data.
    
    Parameters:
    - aggregated_dir: directory with JSON files
    - output_file: where to save markdown report
    """
    
    agg_path = Path(aggregated_dir)
    stats_file = agg_path / 'complete_statistics.json'
    
    if not stats_file.exists():
        raise FileNotFoundError(f"Statistics file not found: {stats_file}")
    
    with open(stats_file, 'r') as f:
        stats = json.load(f)
    
    # Build markdown report
    report = []
    report.append("# ICU Analysis Summary Report\n")
    report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
    report.append("---\n")
    
    # Metadata
    meta = stats['metadata']
    report.append("## Dataset Overview\n")
    report.append(f"- **Total Records:** {meta['total_records']}")
    report.append(f"- **Unique Patients:** {meta['unique_patients']}")
    report.append(f"- **Date Range:** {meta['date_range']['start'][:10]} to {meta['date_range']['end'][:10]}")
    if meta.get('suppression_threshold'):
        report.append(f"- **Note:** Counts <{meta['suppression_threshold']} are suppressed for confidentiality")
    report.append("\n---\n")
    
    # Unit Distribution
    report.append("## ICU Unit Distribution\n")
    unit_dist = stats['unit_distribution']
    for unit, count in unit_dist.items():
        report.append(f"- **{unit}:** {count} admissions")
    report.append("\n---\n")
    
    # Outcomes
    report.append("## Outcome Statistics\n")
    outcomes = stats['outcome_statistics']
    if 'percentages' in outcomes:
        for unit, outcome_pcts in outcomes['percentages'].items():
            report.append(f"\n### {unit}")
            for outcome, pct in outcome_pcts.items():
                report.append(f"- {outcome}: {pct}%")
    report.append("\n---\n")
    
    # Length of Stay
    report.append("## Length of Stay (days)\n")
    los = stats['length_of_stay']
    report.append("\n| Unit | Median | IQR | Count |")
    report.append("|------|--------|-----|-------|")
    for unit, los_stats in los.items():
        iqr = f"{los_stats['q25']} - {los_stats['q75']}"
        report.append(f"| {unit} | {los_stats['median']} | {iqr} | {los_stats['count']} |")
    report.append("\n---\n")
    
    # Top Diagnoses
    report.append("## Top Diagnoses\n")
    diagnoses = stats['diagnosis_distribution']
    for i, (diagnosis, count) in enumerate(list(diagnoses.items())[:10], 1):
        report.append(f"{i}. **{diagnosis}:** {count}")
    report.append("\n---\n")
    
    # Admission Sources
    report.append("## Admission Sources\n")
    sources = stats['admission_sources']
    for source, count in sources.items():
        report.append(f"- **{source}:** {count}")
    report.append("\n---\n")
    
    # Specialties
    report.append("## Top Specialties\n")
    specialties = stats['specialties']
    for specialty, count in specialties.items():
        report.append(f"- **{specialty}:** {count}")
    report.append("\n")
    
    # Write report
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        f.write('\n'.join(report))
    
    print(f"✓ Summary report generated: {output_path}")
    
    return output_path


if __name__ == "__main__":
    generate_markdown_report()
    print("\nView report at: docs/analysis_summary.md")
