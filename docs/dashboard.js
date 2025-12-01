// ICU Dashboard JavaScript
// Loads aggregated data and creates interactive visualisations

// Configuration
const DATA_PATH = './'; // Relative path to data files
let allData = {};
let currentFilters = {
    unit: 'all',
    timePeriod: 'all'
};

// Colour scheme
const COLORS = {
    'A600': '#667eea',
    'C604': '#f093fb',
    'WICU': '#4facfe',
    'Survived': '#48bb78',
    'Died': '#f56565'
};

// Load all data files
async function loadData() {
    try {
        const response = await fetch(`${DATA_PATH}../data/aggregated/complete_statistics.json`);
        if (!response.ok) throw new Error('Failed to load data');
        allData = await response.json();
        
        // Update metadata
        updateMetadata();
        
        // Create all charts
        createMonthlyAdmissionsChart();
        createUnitDistributionChart();
        createOutcomeChart();
        createDiagnosisChart();
        createLOSChart();
        createAdmissionSourcesChart();
        createSpecialtiesChart();
        
        // Setup filter listeners
        setupFilters();
        
    } catch (error) {
        console.error('Error loading data:', error);
        document.querySelector('.container').innerHTML = 
            '<div class="error">Error loading data. Please ensure data files are present in data/aggregated/</div>';
    }
}

// Update metadata display
function updateMetadata() {
    const meta = allData.metadata;
    
    document.getElementById('total-records').textContent = meta.total_records.toLocaleString();
    document.getElementById('unique-patients').textContent = meta.unique_patients.toLocaleString();
    
    const startDate = new Date(meta.date_range.start).toLocaleDateString('en-GB');
    const endDate = new Date(meta.date_range.end).toLocaleDateString('en-GB');
    document.getElementById('date-range').textContent = `${startDate} – ${endDate}`;
    
    document.getElementById('last-updated').textContent = 
        new Date(meta.generated).toLocaleDateString('en-GB', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit'
        });
}

// Monthly Admissions Chart
function createMonthlyAdmissionsChart() {
    const data = allData.monthly_admissions;
    
    // Get all months
    const months = Object.keys(data);
    
    // Get all units
    const units = ['A600', 'C604', 'WICU'];
    
    // Create traces for each unit
    const traces = units.map(unit => {
        const values = months.map(month => {
            const value = data[month][unit];
            // Handle suppressed values
            return (typeof value === 'string' && value.startsWith('<')) ? null : value;
        });
        
        return {
            x: months,
            y: values,
            name: unit,
            type: 'scatter',
            mode: 'lines+markers',
            marker: { color: COLORS[unit], size: 8 },
            line: { color: COLORS[unit], width: 3 }
        };
    });
    
    const layout = {
        xaxis: {
            title: 'Month',
            tickangle: -45
        },
        yaxis: {
            title: 'Number of Admissions'
        },
        hovermode: 'closest',
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: { t: 20, b: 80 }
    };
    
    Plotly.newPlot('monthly-admissions-chart', traces, layout, {responsive: true});
}

// Unit Distribution Chart
function createUnitDistributionChart() {
    const data = allData.unit_distribution;
    
    const units = Object.keys(data);
    const values = Object.values(data).map(v => 
        (typeof v === 'string' && v.startsWith('<')) ? 0 : v
    );
    const colors = units.map(unit => COLORS[unit]);
    
    const trace = {
        labels: units,
        values: values,
        type: 'pie',
        marker: { colors: colors },
        textinfo: 'label+percent',
        hovertemplate: '<b>%{label}</b><br>Admissions: %{value}<br>%{percent}<extra></extra>'
    };
    
    const layout = {
        showlegend: true,
        margin: { t: 20, b: 20 }
    };
    
    Plotly.newPlot('unit-distribution-chart', [trace], layout, {responsive: true});
}

// Outcome Statistics Chart
function createOutcomeChart() {
    const data = allData.outcome_statistics;
    
    if (!data.percentages) return;
    
    const units = Object.keys(data.percentages);
    const outcomes = ['Survived', 'Died'];
    
    const traces = outcomes.map(outcome => {
        const values = units.map(unit => data.percentages[unit][outcome] || 0);
        
        return {
            x: units,
            y: values,
            name: outcome,
            type: 'bar',
            marker: { color: COLORS[outcome] },
            text: values.map(v => `${v}%`),
            textposition: 'auto'
        };
    });
    
    const layout = {
        barmode: 'stack',
        xaxis: { title: 'ICU Unit' },
        yaxis: { 
            title: 'Percentage (%)',
            range: [0, 100]
        },
        showlegend: true,
        legend: {
            orientation: 'h',
            y: -0.2
        },
        margin: { t: 20, b: 60 }
    };
    
    Plotly.newPlot('outcome-chart', traces, layout, {responsive: true});
}

// Diagnosis Distribution Chart
function createDiagnosisChart() {
    const data = allData.diagnosis_distribution;
    
    // Filter out suppressed values and sort
    const diagnoses = Object.entries(data)
        .filter(([_, count]) => !(typeof count === 'string' && count.startsWith('<')))
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    const trace = {
        x: diagnoses.map(d => d[1]),
        y: diagnoses.map(d => d[0]),
        type: 'bar',
        orientation: 'h',
        marker: { 
            color: '#667eea',
            opacity: 0.8
        },
        text: diagnoses.map(d => d[1]),
        textposition: 'auto'
    };
    
    const layout = {
        xaxis: { title: 'Number of Cases' },
        yaxis: { 
            automargin: true,
            tickfont: { size: 11 }
        },
        margin: { l: 150, t: 20, b: 60 }
    };
    
    Plotly.newPlot('diagnosis-chart', [trace], layout, {responsive: true});
}

// Length of Stay Chart
function createLOSChart() {
    const data = allData.length_of_stay;
    
    const units = Object.keys(data);
    const medians = units.map(unit => data[unit].median);
    const q25 = units.map(unit => data[unit].q25);
    const q75 = units.map(unit => data[unit].q75);
    
    // Calculate error bars (distance from median to quartiles)
    const errors_y_minus = medians.map((med, i) => med - q25[i]);
    const errors_y_plus = medians.map((med, i) => q75[i] - med);
    
    const trace = {
        x: units,
        y: medians,
        type: 'bar',
        marker: { 
            color: units.map(unit => COLORS[unit]),
            opacity: 0.8
        },
        error_y: {
            type: 'data',
            symmetric: false,
            array: errors_y_plus,
            arrayminus: errors_y_minus,
            color: '#555'
        },
        text: medians.map(m => `${m} days`),
        textposition: 'auto'
    };
    
    const layout = {
        xaxis: { title: 'ICU Unit' },
        yaxis: { title: 'Days (Median with IQR)' },
        showlegend: false,
        margin: { t: 20, b: 60 }
    };
    
    Plotly.newPlot('los-chart', [trace], layout, {responsive: true});
}

// Admission Sources Chart
function createAdmissionSourcesChart() {
    const data = allData.admission_sources;
    
    const sources = Object.keys(data);
    const values = Object.values(data).map(v => 
        (typeof v === 'string' && v.startsWith('<')) ? 0 : v
    );
    
    const trace = {
        labels: sources,
        values: values,
        type: 'pie',
        marker: { 
            colors: ['#667eea', '#764ba2', '#f093fb', '#4facfe', '#43e97b']
        },
        textinfo: 'label+percent',
        hovertemplate: '<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>'
    };
    
    const layout = {
        showlegend: true,
        margin: { t: 20, b: 20 }
    };
    
    Plotly.newPlot('admission-sources-chart', [trace], layout, {responsive: true});
}

// Specialties Chart
function createSpecialtiesChart() {
    const data = allData.specialties;
    
    // Filter and sort
    const specialties = Object.entries(data)
        .filter(([_, count]) => !(typeof count === 'string' && count.startsWith('<')))
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    const trace = {
        x: specialties.map(s => s[1]),
        y: specialties.map(s => s[0]),
        type: 'bar',
        orientation: 'h',
        marker: { 
            color: '#764ba2',
            opacity: 0.8
        },
        text: specialties.map(s => s[1]),
        textposition: 'auto'
    };
    
    const layout = {
        xaxis: { title: 'Number of Cases' },
        yaxis: { 
            automargin: true,
            tickfont: { size: 11 }
        },
        margin: { l: 120, t: 20, b: 60 }
    };
    
    Plotly.newPlot('specialties-chart', [trace], layout, {responsive: true});
}

// Setup filter listeners
function setupFilters() {
    document.getElementById('unit-filter').addEventListener('change', (e) => {
        currentFilters.unit = e.target.value;
        applyFilters();
    });
    
    document.getElementById('time-period').addEventListener('change', (e) => {
        currentFilters.timePeriod = e.target.value;
        applyFilters();
    });
}

// Apply filters (simplified - full implementation would filter data before charting)
function applyFilters() {
    // For now, show alert that filtering is applied
    // Full implementation would re-filter the data and recreate charts
    console.log('Filters applied:', currentFilters);
    
    // Note: A full implementation would:
    // 1. Filter the monthly admissions data by time period
    // 2. Filter all data by unit if specific unit selected
    // 3. Recreate all charts with filtered data
    // This would require more complex data processing
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', loadData);
