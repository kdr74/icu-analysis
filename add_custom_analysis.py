with open('docs/index.html', 'r') as f:
    content = f.read()

# Find where to insert (before </div> of container, after charts-grid closing div)
insertion_point = content.rfind('</div>\n\n    <script>')

custom_section = '''
        <div style="margin-top: 40px;">
            <div class="filters-section">
                <div class="filters-title">🔬 Custom Analysis Builder</div>
                <p style="color: var(--slate-600); margin-bottom: 20px; font-size: 14px;">
                    Build your own analysis - e.g., "Cardiology deaths by month" or "HPB mean LOS: survived vs died"
                </p>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin-bottom: 20px;">
                    <div class="filter-group">
                        <label class="filter-label">What to Measure</label>
                        <select id="customMetric" style="padding: 10px 12px; border: 1px solid var(--slate-300); border-radius: 8px; font-size: 14px;">
                            <option value="count">Number of Admissions</option>
                            <option value="mortality">Mortality Rate (%)</option>
                            <option value="avg_los">Average Length of Stay</option>
                            <option value="median_los">Median Length of Stay</option>
                            <option value="total_los">Total Patient Days</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label class="filter-label">Group By</label>
                        <select id="customGroupBy" style="padding: 10px 12px; border: 1px solid var(--slate-300); border-radius: 8px; font-size: 14px;">
                            <option value="icu_ward">ICU Unit</option>
                            <option value="specialty">Specialty</option>
                            <option value="patient_classification">Admission Type</option>
                            <option value="year_month">Month</option>
                            <option value="icu_death">Outcome (Survived/Died)</option>
                            <option value="discharge_category">Discharge Destination</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label class="filter-label">Chart Type</label>
                        <select id="customChartType" style="padding: 10px 12px; border: 1px solid var(--slate-300); border-radius: 8px; font-size: 14px;">
                            <option value="bar">Bar Chart</option>
                            <option value="line">Line Chart</option>
                            <option value="pie">Pie Chart</option>
                        </select>
                    </div>
                    
                    <div class="filter-group" style="align-self: flex-end;">
                        <button onclick="generateCustomChart()" style="padding: 10px 24px; background: linear-gradient(135deg, rgb(37, 99, 235), rgb(59, 130, 246)); color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 14px; font-weight: 600; box-shadow: 0 2px 4px rgba(0,0,0,0.1); transition: all 0.2s;">
                            Generate Chart
                        </button>
                    </div>
                </div>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div class="filter-group">
                        <label class="filter-label">Filter: ICU Unit</label>
                        <select id="customFilterUnit" style="padding: 10px 12px; border: 1px solid var(--slate-300); border-radius: 8px; font-size: 14px;">
                            <option value="">All Units</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label class="filter-label">Filter: Specialty</label>
                        <select id="customFilterSpecialty" style="padding: 10px 12px; border: 1px solid var(--slate-300); border-radius: 8px; font-size: 14px;">
                            <option value="">All Specialties</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label class="filter-label">Filter: Outcome</label>
                        <select id="customFilterOutcome" style="padding: 10px 12px; border: 1px solid var(--slate-300); border-radius: 8px; font-size: 14px;">
                            <option value="">All Outcomes</option>
                            <option value="No">Survived Only</option>
                            <option value="Yes">Died Only</option>
                        </select>
                    </div>
                    
                    <div class="filter-group">
                        <label class="filter-label">Filter: Admission Type</label>
                        <select id="customFilterAdmType" style="padding: 10px 12px; border: 1px solid var(--slate-300); border-radius: 8px; font-size: 14px;">
                            <option value="">All Types</option>
                        </select>
                    </div>
                </div>
            </div>
            
            <div class="chart-container" id="customChartContainer" style="display: none; margin-top: 24px;">
                <div class="chart-title" id="customChartTitle">Custom Analysis</div>
                <div id="customChart"></div>
            </div>
        </div>
'''

# Insert the custom section
new_content = content[:insertion_point] + custom_section + '\n' + content[insertion_point:]

# Now add the JavaScript functions before the closing </script> tag
js_insertion = new_content.rfind('</script>')

custom_js = '''
        // Custom Analysis Functions
        function populateCustomFilters() {
            if (!allData || allData.length === 0) return;
            
            const units = [...new Set(allData.map(r => r.icu_ward))].sort();
            const specialties = [...new Set(allData.map(r => r.specialty))].sort();
            const admTypes = [...new Set(allData.map(r => r.patient_classification))].sort();
            
            const unitSelect = document.getElementById('customFilterUnit');
            units.forEach(u => {
                const opt = document.createElement('option');
                opt.value = u;
                opt.textContent = u;
                unitSelect.appendChild(opt);
            });
            
            const specSelect = document.getElementById('customFilterSpecialty');
            specialties.forEach(s => {
                const opt = document.createElement('option');
                opt.value = s;
                opt.textContent = s;
                specSelect.appendChild(opt);
            });
            
            const admTypeSelect = document.getElementById('customFilterAdmType');
            admTypes.forEach(a => {
                const opt = document.createElement('option');
                opt.value = a;
                opt.textContent = a;
                admTypeSelect.appendChild(opt);
            });
        }
        
        function generateCustomChart() {
            const metric = document.getElementById('customMetric').value;
            const groupBy = document.getElementById('customGroupBy').value;
            const chartType = document.getElementById('customChartType').value;
            
            const filterUnit = document.getElementById('customFilterUnit').value;
            const filterSpec = document.getElementById('customFilterSpecialty').value;
            const filterOutcome = document.getElementById('customFilterOutcome').value;
            const filterAdmType = document.getElementById('customFilterAdmType').value;
            
            let customData = allData.filter(record => {
                if (filterUnit && record.icu_ward !== filterUnit) return false;
                if (filterSpec && record.specialty !== filterSpec) return false;
                if (filterOutcome && record.icu_death !== filterOutcome) return false;
                if (filterAdmType && record.patient_classification !== filterAdmType) return false;
                return true;
            });
            
            if (customData.length === 0) {
                alert('No data matches your filters. Try adjusting your selection.');
                return;
            }
            
            const grouped = {};
            customData.forEach(record => {
                const key = record[groupBy];
                if (!grouped[key]) grouped[key] = [];
                grouped[key].push(record);
            });
            
            const results = {};
            Object.entries(grouped).forEach(([key, records]) => {
                switch(metric) {
                    case 'count':
                        results[key] = records.length;
                        break;
                    case 'mortality':
                        const deaths = records.filter(r => r.icu_death === 'Yes').length;
                        results[key] = (deaths / records.length * 100).toFixed(2);
                        break;
                    case 'avg_los':
                        const avgLos = records.reduce((sum, r) => sum + r.los, 0) / records.length;
                        results[key] = avgLos.toFixed(1);
                        break;
                    case 'median_los':
                        const sorted = records.map(r => r.los).sort((a, b) => a - b);
                        const mid = Math.floor(sorted.length / 2);
                        results[key] = sorted.length % 2 ? sorted[mid] : ((sorted[mid - 1] + sorted[mid]) / 2).toFixed(1);
                        break;
                    case 'total_los':
                        results[key] = records.reduce((sum, r) => sum + r.los, 0);
                        break;
                }
            });
            
            let sortedResults;
            if (groupBy === 'year_month') {
                sortedResults = Object.entries(results).sort((a, b) => a[0].localeCompare(b[0]));
            } else if (metric === 'count' || metric === 'total_los') {
                sortedResults = Object.entries(results).sort((a, b) => b[1] - a[1]).slice(0, 15);
            } else {
                sortedResults = Object.entries(results).sort((a, b) => a[0].localeCompare(b[0]));
            }
            
            createCustomChart(sortedResults, metric, groupBy, chartType, customData.length);
        }
        
        function createCustomChart(data, metric, groupBy, chartType, totalRecords) {
            const container = document.getElementById('customChartContainer');
            const titleEl = document.getElementById('customChartTitle');
            
            const metricNames = {
                'count': 'Number of Admissions',
                'mortality': 'Mortality Rate (%)',
                'avg_los': 'Average Length of Stay (days)',
                'median_los': 'Median Length of Stay (days)',
                'total_los': 'Total Patient Days'
            };
            
            const groupNames = {
                'icu_ward': 'ICU Unit',
                'specialty': 'Specialty',
                'patient_classification': 'Admission Type',
                'year_month': 'Month',
                'icu_death': 'Outcome',
                'discharge_category': 'Discharge Destination'
            };
            
            titleEl.textContent = `${metricNames[metric]} by ${groupNames[groupBy]} (n=${totalRecords})`;
            container.style.display = 'block';
            
            const labels = data.map(d => d[0]);
            const values = data.map(d => parseFloat(d[1]));
            
            const plotConfig = { responsive: true, displayModeBar: false };
            const plotLayout = { 
                plot_bgcolor: 'white',
                paper_bgcolor: 'white',
                font: { family: 'Inter, sans-serif', color: 'rgb(15, 23, 42)' }
            };
            
            let trace, layout;
            
            if (chartType === 'bar') {
                const isHorizontal = labels.length > 8 || labels.some(l => l.length > 15);
                
                trace = {
                    type: 'bar',
                    [isHorizontal ? 'y' : 'x']: labels,
                    [isHorizontal ? 'x' : 'y']: values,
                    [isHorizontal ? 'orientation' : '']: isHorizontal ? 'h' : undefined,
                    marker: { color: 'rgb(59, 130, 246)', line: { width: 0 } },
                    text: values.map(v => typeof v === 'number' ? v.toLocaleString() : v),
                    textposition: 'outside'
                };
                
                layout = {
                    ...plotLayout,
                    margin: isHorizontal ? { t: 10, b: 40, l: 150, r: 60 } : { t: 10, b: 100, l: 60, r: 20 },
                    xaxis: { gridcolor: 'rgb(241, 245, 249)', title: isHorizontal ? metricNames[metric] : '' },
                    yaxis: { gridcolor: 'rgb(241, 245, 249)', title: isHorizontal ? '' : metricNames[metric] },
                    height: isHorizontal ? Math.max(400, labels.length * 30) : 400
                };
                
            } else if (chartType === 'line') {
                trace = {
                    type: 'scatter',
                    mode: 'lines+markers',
                    x: labels,
                    y: values,
                    line: { color: 'rgb(59, 130, 246)', width: 3, shape: 'spline' },
                    marker: { color: 'rgb(59, 130, 246)', size: 8, line: { color: 'white', width: 2 } },
                    fill: 'tozeroy',
                    fillcolor: 'rgba(59, 130, 246, 0.1)'
                };
                
                layout = {
                    ...plotLayout,
                    margin: { t: 10, b: 80, l: 60, r: 20 },
                    xaxis: { gridcolor: 'rgb(241, 245, 249)' },
                    yaxis: { title: metricNames[metric], gridcolor: 'rgb(241, 245, 249)' },
                    height: 400
                };
                
            } else if (chartType === 'pie') {
                trace = {
                    type: 'pie',
                    labels: labels,
                    values: values,
                    marker: { colors: colors.specialties, line: { color: 'white', width: 2 } },
                    textinfo: 'label+percent'
                };
                
                layout = {
                    ...plotLayout,
                    margin: { t: 10, b: 10, l: 10, r: 10 },
                    height: 400,
                    showlegend: true
                };
            }
            
            Plotly.newPlot('customChart', [trace], layout, plotConfig);
            container.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
        }
        
'''

# Insert custom JS before closing script tag, and add call to populateCustomFilters
new_content = new_content.replace(
    'populateFilters(data.filter_options);',
    'populateFilters(data.filter_options);\n                populateCustomFilters();'
)

new_content = new_content[:js_insertion] + custom_js + '\n        ' + new_content[js_insertion:]

with open('docs/index.html', 'w') as f:
    f.write(new_content)

print("✓ Custom Analysis section added!")
