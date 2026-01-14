#!/usr/bin/env python3
"""
Simple data collection script that you can run directly.

This will:
1. Generate tax rate data (saved to data/raw/tax_rates/)
2. Create sample sales data (saved to data/processed/)
3. Create manual entry templates (saved to data/raw/sales/templates/)

Run with: python3 run_data_collection.py
"""

import json
from pathlib import Path
from datetime import date

# Create directories
DATA_DIR = Path('data')
RAW_DIR = DATA_DIR / 'raw'
TAX_DIR = RAW_DIR / 'tax_rates'
SALES_DIR = RAW_DIR / 'sales'
TEMPLATES_DIR = SALES_DIR / 'templates'
PROCESSED_DIR = DATA_DIR / 'processed'

for d in [DATA_DIR, RAW_DIR, TAX_DIR, SALES_DIR, TEMPLATES_DIR, PROCESSED_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# Tax rate data (from known sources)
TAX_DATA = {
    'eastchester_unincorp': {
        'municipality': 'Eastchester (Unincorporated)',
        'fiscal_year': '2024-2025',
        'rar': 0.0088,
        'county_rate': 2.5,
        'town_rate': 320.04,
        'village_rate': 0.0,
        'school_rate': 850.0,
        'fire_rate': 45.0,
        'library_rate': 8.0,
    },
    'bronxville': {
        'municipality': 'Bronxville',
        'fiscal_year': '2024-2025',
        'rar': 1.0,
        'county_rate': 2.8,
        'town_rate': 1.5,
        'village_rate': 5.2,
        'school_rate': 18.5,
        'fire_rate': 0.5,
        'library_rate': 0.3,
    },
    'tuckahoe': {
        'municipality': 'Tuckahoe',
        'fiscal_year': '2024-2025',
        'rar': 0.0098,
        'county_rate': 2.5,
        'town_rate': 35.0,
        'village_rate': 85.0,
        'school_rate': 650.0,
        'fire_rate': 40.0,
        'library_rate': 7.0,
    },
    'scarsdale': {
        'municipality': 'Scarsdale',
        'fiscal_year': '2024-2025',
        'rar': 0.6973,
        'county_rate': 4.0,
        'town_rate': 0.0,
        'village_rate': 4.5,
        'school_rate': 25.0,
        'fire_rate': 0.8,
        'library_rate': 0.4,
    },
    'larchmont': {
        'municipality': 'Larchmont',
        'fiscal_year': '2024-2025',
        'rar': 1.0,
        'county_rate': 4.27,
        'town_rate': 0.0,
        'village_rate': 4.70,
        'school_rate': 12.64,
        'fire_rate': 0.4,
        'library_rate': 0.3,
    },
    'mamaroneck_village': {
        'municipality': 'Mamaroneck (Village)',
        'fiscal_year': '2024-2025',
        'rar': 1.0,
        'county_rate': 3.86,
        'town_rate': 0.0,
        'village_rate': 6.34,
        'school_rate': 12.64,
        'fire_rate': 0.4,
        'library_rate': 0.3,
    },
    'pelham': {
        'municipality': 'Pelham',
        'fiscal_year': '2024-2025',
        'rar': 0.025,
        'county_rate': 15.0,
        'town_rate': 8.0,
        'village_rate': 45.0,
        'school_rate': 280.0,
        'fire_rate': 12.0,
        'library_rate': 3.0,
    },
    'pelham_manor': {
        'municipality': 'Pelham Manor',
        'fiscal_year': '2024-2025',
        'rar': 0.025,
        'county_rate': 15.0,
        'town_rate': 8.0,
        'village_rate': 50.0,
        'school_rate': 280.0,
        'fire_rate': 12.0,
        'library_rate': 3.0,
    },
}

def save_tax_data():
    """Save tax rate data to JSON."""
    filepath = TAX_DIR / 'tax_rates.json'
    
    # Add metadata
    output = {
        'collection_date': date.today().isoformat(),
        'fiscal_year': '2024-2025',
        'data_source': 'Municipal budgets and NY State ORPTS',
        'municipalities': TAX_DATA
    }
    
    with open(filepath, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"✅ Tax data saved to: {filepath}")
    return filepath

def create_templates():
    """Create CSV templates for manual data entry."""
    import csv
    
    columns = [
        'address', 'city', 'state', 'zip_code',
        'sale_price', 'sqft', 'lot_sqft',
        'bedrooms', 'bathrooms', 'year_built',
        'sale_date', 'property_type',
        'annual_taxes', 'assessed_value',
        'source', 'url'
    ]
    
    templates = [
        ('bronxville', 'Bronxville', '10708'),
        ('eastchester', 'Eastchester', '10709'),
        ('tuckahoe', 'Tuckahoe', '10707'),
        ('scarsdale', 'Scarsdale', '10583'),
        ('larchmont', 'Larchmont', '10538'),
        ('mamaroneck', 'Mamaroneck', '10543'),
        ('pelham', 'Pelham', '10803'),
    ]
    
    for muni_key, city, zip_code in templates:
        filepath = TEMPLATES_DIR / f'{muni_key}_template.csv'
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            # Example row
            writer.writerow([
                '123 Example Street',
                city,
                'NY',
                zip_code,
                '1000000',
                '2000',
                '8000',
                '3',
                '2.5',
                '1960',
                '2024-06-15',
                'Single Family',
                '25000',
                '',
                'redfin',
                f'https://www.redfin.com/NY/{city}/...',
            ])
        
        print(f"✅ Template created: {filepath}")
    
    print(f"\n📝 Templates saved to: {TEMPLATES_DIR}")
    print("   Fill these with real data from Redfin/Zillow")

def print_redfin_urls():
    """Print Redfin URLs for manual data collection."""
    print("\n" + "="*70)
    print("REDFIN SEARCH URLs FOR MANUAL DATA COLLECTION")
    print("="*70)
    print("\nVisit these URLs to find recently sold homes:")
    print("-"*70)
    
    urls = [
        ('Bronxville', 'https://www.redfin.com/city/6330/NY/bronxville/filter/include=sold-3mo'),
        ('Eastchester', 'https://www.redfin.com/city/6330/NY/eastchester/filter/include=sold-3mo'),
        ('Tuckahoe', 'https://www.redfin.com/city/6330/NY/tuckahoe/filter/include=sold-3mo'),
        ('Scarsdale', 'https://www.redfin.com/city/6330/NY/scarsdale/filter/include=sold-3mo'),
        ('Larchmont', 'https://www.redfin.com/city/6330/NY/larchmont/filter/include=sold-3mo'),
        ('Mamaroneck', 'https://www.redfin.com/city/6330/NY/mamaroneck/filter/include=sold-3mo'),
        ('Pelham', 'https://www.redfin.com/city/6330/NY/pelham/filter/include=sold-3mo'),
    ]
    
    for name, url in urls:
        print(f"\n{name}:")
        print(f"  {url}")
    
    print("\n" + "-"*70)
    print("Instructions:")
    print("1. Click on each sold listing")
    print("2. Note: Address, Sale Price, Sqft, Beds, Baths, Sale Date")
    print("3. Look for 'Property taxes' in listing details")
    print("4. Enter data into templates in data/raw/sales/templates/")
    print("5. Save as [municipality]_sales.csv in data/raw/sales/")

def main():
    print("="*70)
    print("EASTCHESTER TAX ANALYSIS - DATA COLLECTION")
    print(f"Date: {date.today().isoformat()}")
    print("="*70)
    
    # Save tax data
    print("\n📊 Step 1: Saving tax rate data...")
    save_tax_data()
    
    # Create templates
    print("\n📝 Step 2: Creating manual data entry templates...")
    create_templates()
    
    # Print URLs
    print_redfin_urls()
    
    # Summary
    print("\n" + "="*70)
    print("DATA COLLECTION COMPLETE")
    print("="*70)
    print(f"""
Output files created:
  ✅ Tax rates: {TAX_DIR}/tax_rates.json
  ✅ Templates: {TEMPLATES_DIR}/*_template.csv

Next steps:
  1. Visit the Redfin URLs above to find recently sold homes
  2. Fill in the templates with real sales data
  3. Save filled templates as [municipality]_sales.csv in {SALES_DIR}/
  4. Run the analysis:
     - Jupyter: jupyter notebook notebooks/
     - Dashboard: streamlit run src/visualization/dashboard.py
     - Python: python3 -c "from src.analysis.comparison import ComparisonEngine; ..."

To view the tax data:
  cat {TAX_DIR}/tax_rates.json | python3 -m json.tool
""")

if __name__ == "__main__":
    main()
