# Quick Start Guide

## Step 1: Get ID Link File from IT

**CRITICAL FIRST STEP**

Request CSV with both identifiers:
```csv
hospital_number,nhs_number
H1234567,NHS9876543210
```

Save as: `data/raw/master/id_link_file.csv`

---

## Step 2: Process Your First File
```bash
cd ~/Desktop/icu-analysis
source venv/bin/activate

# Process master registry
python scripts/master/process_master_registry.py data/raw/master/january.xlsx hospital_number
```

**What happens:**
- ✅ Loads ID link file
- ✅ Removes any names automatically
- ✅ Converts postcodes to areas (e.g., BS2 8HW → BS2)
- ✅ Converts DOB to age at admission
- ✅ Creates anonymous IDs
- ✅ Checks for duplicates
- ✅ Saves to `data/processed/master_registry.csv`

---

## Step 3: Check It Worked
```bash
# View first 20 lines
head -20 data/processed/master_registry.csv

# Check how many records
wc -l data/processed/master_registry.csv

# Check anonymisation worked
cat data/processed/id_mapping.json
```

---

## Step 4: Run Your First Audit
```bash
# Example: Ventilation audit
python scripts/audits/ventilation/ventilation_audit.py data/raw/audits/ventilation/jan_vent.xlsx hospital_number
```

---

## Common Commands

### Process Monthly Update
```bash
python scripts/master/process_master_registry.py data/raw/master/february.xlsx hospital_number
```

### Run Specific Audit
```bash
python scripts/audits/[audit_name]/[audit_name]_audit.py data/raw/audits/[audit_name]/file.xlsx
```

### Check for Duplicates (Dry Run)
```bash
python scripts/check_for_duplicates.py data/raw/master/file.xlsx
```

### View Duplicate Report
```bash
cat reports/duplicates_*.csv
```

---

## Troubleshooting

**Error: "ID link file not found"**
- Get file from IT
- Save at: `data/raw/master/id_link_file.csv`

**Error: "Column 'hospital_number' not found"**
- Check your file has this column
- Or use 'nhs_number' if that's what you have

**Warning: "Found duplicate records"**
- Normal if reprocessing same file
- Check report in `reports/` folder
- Duplicates automatically skipped (safe)

---

## Monthly Workflow
```bash
# 1. Update ID links (if changed)
cp new_links.csv data/raw/master/id_link_file.csv

# 2. Process master index
python scripts/master/process_master_registry.py data/raw/master/february.xlsx

# 3. Run audits
python scripts/audits/ventilation/ventilation_audit.py data/raw/audits/ventilation/feb.xlsx
python scripts/audits/renal/renal_audit.py data/raw/audits/renal/feb.xlsx

# 4. Done!
```

---

## What Gets Protected Automatically

✅ **Patient names** - removed  
✅ **Addresses** - removed  
✅ **Phone/email** - removed  
✅ **Full postcodes** - converted to area only  
✅ **Date of birth** - converted to age  
✅ **Hospital/NHS numbers** - converted to anonymous IDs  
✅ **Duplicates** - automatically detected and skipped  

---

## What To Check

After processing, always check:

1. **No names in output:**
```bash
   head -50 data/processed/master_registry.csv
   # Should see: ICU-000001, not real names
```

2. **Postcodes are areas only:**
```bash
   # Should see: BS2, not BS2 8HW
```

3. **Ages not DOBs:**
```bash
   # Should see: age_at_admission: 67
   # Should NOT see: dob: 1957-03-15
```

4. **No duplicates added:**
```bash
   # Check reports folder
   ls reports/
```

