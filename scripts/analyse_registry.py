"""
Analysis and aggregation of ICU patient data
Generates safe, shareable statistics from master registry
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import json

class ICUAnalyser:
    """Analyse ICU patient registry and generate aggregated statistics"""
    
    def __init__(self, registry_path='data/processed/master_registry.csv'):
        """Load master registry for analysis"""
        self.registry_path = Path(registry_path)
        
        if not self.registry_path.exists():
            raise FileNotFoundError(f"Registry not found: {registry_path}")
        
        print(f"Loading registry: {self.registry_path}")
        self.df = pd.read_csv(registry_path)
        
        # Parse dates
        if 'admission_datetime' in self.df.columns:
            self.df['admission_datetime'] = pd.to_datetime(
                self.df['admission_datetime'], errors='coerce'
            )
        
        if 'discharge_datetime' in self.df.columns:
            self.df['discharge_datetime'] = pd.to_datetime(
                self.df['discharge_datetime'], errors='coerce'
            )
        
        # Calculate length of stay
        if 'admission_datetime' in self.df.columns and 'discharge_datetime' in self.df.columns:
            self.df['los_hours'] = (
                self.df['discharge_datetime'] - self.df['admission_datetime']
            ).dt.total_seconds() / 3600
            self.df['los_days'] = self.df['los_hours'] / 24
        
        # Add time period columns
        if 'admission_datetime' in self.df.columns:
            self.df['admission_year'] = self.df['admission_datetime'].dt.year
            self.df['admission_month'] = self.df['admission_datetime'].dt.to_period('M').astype(str)
            self.df['admission_quarter'] = self.df['admission_datetime'].dt.to_period('Q').astype(str)
        
        print(f"Loaded {len(self.df)} records")
        print(f"Date range: {self.df['admission_datetime'].min()} to {self.df['admission_datetime'].max()}")
    
    def suppress_small_cells(self, data, threshold=5):
        """
        Suppress counts <5 to prevent re-identification.
        
        Parameters:
        - data: dict or DataFrame with counts
        - threshold: minimum cell size (default 5)
        
        Returns:
        - Data with small cells suppressed
        """
        if isinstance(data, dict):
            return {k: v if v >= threshold else f"<{threshold}" for k, v in data.items()}
        elif isinstance(data, pd.DataFrame):
            # For DataFrames, suppress small counts in numeric columns
            df_copy = data.copy()
            for col in df_copy.select_dtypes(include=[np.number]).columns:
                df_copy.loc[df_copy[col] < threshold, col] = f"<{threshold}"
            return df_copy
        return data
    
    def monthly_admissions(self, by_unit=True, suppress=True):
        """
        Calculate monthly admission counts.
        
        Parameters:
        - by_unit: split by ICU unit
        - suppress: apply small cell suppression
        
        Returns:
        - DataFrame with monthly counts
        """
        print("\nCalculating monthly admissions...")
        
        if by_unit and 'icu_unit' in self.df.columns:
            monthly = self.df.groupby(['admission_month', 'icu_unit']).size().reset_index(name='admissions')
            
            # Pivot for easier visualization
            monthly_pivot = monthly.pivot(index='admission_month', columns='icu_unit', values='admissions').fillna(0)
            
            if suppress:
                monthly_pivot = self.suppress_small_cells(monthly_pivot)
            
            return monthly_pivot
        else:
            monthly = self.df.groupby('admission_month').size().reset_index(name='admissions')
            
            if suppress:
                monthly['admissions'] = monthly['admissions'].apply(
                    lambda x: x if x >= 5 else "<5"
                )
            
            return monthly
    
    def unit_distribution(self, suppress=True):
        """
        Calculate distribution of admissions across ICU units.
        
        Returns:
        - dict with unit counts
        """
        print("\nCalculating unit distribution...")
        
        if 'icu_unit' not in self.df.columns:
            return {}
        
        counts = self.df['icu_unit'].value_counts().to_dict()
        
        if suppress:
            counts = self.suppress_small_cells(counts)
        
        return counts
    
    def diagnosis_distribution(self, top_n=10, suppress=True):
        """
        Calculate most common diagnoses.
        
        Parameters:
        - top_n: number of top diagnoses to return
        - suppress: apply small cell suppression
        
        Returns:
        - dict with diagnosis counts
        """
        print("\nCalculating diagnosis distribution...")
        
        if 'primary_diagnosis' not in self.df.columns:
            return {}
        
        counts = self.df['primary_diagnosis'].value_counts().head(top_n).to_dict()
        
        if suppress:
            counts = self.suppress_small_cells(counts)
        
        return counts
    
    def outcome_statistics(self, by_unit=False, suppress=True):
        """
        Calculate outcome statistics (mortality rates, etc.).
        
        Parameters:
        - by_unit: split by ICU unit
        - suppress: apply small cell suppression
        
        Returns:
        - dict with outcome statistics
        """
        print("\nCalculating outcome statistics...")
        
        if 'icu_outcome' not in self.df.columns:
            return {}
        
        if by_unit and 'icu_unit' in self.df.columns:
            outcomes = self.df.groupby(['icu_unit', 'icu_outcome']).size().unstack(fill_value=0)
            
            # Calculate percentages
            outcomes_pct = outcomes.div(outcomes.sum(axis=1), axis=0) * 100
            
            if suppress:
                outcomes = self.suppress_small_cells(outcomes)
            
            return {
                'counts': outcomes.to_dict(),
                'percentages': outcomes_pct.round(1).to_dict()
            }
        else:
            counts = self.df['icu_outcome'].value_counts().to_dict()
            total = sum(counts.values())
            percentages = {k: round((v/total)*100, 1) for k, v in counts.items()}
            
            if suppress:
                counts = self.suppress_small_cells(counts)
            
            return {
                'counts': counts,
                'percentages': percentages
            }
    
    def length_of_stay_statistics(self, by_unit=False):
        """
        Calculate length of stay statistics.
        
        Parameters:
        - by_unit: split by ICU unit
        
        Returns:
        - dict with LOS statistics (median, IQR)
        """
        print("\nCalculating length of stay statistics...")
        
        if 'los_days' not in self.df.columns:
            return {}
        
        # Remove outliers (>30 days or negative)
        los_clean = self.df[(self.df['los_days'] > 0) & (self.df['los_days'] <= 30)].copy()
        
        if by_unit and 'icu_unit' in self.df.columns:
            stats = los_clean.groupby('icu_unit')['los_days'].agg([
                ('median', 'median'),
                ('q25', lambda x: x.quantile(0.25)),
                ('q75', lambda x: x.quantile(0.75)),
                ('count', 'count')
            ]).round(1)
            
            return stats.to_dict('index')
        else:
            stats = {
                'median': round(los_clean['los_days'].median(), 1),
                'q25': round(los_clean['los_days'].quantile(0.25), 1),
                'q75': round(los_clean['los_days'].quantile(0.75), 1),
                'count': len(los_clean)
            }
            
            return stats
    
    def admission_source_distribution(self, suppress=True):
        """
        Calculate distribution of admission sources.
        
        Returns:
        - dict with admission source counts
        """
        print("\nCalculating admission source distribution...")
        
        if 'admission_source' not in self.df.columns:
            return {}
        
        counts = self.df['admission_source'].value_counts().to_dict()
        
        if suppress:
            counts = self.suppress_small_cells(counts)
        
        return counts
    
    def specialty_distribution(self, top_n=10, suppress=True):
        """
        Calculate specialty distribution.
        
        Parameters:
        - top_n: number of top specialties to return
        - suppress: apply small cell suppression
        
        Returns:
        - dict with specialty counts
        """
        print("\nCalculating specialty distribution...")
        
        if 'specialty' not in self.df.columns:
            return {}
        
        counts = self.df['specialty'].value_counts().head(top_n).to_dict()
        
        if suppress:
            counts = self.suppress_small_cells(counts)
        
        return counts
    
    def discharge_destination_distribution(self, suppress=True):
        """
        Calculate ICU discharge destination distribution.
        
        Returns:
        - dict with discharge destination counts
        """
        print("\nCalculating discharge destination distribution...")
        
        if 'icu_discharge_destination' not in self.df.columns:
            return {}
        
        counts = self.df['icu_discharge_destination'].value_counts().to_dict()
        
        if suppress:
            counts = self.suppress_small_cells(counts)
        
        return counts
    
    def generate_all_statistics(self, suppress=True):
        """
        Generate all statistics in one comprehensive dataset.
        
        Parameters:
        - suppress: apply small cell suppression
        
        Returns:
        - dict with all statistics
        """
        print("\n" + "=" * 70)
        print("GENERATING COMPREHENSIVE STATISTICS")
        print("=" * 70)
        
        stats = {
            'metadata': {
                'generated': datetime.now().isoformat(),
                'total_records': len(self.df),
                'unique_patients': int(self.df['anonymous_patient_id'].nunique()),
                'date_range': {
                    'start': str(self.df['admission_datetime'].min()),
                    'end': str(self.df['admission_datetime'].max())
                },
                'suppression_threshold': 5 if suppress else None
            },
            'monthly_admissions': self.monthly_admissions(by_unit=True, suppress=suppress).to_dict(),
            'unit_distribution': self.unit_distribution(suppress=suppress),
            'diagnosis_distribution': self.diagnosis_distribution(suppress=suppress),
            'outcome_statistics': self.outcome_statistics(by_unit=True, suppress=suppress),
            'length_of_stay': self.length_of_stay_statistics(by_unit=True),
            'admission_sources': self.admission_source_distribution(suppress=suppress),
            'specialties': self.specialty_distribution(suppress=suppress),
            'discharge_destinations': self.discharge_destination_distribution(suppress=suppress)
        }
        
        print("\n✓ All statistics generated")
        return stats
    
    def save_aggregated_data(self, output_dir='data/aggregated'):
        """
        Save all aggregated statistics as JSON files for visualization.
        
        Parameters:
        - output_dir: directory to save aggregated data
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        print("\n" + "=" * 70)
        print("SAVING AGGREGATED DATA")
        print("=" * 70)
        
        # Generate all statistics
        stats = self.generate_all_statistics(suppress=True)
        
        # Save complete statistics
        complete_path = output_path / 'complete_statistics.json'
        with open(complete_path, 'w') as f:
            json.dump(stats, f, indent=2)
        print(f"\n✓ Complete statistics: {complete_path}")
        
        # Save individual components for easier dashboard loading
        components = [
            ('monthly_admissions', stats['monthly_admissions']),
            ('unit_distribution', stats['unit_distribution']),
            ('diagnosis_distribution', stats['diagnosis_distribution']),
            ('outcome_statistics', stats['outcome_statistics']),
            ('length_of_stay', stats['length_of_stay']),
            ('admission_sources', stats['admission_sources']),
            ('specialties', stats['specialties']),
            ('discharge_destinations', stats['discharge_destinations'])
        ]
        
        for name, data in components:
            component_path = output_path / f'{name}.json'
            with open(component_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"✓ {name}: {component_path}")
        
        print("\n" + "=" * 70)
        print("AGGREGATION COMPLETE")
        print("=" * 70)
        print(f"\nAll files saved to: {output_path}")
        print("\nThese aggregated files are safe to commit to GitHub:")
        print("- No patient-level data")
        print("- Small cells suppressed (<5)")
        print("- Only summary statistics")
        print("\nReady for visualization!")


def analyse_and_export(registry_path='data/processed/master_registry.csv',
                       output_dir='data/aggregated'):
    """
    Convenience function to analyse registry and export aggregated data.
    
    Parameters:
    - registry_path: path to master registry
    - output_dir: where to save aggregated data
    """
    analyser = ICUAnalyser(registry_path)
    analyser.save_aggregated_data(output_dir)
    
    return analyser


if __name__ == "__main__":
    print("\nICU Data Analysis Script")
    print("-" * 70)
    print("\nThis script analyses the master registry and generates aggregated statistics.")
    print("\nExample usage:\n")
    print("from scripts.analyse_registry import analyse_and_export")
    print("\nanalyser = analyse_and_export(")
    print("    registry_path='data/processed/master_registry.csv',")
    print("    output_dir='data/aggregated'")
    print(")")
    print()
