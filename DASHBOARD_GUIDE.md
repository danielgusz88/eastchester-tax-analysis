# 🎨 Dashboard & Visualization Guide

## ✅ What's Been Created

### 1. **Enhanced Streamlit Dashboard** (`src/visualization/dashboard.py`)
A fully-featured interactive web dashboard with:

#### 🗺️ **Map View Tab** (NEW!)
- Interactive map of Westchester County
- Municipalities shown as circles
- **Size** = Home value per sqft
- **Color** = Tax burden per sqft
- Hover for detailed metrics
- Zoom and pan controls

#### 📊 **Comparison Tab**
- Value vs Tax scatter plot
- Side-by-side bar charts
- Automatic insights generation
- Interactive Plotly charts

#### 🧮 **Calculator Tab**
- Tax calculator with sliders
- Compare taxes across municipalities
- Tax component breakdown (School, County, Town, etc.)
- Monthly payment estimates

#### ⚡ **Efficiency Tab**
- Tax efficiency rankings
- Best/worst value analysis
- Visual efficiency comparison

#### 📋 **Data Tab**
- Full metrics table
- Export to CSV, JSON, or text report
- Downloadable data

### 2. **Map Visualization Module** (`src/visualization/map_view.py`)
- Reusable map components
- Multiple map types (value, tax, combined)
- Geographic coordinate data

### 3. **Launch Script** (`launch_dashboard.sh`)
- One-command dashboard launch
- Automatic dependency checking

## 🚀 How to Use

### Quick Start:
```bash
# Option 1: Use launch script
./launch_dashboard.sh

# Option 2: Direct command
streamlit run src/visualization/dashboard.py
```

### What You'll See:

1. **Header** with key metrics:
   - Number of municipalities compared
   - Average value/sqft
   - Average tax/sqft
   - Average effective tax rate

2. **Sidebar Controls**:
   - Select municipalities to compare
   - Adjust home value ($300K - $5M)
   - Adjust square footage (500 - 6,000 sqft)

3. **Five Main Tabs**:
   - **Map**: Geographic visualization
   - **Comparison**: Charts and insights
   - **Calculator**: Tax calculations
   - **Efficiency**: Value analysis
   - **Data**: Full data table and exports

## 📊 Key Visualizations

### Map View
- **Interactive OpenStreetMap** with municipality markers
- **Size encoding**: Larger circles = higher home values
- **Color encoding**: Redder = higher taxes
- **Hover tooltips**: Detailed metrics on hover

### Comparison Charts
- **Scatter Plot**: Value vs Tax relationship
- **Bar Charts**: Rankings by value and tax
- **All interactive**: Zoom, pan, hover for details

### Tax Calculator
- **Dynamic calculations**: Updates as you adjust sliders
- **Component breakdown**: See where your tax dollars go
- **Comparison table**: Side-by-side municipality comparison

## 💡 Tips for Best Experience

1. **Start with Map View**: Get geographic context
2. **Use Calculator**: Enter your actual home value to see real comparisons
3. **Compare 3-5 municipalities**: Too many makes charts cluttered
4. **Export data**: Download CSV for your own analysis
5. **Check insights**: Automatic analysis highlights key findings

## 🔄 Data Flow

```
Real Sales Data (CSV) 
    ↓
DataLoader.load_all_sales()
    ↓
ComparisonEngine.generate_full_report()
    ↓
Dashboard displays metrics, charts, maps
```

If no real data:
```
Sample Data Generator
    ↓
Same flow as above
```

## 🎨 Customization

### Change Colors:
Edit `src/visualization/charts.py` → `COLORS` dictionary

### Add Municipalities:
1. Add to `src/config.py` → `MUNICIPALITIES`
2. Add coordinates to `src/visualization/map_view.py` → `MUNICIPALITY_COORDS`
3. Restart dashboard

### Modify Charts:
Edit functions in `src/visualization/dashboard.py`:
- `render_comparison_charts()` - Main comparison charts
- `render_map_view()` - Map visualization
- `render_tax_calculator()` - Calculator section

## 📱 Mobile Experience

The dashboard is responsive and works on:
- ✅ Desktop (best experience)
- ✅ Tablets
- ✅ Mobile phones (some features may be smaller)

## 🚀 Deployment Options

### Local Network Sharing:
```bash
streamlit run src/visualization/dashboard.py --server.address 0.0.0.0
```
Others can access via: `http://[your-ip]:8501`

### Streamlit Cloud (Free):
1. Push to GitHub
2. Connect to https://streamlit.io/cloud
3. Deploy automatically

### Docker:
```dockerfile
FROM python:3.11
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["streamlit", "run", "src/visualization/dashboard.py"]
```

## 📊 Export Options

From the Data tab, export:
- **CSV**: For Excel/Google Sheets analysis
- **JSON**: For programmatic use
- **Text Report**: Human-readable summary

## 🐛 Troubleshooting

### Dashboard won't start:
```bash
pip3 install streamlit plotly pandas numpy
```

### Map not showing:
- Requires internet (uses OpenStreetMap)
- Check firewall settings

### No data:
- Run `python3 run_data_collection.py` to generate sample data
- Or add real CSV files to `data/raw/sales/`

### Charts not interactive:
- Make sure Plotly is installed: `pip install plotly`

## 📈 Next Steps

1. **Add Real Data**: Collect actual sales from Redfin
2. **Customize**: Adjust colors, add municipalities
3. **Share**: Deploy to Streamlit Cloud or share locally
4. **Extend**: Add time series, more filters, etc.

## 🎉 You're Ready!

The dashboard is fully functional and ready to use. Just run:
```bash
./launch_dashboard.sh
```

Or:
```bash
streamlit run src/visualization/dashboard.py
```

Enjoy exploring your data! 🏠📊
