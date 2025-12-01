# ICU Analysis Dashboard

Interactive visualisation of ICU admission data across three units:
- General ICU (A600)
- Cardiac ICU (C604)
- Weston ICU (WICU)

## Access

**Live Dashboard:** [View Dashboard](https://yourusername.github.io/icu-analysis/)

Replace `yourusername` with your GitHub username.

## Features

- **Monthly Admissions:** Track admission trends over time by unit
- **Unit Distribution:** Overall distribution of admissions across units
- **Outcome Statistics:** Survival rates by unit
- **Diagnosis Distribution:** Most common diagnoses
- **Length of Stay:** Median and interquartile range by unit
- **Admission Sources:** Where patients are admitted from
- **Specialty Distribution:** Most common responsible specialties

## Data Security

- All patient identifiers anonymised
- Small cell counts (<5) suppressed for confidentiality
- Only aggregated statistics displayed
- No patient-level data accessible

## Technical Details

- Built with Plotly.js for interactive visualisations
- Loads data from JSON files in `data/aggregated/`
- Fully client-side (no server required)
- Works on desktop and mobile browsers

## Data Updates

To update the dashboard with new data:

1. Process new data files through the anonymisation pipeline
2. Run analysis script to generate aggregated statistics
3. Commit updated JSON files to GitHub
4. Dashboard updates automatically

Last updated: [Date from metadata]
