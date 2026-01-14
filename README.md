# Eastchester Tax & Home Value Analysis Model

A comprehensive mathematical model to analyze and compare property taxes and home values in Eastchester, NY (including villages of Bronxville and Tuckahoe) against comparable Westchester County municipalities.

## Overview

This project answers key questions about real estate value and tax burden:
- What are the taxes paid per square foot in each municipality?
- What is the home value per square foot based on recent sales?
- Which areas offer the best value-for-tax ratio?
- How do the complex tax structures (town/village/school/county) affect total burden?

## Understanding Eastchester's Tax Structure

Eastchester has a uniquely complex structure:

```
┌─────────────────────────────────────────────────────────────┐
│                    TOWN OF EASTCHESTER                       │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│  │    Village of   │  │    Village of   │  │  Unincorporated │
│  │   BRONXVILLE    │  │    TUCKAHOE     │  │   EASTCHESTER   │
│  │   RAR: 100%     │  │   RAR: 0.98%    │  │   RAR: 0.88%    │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘
│         ↓                    ↓                    ↓
│   Bronxville UFSD      Tuckahoe UFSD      Eastchester UFSD
└─────────────────────────────────────────────────────────────┘
```

### Key Concepts

- **RAR (Residential Assessment Ratio)**: The percentage of market value at which properties are assessed
  - Bronxville: 100% (assessed at full market value)
  - Eastchester: 0.88% (assessed at less than 1% of market value!)
  - This doesn't mean lower taxes—tax rates are adjusted accordingly

- **Tax Layers**: Residents pay multiple overlapping taxes:
  - County taxes (Westchester)
  - Town taxes (Eastchester)
  - Village taxes (Bronxville/Tuckahoe only)
  - School district taxes
  - Fire district taxes

## Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Project Structure

```
eastchester/
├── data/
│   ├── raw/                    # Raw collected data
│   │   ├── sales/              # Home sales CSVs
│   │   ├── assessments/        # Property assessment data
│   │   └── tax_rates/          # Municipal tax rate schedules
│   └── processed/              # Cleaned, unified datasets
├── src/
│   ├── config.py               # Municipality definitions, RARs, tax rates
│   ├── models/
│   │   ├── property.py         # Property and sale data models
│   │   ├── tax_calculator.py   # Tax computation engine
│   │   └── metrics.py          # Value/tax metrics calculations
│   ├── data_collection/
│   │   ├── redfin_scraper.py   # Collect recent sales from Redfin
│   │   └── data_loader.py      # Load and unify data sources
│   ├── analysis/
│   │   ├── comparison.py       # Cross-municipality comparison
│   │   └── statistics.py       # Statistical analysis utilities
│   └── visualization/
│       ├── charts.py           # Matplotlib/Seaborn charts
│       └── dashboard.py        # Streamlit dashboard
├── notebooks/
│   ├── 01_data_exploration.ipynb
│   ├── 02_tax_analysis.ipynb
│   └── 03_comparative_report.ipynb
├── requirements.txt
└── README.md
```

## Usage

### 1. Collect Sales Data

```python
from src.data_collection.redfin_scraper import RedfinScraper

scraper = RedfinScraper()
sales = scraper.collect_recent_sales('eastchester', num_sales=50)
sales.to_csv('data/raw/sales/eastchester_sales.csv')
```

### 2. Calculate Tax Metrics

```python
from src.models.tax_calculator import TaxCalculator
from src.config import MUNICIPALITIES

calc = TaxCalculator()
property_tax = calc.calculate_total_tax(
    assessed_value=9000,  # Low due to 0.88% RAR
    municipality='eastchester_unincorp'
)
print(f"Total annual tax: ${property_tax.total:,.2f}")
```

### 3. Run Comparison Analysis

```python
from src.analysis.comparison import ComparisonEngine

engine = ComparisonEngine()
report = engine.generate_full_report()
print(report.summary())
```

### 4. Launch Dashboard

```bash
streamlit run src/visualization/dashboard.py
```

## Key Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| Value/sqft | `sale_price / sqft` | Market value per square foot |
| Tax/sqft | `annual_tax / sqft` | Tax burden per square foot |
| Effective Tax Rate | `annual_tax / market_value * 100` | True tax as % of value |
| Tax Efficiency | `(tax/sqft) / (value/sqft) * 1000` | Tax per $1000 value/sqft |

## Municipalities Analyzed

| Municipality | Type | RAR | School District |
|-------------|------|-----|-----------------|
| Eastchester (unincorp) | Town | 0.88% | Eastchester UFSD |
| Bronxville | Village | 100% | Bronxville UFSD |
| Tuckahoe | Village | 0.98% | Tuckahoe UFSD |
| Scarsdale | Village | 69.73% | Scarsdale UFSD |
| Larchmont | Village | 100% | Mamaroneck UFSD |
| Mamaroneck (Village) | Village | 100% | Mamaroneck UFSD |
| Pelham | Village | ~2.5% | Pelham UFSD |
| Pelham Manor | Village | ~2.5% | Pelham UFSD |

## Data Sources

- **Sales Data**: Redfin, Zillow, local MLS
- **Assessment Data**: Westchester County Tax Viewer
- **Tax Rates**: Municipal websites, annual budgets
- **RAR Values**: NY State ORPTS, retiredassessor.com

## License

MIT License - See LICENSE file for details.


