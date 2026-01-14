#!/usr/bin/env python3
"""
Master Data Collection Script

Collects all data needed for the Eastchester tax analysis model:
1. Tax rate data from municipal sources
2. Home sales data from Redfin/Zillow/Realtor
3. RAR data from NY State ORPTS

Run with: python src/data_collection/collect_all_data.py
"""

import sys
from pathlib import Path
from datetime import date
import json
import time

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MUNICIPALITIES, SALES_DATA_DIR, TAX_RATES_DIR, 
    PROCESSED_DATA_DIR, DATA_DIR
)


def collect_tax_data():
    """Collect and save tax rate data."""
    from data_collection.tax_scraper import collect_all_tax_data
    
    print("\n" + "=" * 70)
    print("STEP 1: COLLECTING TAX RATE DATA")
    print("=" * 70)
    
    tax_data = collect_all_tax_data()
    return tax_data


def collect_sales_data():
    """Collect home sales data."""
    from data_collection.zillow_scraper import collect_all_sales
    
    print("\n" + "=" * 70)
    print("STEP 2: COLLECTING HOME SALES DATA")
    print("=" * 70)
    
    municipalities = [
        'bronxville', 'eastchester', 'tuckahoe',
        'scarsdale', 'larchmont', 'mamaroneck',
        'pelham',
    ]
    
    sales_data = collect_all_sales(municipalities, num_per_muni=50)
    return sales_data


def generate_sample_data_if_needed():
    """Generate sample data if scraping fails."""
    from data_collection.data_loader import DataLoader
    
    print("\n" + "=" * 70)
    print("GENERATING SAMPLE DATA (Scraping may be limited)")
    print("=" * 70)
    
    loader = DataLoader()
    
    # Check if we have any real data
    existing_files = list(SALES_DATA_DIR.glob('*.csv'))
    
    if not existing_files:
        print("No scraped data found. Generating realistic sample data...")
        
        dataset = loader.generate_sample_data(
            municipalities=[
                'bronxville', 'eastchester_unincorp', 'tuckahoe',
                'scarsdale', 'larchmont', 'mamaroneck_village',
                'pelham', 'pelham_manor'
            ],
            samples_per_muni=50
        )
        
        loader.save_unified_dataset(dataset, 'sample_sales.parquet')
        
        # Also save as CSV for inspection
        df = dataset.to_dataframe()
        df.to_csv(PROCESSED_DATA_DIR / 'sample_sales.csv', index=False)
        
        print(f"Generated {len(dataset)} sample sales records")
        return dataset
    else:
        print(f"Found {len(existing_files)} existing data files")
        return None


def update_config_with_real_rates(tax_data: dict):
    """Update config.py with actual tax rates."""
    
    print("\n" + "=" * 70)
    print("UPDATING CONFIGURATION WITH REAL DATA")
    print("=" * 70)
    
    # Save a Python-importable version
    config_data_path = DATA_DIR / 'tax_config.py'
    
    lines = [
        '"""',
        'Auto-generated tax configuration data.',
        f'Generated: {date.today().isoformat()}',
        '"""',
        '',
        '# Tax rates per $1,000 assessed value',
        'TAX_RATES = {',
    ]
    
    for key, data in tax_data.items():
        lines.append(f'    "{key}": {{')
        lines.append(f'        "rar": {data.rar},')
        lines.append(f'        "county": {data.county_rate},')
        lines.append(f'        "town": {data.town_rate},')
        lines.append(f'        "village": {data.village_rate},')
        lines.append(f'        "school": {data.school_rate},')
        lines.append(f'        "fire": {data.fire_rate},')
        lines.append(f'        "library": {data.library_rate},')
        lines.append('    },')
    
    lines.append('}')
    
    with open(config_data_path, 'w') as f:
        f.write('\n'.join(lines))
    
    print(f"Saved tax configuration to {config_data_path}")


def create_manual_data_templates():
    """Create CSV templates for manual data entry."""
    import pandas as pd
    
    print("\n" + "=" * 70)
    print("CREATING MANUAL DATA ENTRY TEMPLATES")
    print("=" * 70)
    
    # Template columns
    columns = [
        'address', 'city', 'state', 'zip_code',
        'sale_price', 'sqft', 'lot_sqft',
        'bedrooms', 'bathrooms', 'year_built',
        'sale_date', 'property_type',
        'annual_taxes', 'assessed_value',
        'source', 'url'
    ]
    
    municipalities = [
        ('bronxville', 'Bronxville', '10708'),
        ('eastchester', 'Eastchester', '10709'),
        ('tuckahoe', 'Tuckahoe', '10707'),
        ('scarsdale', 'Scarsdale', '10583'),
        ('larchmont', 'Larchmont', '10538'),
        ('mamaroneck', 'Mamaroneck', '10543'),
        ('pelham', 'Pelham', '10803'),
    ]
    
    templates_dir = SALES_DATA_DIR / 'templates'
    templates_dir.mkdir(parents=True, exist_ok=True)
    
    for muni_key, city_name, zip_code in municipalities:
        # Create example row
        example = pd.DataFrame([{
            'address': '123 Example Street',
            'city': city_name,
            'state': 'NY',
            'zip_code': zip_code,
            'sale_price': 1000000,
            'sqft': 2000,
            'lot_sqft': 8000,
            'bedrooms': 3,
            'bathrooms': 2.5,
            'year_built': 1960,
            'sale_date': '2024-06-15',
            'property_type': 'Single Family',
            'annual_taxes': 25000,
            'assessed_value': '',
            'source': 'redfin',
            'url': f'https://www.redfin.com/NY/{city_name}/...',
        }], columns=columns)
        
        filepath = templates_dir / f'{muni_key}_template.csv'
        example.to_csv(filepath, index=False)
        print(f"  Created: {filepath}")
    
    print(f"\nTemplates saved to {templates_dir}")
    print("Fill these in with real data from Redfin/Zillow search results")


def print_redfin_search_urls():
    """Print Redfin URLs for manual data collection."""
    
    print("\n" + "=" * 70)
    print("REDFIN SEARCH URLs FOR MANUAL DATA COLLECTION")
    print("=" * 70)
    print("\nVisit these URLs to view recently sold homes:")
    print("-" * 70)
    
    municipalities = [
        ('Bronxville', 'bronxville'),
        ('Eastchester', 'eastchester'), 
        ('Tuckahoe', 'tuckahoe'),
        ('Scarsdale', 'scarsdale'),
        ('Larchmont', 'larchmont'),
        ('Mamaroneck', 'mamaroneck'),
        ('Pelham', 'pelham'),
        ('Pelham Manor', 'pelham-manor'),
    ]
    
    for name, slug in municipalities:
        url = f"https://www.redfin.com/city/6330/NY/{slug}/filter/include=sold-3mo"
        print(f"\n{name}:")
        print(f"  {url}")
    
    print("\n" + "-" * 70)
    print("Tips for manual collection:")
    print("1. Click on each sold listing")
    print("2. Note: Address, Sale Price, Sqft, Beds, Baths, Sale Date")
    print("3. Look for 'Property taxes' in the listing details")
    print("4. Enter data into the templates in data/raw/sales/templates/")


def main():
    """Main data collection routine."""
    print("=" * 70)
    print("EASTCHESTER TAX ANALYSIS - DATA COLLECTION")
    print(f"Date: {date.today().isoformat()}")
    print("=" * 70)
    
    # Step 1: Collect tax data (always works - uses known values)
    tax_data = collect_tax_data()
    
    # Step 2: Try to collect sales data (may be blocked)
    print("\nAttempting to scrape home sales data...")
    print("Note: Real estate sites may block automated scraping.")
    
    try:
        sales_data = collect_sales_data()
    except Exception as e:
        print(f"\nScraping failed: {e}")
        sales_data = {}
    
    # Step 3: Generate sample data if scraping didn't work well
    total_sales = sum(len(s) for s in sales_data.values()) if sales_data else 0
    
    if total_sales < 50:
        print(f"\nOnly collected {total_sales} sales via scraping.")
        generate_sample_data_if_needed()
    
    # Step 4: Update config with real tax rates
    if tax_data:
        update_config_with_real_rates(tax_data)
    
    # Step 5: Create manual entry templates
    create_manual_data_templates()
    
    # Step 6: Print URLs for manual collection
    print_redfin_search_urls()
    
    # Summary
    print("\n" + "=" * 70)
    print("DATA COLLECTION COMPLETE")
    print("=" * 70)
    print(f"""
Next steps:
1. Tax rates have been saved to data/raw/tax_rates/
2. Sample data has been generated for testing
3. For REAL analysis, manually collect data from Redfin:
   - Use the templates in data/raw/sales/templates/
   - Fill in actual recently sold properties
   - Save as {muni}_sales.csv in data/raw/sales/

To run the analysis with current data:
  python -c "from src.analysis.comparison import ComparisonEngine; ..."
  
Or use the Jupyter notebooks:
  jupyter notebook notebooks/

Or launch the dashboard:
  streamlit run src/visualization/dashboard.py
""")


if __name__ == "__main__":
    main()


