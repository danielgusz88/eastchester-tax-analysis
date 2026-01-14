# 🏠 Eastchester Tax Analysis Dashboard

Interactive web dashboard for exploring and comparing property taxes and home values across Westchester County municipalities.

## 🚀 Quick Start

### Option 1: Using the Launch Script (Easiest)
```bash
./launch_dashboard.sh
```

### Option 2: Manual Launch
```bash
streamlit run src/visualization/dashboard.py
```

The dashboard will open in your browser at `http://localhost:8501`

## 📊 Features

### 🗺️ Map View Tab
- Interactive map showing all municipalities
- Circle size = Home value per sqft
- Circle color = Tax burden per sqft
- Hover for detailed metrics
- Zoom and pan controls

### 📊 Comparison Tab
- **Value vs Tax Scatter Plot**: See the relationship between home values and taxes
- **Value Ranking Bar Chart**: Compare home values across municipalities
- **Tax Ranking Bar Chart**: Compare tax burdens
- **Key Insights**: Automatic analysis and findings

### 🧮 Calculator Tab
- **Tax Calculator**: Enter home value and square footage to compare taxes
- **Tax Component Breakdown**: See how taxes are split (School, County, Town, Village, etc.)
- **Monthly Payment Estimates**: See monthly tax costs

### ⚡ Efficiency Tab
- **Tax Efficiency Ranking**: Which municipalities offer best value for tax dollar
- **Efficiency Ratio**: Lower = better value
- **Best/Worst Analysis**: Highlights most and least efficient areas

### 📋 Data Tab
- **Full Data Table**: Complete metrics for all municipalities
- **Export Options**: Download as CSV, JSON, or text report

## 🎛️ Controls

### Sidebar Options:
- **Municipality Selection**: Choose which areas to compare
- **Home Value Slider**: Set home value for tax calculations ($300K - $5M)
- **Square Footage Slider**: Set home size (500 - 6,000 sqft)

## 📁 Data Sources

The dashboard automatically:
1. **Tries to load real data** from `data/raw/sales/*.csv`
2. **Falls back to unified dataset** from `data/processed/unified_sales.parquet`
3. **Uses sample data** if no real data is available

### Adding Real Data:
1. Collect sales data from Redfin/Zillow
2. Fill in templates from `data/raw/sales/templates/`
3. Save as `[municipality]_sales.csv` in `data/raw/sales/`
4. Restart dashboard to see real data

## 📊 Key Metrics Explained

- **Value/sqft**: Median home sale price per square foot
- **Tax/sqft**: Annual property tax per square foot
- **Effective Rate**: Tax as percentage of home value
- **Tax Efficiency Ratio**: Tax dollars per $1,000 of value/sqft (lower is better)
- **Sample Size**: Number of sales analyzed

## 🎨 Visualizations

All charts are interactive:
- **Hover** for detailed information
- **Zoom** with mouse wheel
- **Pan** by clicking and dragging
- **Click legends** to show/hide series

## 💾 Export Options

From the Data tab, you can export:
- **CSV**: For Excel/Google Sheets
- **JSON**: For programmatic use
- **Text Report**: Human-readable summary

## 🔧 Troubleshooting

### Dashboard won't start:
```bash
pip3 install streamlit plotly pandas numpy
```

### No data showing:
- Check that sales CSV files exist in `data/raw/sales/`
- Or run `python3 run_data_collection.py` to generate sample data

### Map not loading:
- Map uses OpenStreetMap (requires internet)
- Check your internet connection

## 📱 Mobile Friendly

The dashboard is responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones

## 🚀 Sharing

To share your dashboard:
1. **Local Network**: Others on your network can access via `http://[your-ip]:8501`
2. **Streamlit Cloud**: Deploy to https://streamlit.io/cloud (free tier available)
3. **Export Reports**: Download and share CSV/JSON files

## 📝 Notes

- Tax rates are from 2024-2025 fiscal year
- RAR values from NY State ORPTS
- Sales data should be from last 3-6 months for best accuracy
- All calculations are estimates - verify with municipal sources for official figures

## 🆘 Support

For issues or questions:
1. Check the Jupyter notebooks in `notebooks/` for detailed analysis
2. Review the code in `src/visualization/dashboard.py`
3. See `README.md` for full project documentation
