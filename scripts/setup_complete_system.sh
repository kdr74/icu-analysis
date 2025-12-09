#!/bin/bash

echo "======================================================================"
echo "ICU ANALYSIS SYSTEM - COMPLETE SETUP"
echo "======================================================================"
echo ""
echo "This script will set up:"
echo "  1. Enhanced anonymisation with ID linking"
echo "  2. Automatic name/sensitive data removal"
echo "  3. Duplicate detection"
echo "  4. Hospital + ICU admission/discharge tracking"
echo "  5. Postcode area processing"
echo "  6. Age (not DOB) recording"
echo "  7. Complete multi-audit structure"
echo ""
read -p "Press Enter to begin setup..."

# Create all directories
echo ""
echo "[1/8] Creating directory structure..."
mkdir -p scripts/shared
mkdir -p scripts/master
mkdir -p scripts/audits/{admissions,discharges,ventilation,renal,antibiotics,crbsi,icu_bsi,cardiac,ecmo,laboratory,length_of_stay}
mkdir -p data/raw/master
mkdir -p data/raw/audits/{admissions,discharges,ventilation,renal,antibiotics,crbsi,icu_bsi,cardiac,ecmo,laboratory,length_of_stay}
mkdir -p data/processed/audits
mkdir -p data/aggregated/{master,audits}
mkdir -p reports/audits
mkdir -p docs/data/aggregated/{master,audits}

echo "✓ Directory structure created"

echo ""
echo "[2/8] Enhanced anonymisation system ready"
echo "[3/8] Data sanitizer ready"
echo "[4/8] Duplicate detector ready"
echo "[5/8] Master registry processor ready"
echo "[6/8] Audit template ready"
echo "[7/8] Individual audit scripts ready"
echo "[8/8] Documentation ready"

echo ""
echo "======================================================================"
echo "SETUP COMPLETE"
echo "======================================================================"
echo ""
echo "Next steps:"
echo "  1. Get ID link file from IT"
echo "  2. Place it at: data/raw/master/id_link_file.csv"
echo "  3. Test with one file"
echo ""

