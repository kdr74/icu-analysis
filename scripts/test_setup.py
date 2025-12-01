import pandas as pd
import numpy as np
import plotly.express as px

print("Testing ICU Analysis Setup...")
print("-" * 50)

np.random.seed(42)
dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
units = ['A600', 'C604', 'WICU']

data = []
for date in dates:
    for unit in units:
        admissions = np.random.randint(1, 5)
        data.append({
            'date': date,
            'unit': unit,
            'admissions': admissions
        })

df = pd.DataFrame(data)
print(f"Sample data created: {len(df)} rows")

monthly = df.groupby([pd.Grouper(key='date', freq='M'), 'unit'])['admissions'].sum().reset_index()
monthly['month'] = monthly['date'].dt.strftime('%Y-%m')

fig = px.line(monthly, x='month', y='admissions', color='unit',
              title='ICU Admissions by Unit (Test Data)',
              markers=True)

fig.write_html('docs/test_chart.html')

print("\n" + "=" * 50)
print("SUCCESS: Setup complete!")
print("=" * 50)
print("\nTest chart: docs/test_chart.html")
