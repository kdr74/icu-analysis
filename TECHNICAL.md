# Technical Documentation

Detailed technical specifications for the ICU Analysis Dashboard system.

## Data Processing Workflows

### 1. Master Registry Processing

#### Rolling Summary Processing
**Script**: `scripts/master/process_rolling_summary.py`

**Input**: `data/raw/master/Rolling_Summary.csv`

**Process**:
1. Load CSV file
2. Standardize column names (snake_case)
3. Map hospital numbers to anonymous IDs
4. Sanitize patient names
5. Convert postcodes to area codes
6. Detect duplicates
7. Categorize discharge destinations
8. Save to master registry

**Output**: Adds/updates records in `data/processed/master_registry.csv`

**Duplicate Handling**: 
- Match key: `anonymous_patient_id + ICU_admit_date`
- Action: Skip duplicate, log count

#### GICU Discharge Processing
**Script**: `scripts/master/process_gicu_discharges.py`

**Key Feature**: Calculates age from DOB

**Age Calculation**:
```python
def calculate_age_at_admission(dob, admit_date):
    """
    Calculate patient age at ICU admission
    
    Handles multiple date formats:
    - DD/MM/YYYY
    - YYYY-MM-DD  
    - DD-MM-YYYY
    
    Validates: 0 ≤ age < 150
    """
    age = admit_year - birth_year
    if (admit_month, admit_day) < (birth_month, birth_day):
        age -= 1
    return age if 0 <= age < 150 else None
```

**DOB Handling**:
- DOB used to calculate age
- Age stored in `age_at_admission` column
- DOB **removed** from processed files (confidentiality)

### 2. Data Merging

#### Merge Additional Data
**Script**: `scripts/master/merge_additional_data.py`

**Purpose**: Update existing registry records with additional fields from GICU files

**Logic**:
```python
for each registry record:
    find matching GICU record (same patient + date)
    if match found:
        for each field in GICU:
            if registry field is NULL and GICU has value:
                update registry field
```

**Fields Updated** (35 columns):
- Admission details (time, type, source, reason)
- Surgery information
- Discharge details (destination, delays, readiness)
- Length of stay metrics
- Mortality tracking
- Age at admission

**Results**: 69,318 data points updated across 8,402 records

#### Force Update Ages
**Script**: `scripts/master/force_update_ages.py`

**Purpose**: FORCE update ages for all matching records, even if age already exists

**Difference from Merge**:
- Merge: Only updates if registry field is NULL
- Force Update: Updates ALL matching records regardless

**Results**: Updated 5,299 records with age (19.8% coverage)

### 3. Dashboard Data Generation

**Script**: `scripts/generate_enhanced_dashboard_data.py`

**Input**: `data/processed/master_registry.csv`

**Process**:
1. Load master registry
2. Categorize ages into groups
3. Categorize discharge destinations
4. Calculate statistics (mean, median, SD, quartiles)
5. Apply small cell suppression (n≥5)
6. Export to JSON

**Output Structure**:
```json
{
  "metadata": {
    "generated_at": "2024-12-22T10:30:00",
    "total_records": 26728,
    "date_range": {"min": "2015-12", "max": "2025-01"}
  },
  "records": [
    {
      "year_month": "2024-01",
      "icu_ward": "General ICU A600",
      "specialty": "General Surgery",
      "patient_classification": "Emergency",
      "discharge_category": "Home",
      "icu_death": "No",
      "los": 2,
      "age_group": "50-60",
      "age": 55,
      "admit_type": "Unplanned",
      "readmission": false,
      "nature_of_surgery": "Emergency Laparotomy"
    }
  ],
  "filter_options": {
    "units": ["General ICU A600", "Cardiac ICU C604", "Weston WICU"],
    "specialties": ["Cardiology", "General Surgery", ...],
    "patient_classifications": ["Emergency", "Elective", ...],
    "age_groups": ["<16", "16-18", "18-30", ..., "90+"]
  },
  "statistics": {
    "los_overall": {"mean": 4.2, "median": 2, "std": 5.1, ...},
    "age_overall": {"mean": 58.7, "median": 61.0, ...},
    "los_by_outcome": {
      "survived": {"mean": 3.8, ...},
      "died": {"mean": 6.2, ...}
    },
    "los_by_age_group": {
      "50-60": {"mean": 4.1, "median": 2, ...}
    },
    "mortality_by_age_group": {
      "50-60": {"rate": 12.3, "n": 1076, "deaths": 132}
    }
  }
}
```

## Anonymization System

### EnhancedPatientAnonymiser Class

**Location**: `scripts/shared/enhanced_anonymiser.py`

**Core Functions**:

#### 1. ID Link Management
```python
def load_id_links(self, filepath):
    """
    Load hospital_number <-> nhs_number mappings
    
    Creates bidirectional lookup:
    - hosp_to_nhs: hospital_number → nhs_number
    - nhs_to_hosp: nhs_number → hospital_number
    """
```

#### 2. Anonymous ID Generation
```python
def get_anonymous_id(self, hospital_number):
    """
    Generate consistent anonymous patient ID
    
    Process:
    1. Lookup NHS number from hospital number
    2. Hash NHS number using SHA-256
    3. Take first 16 chars of hex digest
    4. Cache result for consistency
    
    Returns: (anonymous_id, patient_id_hash)
    """
    nhs_number = self.hosp_to_nhs[hospital_number]
    hash_full = hashlib.sha256(nhs_number.encode()).hexdigest()
    anonymous_id = f"ANON_{hash_full[:16].upper()}"
    patient_id_hash = hash_full
    return anonymous_id, patient_id_hash
```

**Properties**:
- **Deterministic**: Same NHS number always produces same ID
- **One-way**: Cannot reverse anonymous ID to NHS number
- **Unique**: SHA-256 ensures no collisions
- **Consistent**: Same ID across all files for same patient

#### 3. Data Sanitization
```python
def sanitize_data(self, df):
    """
    Remove/transform sensitive data
    
    Operations:
    - Remove patient_name column
    - Convert full postcode to area code
    - Validate anonymous IDs present
    """
    df = df.drop(columns=['patient_name'], errors='ignore')
    df['postcode_area'] = df['postcode'].str.extract(r'^([A-Z]{1,2}\d{1,2})')
    df = df.drop(columns=['postcode'], errors='ignore')
    return df
```

#### 4. Duplicate Detection
```python
def detect_duplicates(self, new_records, existing_records):
    """
    Identify duplicate admissions
    
    Match key: anonymous_patient_id + ICU_admit_date
    
    Returns:
    - new_count: Number of unique new records
    - duplicate_count: Number of duplicates skipped
    - combined_df: Existing + new (no duplicates)
    """
    new_records['match_key'] = (
        new_records['anonymous_patient_id'].astype(str) + 
        '_' + 
        new_records['ICU_admit_date'].astype(str)
    )
```

### Privacy Protections

#### Small Cell Suppression
```python
def apply_small_cell_suppression(data, min_count=5):
    """
    Hide statistics for groups with <5 patients
    
    Example: Mortality rates only shown if n≥5
    """
    if len(data) < min_count:
        return None
    return calculate_statistic(data)
```

#### Postcode Anonymization
```
Full Postcode → Area Code
BS1 1AA → BS1
BS16 2QQ → BS16
BA1 5TH → BA1
```

Preserves geographic analysis while protecting privacy.

## Dashboard Architecture

### Frontend Stack
- **HTML5**: Structure
- **CSS3**: Styling with gradients, shadows, responsive grid
- **JavaScript (ES6)**: Application logic
- **Plotly.js 2.27.0**: Interactive charts

### Data Flow
```
User Interaction (Filter Change)
    ↓
applyFilters()
    ↓
Filter allData based on selections
    ↓
Update filteredData
    ↓
updateDashboard()
    ↓
Recalculate statistics
    ↓
Redraw all charts with Plotly
```

### Multi-Select Filter Implementation

**CustomSelect Class**:
```javascript
class CustomSelect {
    constructor(id, options, onChange) {
        // Creates dropdown with checkboxes
        // "Select All" functionality
        // Real-time filtering
    }
    
    updateSelected() {
        // Updates selected items array
        // Updates button text ("All X" or "N selected")
        // Triggers onChange callback → applyFilters()
    }
}
```

**Filter Logic**:
```javascript
function applyFilters() {
    const units = customSelects.Unit.getSelected();  // Array of selected units
    
    filteredData = allData.filter(record => {
        // If filter has selections AND record doesn't match → exclude
        if (units.length && !units.includes(record.icu_ward))
            return false;
        
        // Repeat for all filters...
        
        return true;  // Include if passes all filters
    });
    
    updateDashboard();  // Redraw with filtered data
}
```

### Chart Generation

**Box Plot Example**:
```javascript
Plotly.newPlot('chartDiv', [{
    type: 'box',
    y: losValues,
    marker: { color: '#f59e0b' },
    boxmean: 'sd',  // Show mean and standard deviation
    name: 'LOS'
}], {
    margin: { t: 20, b: 40, l: 60, r: 20 },
    yaxis: { title: 'Days in ICU' },
    showlegend: false,
    height: 320
}, {
    displayModeBar: false  // Hide Plotly controls
});
```

**Bar Chart with Text Labels**:
```javascript
Plotly.newPlot('chartDiv', [{
    type: 'bar',
    x: labels,
    y: values,
    marker: { color: '#3b82f6' },
    text: values.map(v => v.toLocaleString()),  // "1,234"
    textposition: 'outside'
}], layoutConfig, displayConfig);
```

### Custom Analysis Builder

**Workflow**:
1. User selects metric (count, mortality, avg LOS, etc.)
2. User selects grouping dimension (unit, specialty, age, etc.)
3. User selects chart type (bar, line, box)
4. User optionally adds filters
5. Click "Generate Chart"

**Implementation**:
```javascript
function generateCustomChart() {
    // 1. Apply custom filters to allData
    let customData = allData.filter(/* custom filters */);
    
    // 2. Group data by selected dimension
    const grouped = {};
    customData.forEach(record => {
        const key = record[groupByField];
        if (!grouped[key]) grouped[key] = [];
        grouped[key].push(record);
    });
    
    // 3. Calculate selected metric for each group
    const results = {};
    Object.entries(grouped).forEach(([key, records]) => {
        results[key] = calculateMetric(records, selectedMetric);
    });
    
    // 4. Render chart
    Plotly.newPlot('customChart', [trace], layout, config);
}
```

## Performance Considerations

### Data Size
- **Master Registry**: 26,728 records × 51 columns = ~1.36M cells
- **Dashboard JSON**: ~8MB uncompressed
- **Browser Memory**: ~15-20MB for full dataset in JavaScript

### Optimization Strategies

1. **JSON Structure**: Array of objects (not object of arrays) for better JavaScript access
2. **Filtering**: Client-side filtering fast enough for <100k records
3. **Chart Rendering**: Plotly handles large datasets efficiently
4. **Lazy Loading**: Could implement if dataset grows >100k records

### Browser Compatibility
- **Chrome**: Full support, best performance
- **Firefox**: Full support
- **Safari**: Full support (cache clearing recommended)
- **Edge**: Full support
- **Mobile**: Responsive design works on tablets/phones

## File Format Specifications

### CSV Files
- **Encoding**: UTF-8
- **Delimiter**: Comma
- **Quote Character**: Double quote
- **Date Format**: DD/MM/YYYY
- **Time Format**: HH:MM (24-hour)
- **Boolean**: "Yes"/"No" or "True"/"False"

### Excel Files
- **Format**: .xlsx (not .xls)
- **Sheets**: Single sheet or first sheet used
- **Headers**: Row 1
- **Date Format**: Excel date serial number or DD/MM/YYYY

### JSON Output
- **Encoding**: UTF-8
- **Format**: Pretty-printed (2-space indent)
- **Numbers**: Integers as int, decimals as float
- **Dates**: String in YYYY-MM-DD format
- **Nulls**: null (not "None" or empty string)

## Error Handling

### File Processing
```python
try:
    df = pd.read_csv(filepath)
except FileNotFoundError:
    print(f"❌ File not found: {filepath}")
    sys.exit(1)
except pd.errors.EmptyDataError:
    print(f"❌ File is empty: {filepath}")
    sys.exit(1)
```

### Age Calculation
```python
def calculate_age(dob, admit_date):
    try:
        # Parse dates with multiple format attempts
        # Calculate age
        # Validate range (0-150)
        return age if 0 <= age < 150 else None
    except:
        return None  # Graceful failure, log for review
```

### Dashboard
```javascript
fetch('./data/aggregated/master/dashboard_data.json')
    .then(r => r.ok ? r.json() : Promise.reject('Failed to load'))
    .then(data => {
        // Process data
    })
    .catch(error => {
        // Show user-friendly error message
        document.querySelector('.container').innerHTML += 
            '<div class="error">Error loading data</div>';
    });
```

## Testing Recommendations

### Unit Tests
- [ ] Anonymizer ID consistency
- [ ] Age calculation edge cases
- [ ] Duplicate detection accuracy
- [ ] Data sanitization completeness

### Integration Tests
- [ ] End-to-end file processing
- [ ] Dashboard data generation
- [ ] Multi-file merge logic

### Data Quality Checks
- [ ] Age range validation (0-150)
- [ ] Date consistency (admit < discharge)
- [ ] LOS calculation accuracy
- [ ] Missing value patterns

### Browser Testing
- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Safari (latest)
- [ ] Mobile responsiveness

## Deployment

### GitHub Pages Setup
1. Repository settings → Pages
2. Source: main branch, /docs folder
3. Custom domain: (optional)
4. Enforce HTTPS: Enabled

### Update Process
```bash
# 1. Process new data
python scripts/master/process_new_file.py

# 2. Regenerate dashboard data
python scripts/generate_enhanced_dashboard_data.py

# 3. Copy to docs
cp data/aggregated/master/dashboard_data.json docs/data/aggregated/master/

# 4. Commit and push
git add docs/data/
git commit -m "Update dashboard data"
git push origin main

# GitHub Pages auto-deploys in 1-2 minutes
```

### Local Development
```bash
# Start server
python -m http.server 8000

# Open browser
open http://localhost:8000/docs/
```

## Security Considerations

### Data at Rest
- **Raw files**: Never committed to Git (in .gitignore)
- **Processed files**: Never committed to Git
- **Aggregated data**: Only anonymized statistics in Git

### Data in Transit
- **GitHub Pages**: HTTPS enforced
- **Local development**: HTTP acceptable (localhost only)

### Access Control
- **Repository**: Private (authorized users only)
- **Dashboard**: Public (contains only anonymized aggregate data)

### Audit Trail
- Git commits track all code changes
- Processing scripts log file operations
- Dashboard tracks generation timestamps

## Maintenance

### Regular Tasks
- **Weekly**: Check for new data files
- **Monthly**: Review data quality metrics
- **Quarterly**: Update documentation
- **Annually**: Review anonymization strategy

### Monitoring
- **Data completeness**: Track % records with age, specialty, etc.
- **Processing errors**: Log and review failed records
- **Dashboard performance**: Monitor load times
- **User feedback**: Collect improvement suggestions

---

**Document Version**: 1.0  
**Last Updated**: December 2024
