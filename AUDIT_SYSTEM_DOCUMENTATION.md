# ICU Analysis System - Complete Documentation

## System Overview

Complete ICU data analysis system with:
- **Master patient index** (anonymised, with hospital + ICU admission/discharge times)
- **Multiple specialized audits** (ventilation, renal, antibiotics, infections, cardiac, ECMO, etc.)
- **Automatic data sanitization** (removes names, converts postcodes, DOB to age)
- **Duplicate detection** (prevents accidental double-counting)
- **ID linking** (hospital number ↔ NHS number automatically matched)

---

## Critical First Step: ID Link File

**YOU MUST GET THIS FILE FROM IT BEFORE PROCESSING ANY DATA**

### Request from IT

Ask for a CSV file with both hospital numbers and NHS numbers:
```csv
hospital_number,nhs_number
H1234567,NHS9876543210
H2345678,NHS8765432109
H3456789,NHS7654321098
```

### Save Location

**Must be saved at:** `data/raw/master/id_link_file.csv`

### Why This Is Critical

Without this file:
- Same patient with hospital number in one file = ICU-000001
- Same patient with NHS number in another file = ICU-000002
- **Result:** One patient counted twice ❌

With this file:
- Same patient with hospital number = ICU-000001
- Same patient with NHS number = ICU-000001
- **Result:** Correctly identified as same patient ✓

### Update Monthly

Request updated file from IT each month to keep links current.

---

## Directory Structure
```
icu-analysis/
├── data/
│   ├── raw/
│   │   ├── master/
│   │   │   └── id_link_file.csv          ← **CRITICAL FILE**
│   │   └── audits/
│   │       ├── admissions/
│   │       ├── ventilation/
│   │       ├── renal/
│   │       └── [... 8 more audit folders]
│   ├── processed/
│   │   ├── master_registry.csv           ← Core patient database
│   │   ├── id_mapping.json               ← Anonymous ID mappings
│   │   └── audits/                       ← Processed audit files
│   └── aggregated/
│       ├── master/                        ← Master statistics
│       └── audits/                        ← Audit statistics
├── scripts/
│   ├── shared/                            ← Core utilities
│   │   ├── enhanced_anonymiser.py        ← ID anonymisation + linking
│   │   ├── data_sanitizer.py             ← Remove names/sensitive data
│   │   └── duplicate_detector.py         ← Find duplicates
│   ├── master/
│   │   └── process_master_registry.py    ← Process master index
│   └── audits/
│       ├── audit_template.py              ← Base template
│       ├── admissions/
│       ├── ventilation/
│       └── [... 9 more audit folders]
└── reports/
    └── audits/                            ← Duplicate reports
```

---

## Data Protection Features

### Automatic Sanitization

**Removes automatically:**
- ✅ Patient names (any column with 'name', 'surname', etc.)
- ✅ Full addresses
- ✅ Phone numbers, emails
- ✅ Date of birth (converted to age at admission)
- ✅ Full postcodes (keeps first part only, e.g., BS2 8HW → BS2)

**Keeps:**
- ✅ Age at admission
- ✅ Postcode area (first part)
- ✅ Hospital admission/discharge datetime
- ✅ ICU admission/discharge datetime

### Duplicate Detection

**Automatically prevents:**
- ✅ Same file processed twice
- ✅ Accidental data inflation
- ✅ Double-counting patients

**Generates reports:**
- Shows which records are duplicates
- Saved in `reports/` folder
- Review before proceeding

---

## Processing Workflows

### 1. First Time Setup

**Step 1: Get ID link file**
```bash
# Request from IT, save as:
data/raw/master/id_link_file.csv
```

**Step 2: Process your first master file**
```bash
python scripts/master/process_master_registry.py data/raw/master/january.xlsx hospital_number
```

**Step 3: Check it worked**
```bash
# View processed data
head -20 data/processed/master_registry.csv

# Should see columns like:
# anonymous_patient_id, icu_admission_datetime, age_at_admission, postcode_area, etc.
```

### 2. Monthly Master Registry Update
```bash
# Process new month
python scripts/master/process_master_registry.py data/raw/master/february.xlsx hospital_number

# System will:
# - Check ID link file automatically
# - Remove any names
# - Convert postcode to area
# - Convert DOB to age
# - Check for duplicates
# - Add to existing registry
```

### 3. Run Individual Audit
```bash
# Example: Ventilation audit
python scripts/audits/ventilation/ventilation_audit.py data/raw/audits/ventilation/jan_vent.xlsx hospital_number

# Example: Renal audit
python scripts/audits/renal/renal_audit.py data/raw/audits/renal/jan_rrt.xlsx hospital_number
```

### 4. Handling Duplicates

**Default behavior (recommended):**
```bash
# Automatically skips duplicates
python scripts/master/process_master_registry.py data/raw/master/file.xlsx hospital_number skip
```

**If duplicates found:**
- System prints warning
- Generates report in `reports/` folder
- Skips duplicate records (default)
- Master registry unchanged

**Other options:**
```bash
# Include duplicates with warning
python scripts/master/process_master_registry.py file.xlsx hospital_number warn

# Replace old data with new (for corrections)
python scripts/master/process_master_registry.py file.xlsx hospital_number overwrite
```

---

## Master Registry Columns

| Column | Description | Example |
|--------|-------------|---------|
| anonymous_patient_id | Unique anonymous ID | ICU-000001 |
| hospital_admission_datetime | Hospital admission | 2024-01-15 08:30:00 |
| hospital_discharge_datetime | Hospital discharge | 2024-01-20 14:00:00 |
| icu_admission_datetime | ICU admission | 2024-01-15 10:45:00 |
| icu_discharge_datetime | ICU discharge | 2024-01-18 16:30:00 |
| age_at_admission | Age when admitted | 67 |
| postcode_area | Postcode first part only | BS2 |
| icu_unit | Which ICU | A600, C604, WICU |
| admission_source | Where from | ED, Theatre, Ward |
| primary_diagnosis | Main diagnosis | Sepsis |
| icu_outcome | ICU outcome | Survived, Died |

---

## Available Audits

| Audit | Purpose | Example Metrics |
|-------|---------|-----------------|
| admissions | Admission patterns | Source, type, time to ICU |
| discharges | Discharge patterns | Destination, readmissions |
| ventilation | Ventilation + VAP | Days ventilated, VAP rate |
| renal | RRT usage | RRT days, complications |
| antibiotics | Antibiotic use | Type, duration, de-escalation |
| crbsi | Central line infections | Line days, CRBSI rate |
| icu_bsi | ICU bloodstream infections | BSI rate, organisms |
| cardiac | OHCA outcomes | ROSC, neurological outcome |
| ecmo | ECMO usage | ECMO days, survival |
| laboratory | Blood test usage | Tests per day, transfusions |
| length_of_stay | LOS by groups | LOS by diagnosis, age, etc. |

---

## Troubleshooting

### Issue: Same patient appears with different IDs

**Cause:** ID link file missing or not loaded

**Solution:**
1. Check file exists: `ls data/raw/master/id_link_file.csv`
2. Check format (must have `hospital_number` and `nhs_number` columns)
3. Reprocess data

### Issue: Names still in data

**Cause:** Column name not recognized as forbidden

**Solution:**
1. Check what columns were loaded
2. Add column name to FORBIDDEN_COLUMNS in `scripts/shared/data_sanitizer.py`
3. Reprocess

### Issue: Duplicates being added

**Cause:** Duplicate action set to 'warn' instead of 'skip'

**Solution:**
```bash
# Use skip mode (default)
python scripts/master/process_master_registry.py file.xlsx hospital_number skip
```

### Issue: Age not calculated

**Cause:** No admission date in file, or DOB column not recognized

**Solution:**
- Ensure file has admission_datetime column
- Ensure DOB column named 'dob', 'date_of_birth', or 'birth_date'

---

## Monthly Workflow
```bash
# 1. Update ID link file (request from IT)
cp new_id_links.csv data/raw/master/id_link_file.csv

# 2. Process master index
python scripts/master/process_master_registry.py data/raw/master/february.xlsx hospital_number

# 3. Process each audit you're running this month
python scripts/audits/ventilation/ventilation_audit.py data/raw/audits/ventilation/feb_vent.xlsx
python scripts/audits/renal/renal_audit.py data/raw/audits/renal/feb_rrt.xlsx

# 4. Check for any issues
ls reports/  # Check if duplicate reports generated

# 5. Update dashboards (when ready)
# Copy aggregated data to docs folder
# Commit and push to GitHub
```

---

## Data Security

**Never commit to GitHub:**
- ❌ `data/raw/` - contains identifiable data
- ❌ `data/processed/master_registry.csv` - patient-level data
- ❌ `data/processed/id_mapping.json` - ID mappings
- ❌ `hashing_salt.txt` - encryption key
- ❌ `data/raw/master/id_link_file.csv` - identifier links

**Safe to commit:**
- ✅ `data/aggregated/` - summary statistics only
- ✅ All scripts
- ✅ Documentation

**Your .gitignore already protects all sensitive files.**

---

## Customizing Audits

Each audit script is in `scripts/audits/[audit_name]/[audit_name]_audit.py`

To customize statistics:

1. Open audit script
2. Find `generate_statistics()` method
3. Add your calculations
4. Save and rerun

**Example:**
```python
def generate_statistics(self):
    stats = {...}
    
    # Add custom calculation
    if 'your_column' in merged.columns:
        stats['your_metric'] = merged['your_column'].mean()
    
    return stats
```

---

## Getting Help

1. Check this documentation
2. Review script comments (all scripts are commented)
3. Check reports folder for duplicate/error reports
4. Regenerate from raw data if needed

---

## System Design Principles

✅ **Flexible** - Can restructure anytime, raw data preserved  
✅ **Safe** - Automatic data protection, multiple safety checks  
✅ **Recoverable** - Can always regenerate from raw data  
✅ **Documented** - Comments in all scripts, comprehensive docs  
✅ **Modular** - Each audit independent, easy to add/modify  

