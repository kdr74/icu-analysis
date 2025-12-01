# ICU Data Analysis

Anonymised analysis of ICU admission data across three units:
- **General ICU (A600)**
- **Cardiac ICU (C604)**
- **Weston ICU (WICU)**

## 🔗 Live Dashboard

**[View Interactive Dashboard](https://YOUR_GITHUB_USERNAME.github.io/icu-analysis/)**

Replace `YOUR_GITHUB_USERNAME` with your GitHub username.

## 📊 Features

- Patient data anonymisation with cryptographic hashing
- Multi-source data processing and merging
- Comprehensive statistical analysis
- Interactive browser-based visualisations
- Automatic small cell suppression (<5) for confidentiality

## 🔒 Data Security

- All patient identifiers anonymised before analysis
- Raw data never committed to repository
- Only aggregated statistics published
- Compliant with data protection requirements

## 🛠️ Technical Stack

- **Python 3.12** for data processing
- **pandas** for data manipulation
- **Plotly** for interactive visualisations
- **GitHub Pages** for hosting
- **Git** for version control

## 📁 Repository Structure
```
icu-analysis/
├── data/
│   ├── raw/              # Raw data (never committed)
│   ├── processed/        # Anonymised registry (never committed)
│   └── aggregated/       # Safe statistics (committed)
├── scripts/
│   ├── anonymise_patients.py      # Patient anonymisation
│   ├── process_patient_data.py    # Data processing pipeline
│   ├── validate_registry.py       # Data quality validation
│   ├── analyse_registry.py        # Statistical analysis
│   └── test_all_systems.py        # Comprehensive testing
├── docs/
│   ├── index.html                 # Dashboard
│   └── dashboard.js               # Visualisation code
└── README.md
```

## 🚀 Usage

### Processing New Data
```python
from scripts.process_patient_data import ICUDataProcessor

# Create processor
processor = ICUDataProcessor()

# Process data file
processor.process_file(
    filepath='data/raw/your_data.xlsx',
    identifier_column='hospital_number',
    date_columns={'admission_datetime': 'datetime'}
)

# Save master registry
processor.save_master_registry()
```

### Generating Statistics
```python
from scripts.analyse_registry import analyse_and_export

# Analyse and export aggregated data
analyser = analyse_and_export(
    registry_path='data/processed/master_registry.csv',
    output_dir='data/aggregated'
)
```

### Updating Dashboard
```bash
# Commit new aggregated data
git add data/aggregated/*.json
git commit -m "Update statistics"
git push

# Dashboard updates automatically
```

## 📋 Requirements

- Python 3.10+
- pandas
- numpy
- openpyxl
- plotly
- jupyter (optional)

Install with:
```bash
pip install -r requirements.txt
```

## 🧪 Testing

Run comprehensive system test:
```bash
python scripts/test_all_systems.py
```

Test dashboard deployment:
```bash
python scripts/test_dashboard.py
```

## 📖 Documentation

- [Dashboard Documentation](docs/README.md)
- [Analysis Summary](docs/analysis_summary.md)

## 🔄 Workflow

1. Place raw data in `data/raw/`
2. Run processing scripts to anonymise and merge data
3. Validate data quality
4. Generate aggregated statistics
5. Commit aggregated data to GitHub
6. Dashboard updates automatically

## ⚠️ Important Notes

- Never commit files in `data/raw/` or `data/processed/`
- Always check `.gitignore` is properly configured
- Verify small cell suppression before publishing
- Keep `hashing_salt.txt` secure and never commit

## 📝 License

This project is for internal use. All patient data remains confidential.

## 👤 Author

[Your Name/Organisation]

Last updated: [Date]
