"""
Data Loader for combining multiple data sources.

Loads and unifies data from:
- Scraped sales CSVs
- Manual entry CSVs
- Assessment records
- Tax rate files
"""

import pandas as pd
from pathlib import Path
from datetime import date, datetime
from typing import Optional
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    MUNICIPALITIES, 
    SALES_DATA_DIR, 
    PROCESSED_DATA_DIR,
    TAX_RATES_DIR,
    ASSESSMENTS_DIR,
    get_municipality
)
from models.property import SaleRecord, SaleDataset, PropertyType


class DataLoader:
    """
    Unified data loader for the analysis model.
    
    Handles loading, cleaning, and combining data from multiple sources
    into a consistent format for analysis.
    
    Example:
        >>> loader = DataLoader()
        >>> dataset = loader.load_all_sales()
        >>> print(f"Loaded {len(dataset)} total sales")
        >>> df = dataset.to_dataframe()
    """
    
    PROPERTY_TYPE_MAP = {
        'single family': PropertyType.SINGLE_FAMILY,
        'single-family': PropertyType.SINGLE_FAMILY,
        'house': PropertyType.SINGLE_FAMILY,
        'condo': PropertyType.CONDO,
        'condominium': PropertyType.CONDO,
        'coop': PropertyType.COOP,
        'co-op': PropertyType.COOP,
        'cooperative': PropertyType.COOP,
        'townhouse': PropertyType.TOWNHOUSE,
        'townhome': PropertyType.TOWNHOUSE,
        'multi-family': PropertyType.MULTI_FAMILY,
        'multi family': PropertyType.MULTI_FAMILY,
        'multifamily': PropertyType.MULTI_FAMILY,
    }
    
    # Map city names to municipality keys
    CITY_TO_MUNICIPALITY = {
        'bronxville': 'bronxville',
        'eastchester': 'eastchester_unincorp',
        'tuckahoe': 'tuckahoe',
        'scarsdale': 'scarsdale',
        'larchmont': 'larchmont',
        'mamaroneck': 'mamaroneck_village',
        'pelham': 'pelham',
        'pelham manor': 'pelham_manor',
        'rye': 'rye_city',
    }
    
    def __init__(
        self,
        sales_dir: Optional[Path] = None,
        processed_dir: Optional[Path] = None
    ):
        """
        Initialize loader with data directories.
        
        Args:
            sales_dir: Directory containing sales CSVs
            processed_dir: Directory for processed output
        """
        self.sales_dir = sales_dir or SALES_DATA_DIR
        self.processed_dir = processed_dir or PROCESSED_DATA_DIR
        
        # Ensure directories exist
        self.sales_dir.mkdir(parents=True, exist_ok=True)
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def load_sales_csv(self, filepath: Path) -> list[SaleRecord]:
        """
        Load sales from a single CSV file.
        
        Handles various column naming conventions and data formats.
        
        Args:
            filepath: Path to CSV file
            
        Returns:
            List of SaleRecord objects
        """
        if not filepath.exists():
            print(f"Warning: File not found: {filepath}")
            return []
        
        df = pd.read_csv(filepath)
        
        # Standardize column names
        df.columns = df.columns.str.lower().str.strip()
        df.columns = df.columns.str.replace(' ', '_')
        
        records = []
        
        for _, row in df.iterrows():
            try:
                record = self._row_to_sale_record(row, filepath.stem)
                if record:
                    records.append(record)
            except Exception as e:
                print(f"Warning: Skipping invalid row in {filepath.name}: {e}")
                continue
        
        return records
    
    def _row_to_sale_record(self, row: pd.Series, source_file: str) -> Optional[SaleRecord]:
        """Convert a DataFrame row to SaleRecord."""
        # Extract address
        address = self._get_value(row, ['address', 'street_address', 'streetaddress', 'full_address'])
        if not address:
            return None
        
        # Extract municipality
        city = self._get_value(row, ['city', 'municipality', 'town', 'village'])
        municipality = self._resolve_municipality(city, source_file)
        
        # Extract price
        sale_price = self._get_numeric(row, ['sale_price', 'saleprice', 'price', 'sold_price', 'soldprice'])
        if not sale_price or sale_price <= 0:
            return None
        
        # Extract sqft
        sqft = self._get_numeric(row, ['sqft', 'square_feet', 'squarefeet', 'sq_ft', 'living_area'])
        if not sqft or sqft <= 0:
            return None
        
        # Extract sale date
        sale_date = self._get_date(row, ['sale_date', 'saledate', 'sold_date', 'solddate', 'close_date'])
        if not sale_date:
            sale_date = date.today()
        
        # Extract tax info
        assessed_value = self._get_numeric(row, ['assessed_value', 'assessedvalue', 'assessment', 'tax_assessed_value'])
        annual_taxes = self._get_numeric(row, ['annual_taxes', 'annualtaxes', 'taxes', 'property_tax', 'tax_amount'])
        
        # Estimate taxes if not provided
        if not annual_taxes and assessed_value and municipality in MUNICIPALITIES:
            # Will be calculated later using tax calculator
            annual_taxes = 0.0
        elif not annual_taxes:
            annual_taxes = 0.0
        
        if not assessed_value:
            assessed_value = 0.0
        
        # Other fields
        lot_sqft = self._get_numeric(row, ['lot_sqft', 'lot_size', 'lotsize', 'lot_area'])
        bedrooms = int(self._get_numeric(row, ['bedrooms', 'beds', 'br']) or 0)
        bathrooms = self._get_numeric(row, ['bathrooms', 'baths', 'ba']) or 0.0
        year_built = int(self._get_numeric(row, ['year_built', 'yearbuilt', 'built']) or 0) or None
        
        # Property type
        prop_type_str = self._get_value(row, ['property_type', 'propertytype', 'type', 'home_type'])
        property_type = self._resolve_property_type(prop_type_str)
        
        # URL
        url = self._get_value(row, ['url', 'listing_url', 'link'])
        
        # Source
        source = self._get_value(row, ['source']) or 'csv'
        
        return SaleRecord(
            address=str(address),
            municipality=municipality,
            sqft=float(sqft),
            sale_price=float(sale_price),
            sale_date=sale_date,
            assessed_value=float(assessed_value),
            annual_taxes=float(annual_taxes),
            lot_sqft=float(lot_sqft) if lot_sqft else None,
            bedrooms=bedrooms,
            bathrooms=bathrooms,
            year_built=year_built,
            property_type=property_type,
            source=source,
            listing_url=url,
        )
    
    def _get_value(self, row: pd.Series, columns: list[str]) -> Optional[str]:
        """Get first available value from list of column names."""
        for col in columns:
            if col in row.index and pd.notna(row[col]):
                return str(row[col]).strip()
        return None
    
    def _get_numeric(self, row: pd.Series, columns: list[str]) -> Optional[float]:
        """Get first available numeric value from list of column names."""
        for col in columns:
            if col in row.index and pd.notna(row[col]):
                try:
                    # Handle currency strings
                    value = str(row[col]).replace('$', '').replace(',', '').strip()
                    return float(value)
                except ValueError:
                    continue
        return None
    
    def _get_date(self, row: pd.Series, columns: list[str]) -> Optional[date]:
        """Get first available date value from list of column names."""
        for col in columns:
            if col in row.index and pd.notna(row[col]):
                try:
                    value = row[col]
                    if isinstance(value, (datetime, date)):
                        return value if isinstance(value, date) else value.date()
                    
                    # Try parsing string
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%m-%d-%Y', '%Y/%m/%d']:
                        try:
                            return datetime.strptime(str(value), fmt).date()
                        except ValueError:
                            continue
                except Exception:
                    continue
        return None
    
    def _resolve_municipality(self, city: Optional[str], source_file: str) -> str:
        """Resolve city name to municipality key."""
        if city:
            city_lower = city.lower().strip()
            if city_lower in self.CITY_TO_MUNICIPALITY:
                return self.CITY_TO_MUNICIPALITY[city_lower]
            # Check if it's already a municipality key
            if city_lower in MUNICIPALITIES:
                return city_lower
        
        # Try to infer from filename
        for key in MUNICIPALITIES.keys():
            if key in source_file.lower():
                return key
        
        return city.lower().replace(' ', '_') if city else 'unknown'
    
    def _resolve_property_type(self, type_str: Optional[str]) -> PropertyType:
        """Resolve property type string to enum."""
        if not type_str:
            return PropertyType.SINGLE_FAMILY
        
        type_lower = type_str.lower().strip()
        return self.PROPERTY_TYPE_MAP.get(type_lower, PropertyType.OTHER)
    
    def load_all_sales(self, pattern: str = "*.csv") -> SaleDataset:
        """
        Load all sales CSVs from the sales directory.
        
        Args:
            pattern: Glob pattern for files to load
            
        Returns:
            SaleDataset containing all records
        """
        all_records = []
        
        for filepath in self.sales_dir.glob(pattern):
            if filepath.stem.endswith('_template'):
                continue  # Skip templates
            
            records = self.load_sales_csv(filepath)
            all_records.extend(records)
            print(f"Loaded {len(records)} records from {filepath.name}")
        
        return SaleDataset(records=all_records)
    
    def load_municipality_sales(self, municipality_key: str) -> SaleDataset:
        """
        Load sales for a specific municipality.
        
        Args:
            municipality_key: Municipality identifier
            
        Returns:
            SaleDataset for that municipality
        """
        all_sales = self.load_all_sales()
        return all_sales.filter_by_municipality(municipality_key)
    
    def save_unified_dataset(
        self,
        dataset: SaleDataset,
        filename: str = "unified_sales.parquet"
    ) -> Path:
        """
        Save unified dataset to processed directory.
        
        Uses Parquet format for efficiency and type preservation.
        
        Args:
            dataset: SaleDataset to save
            filename: Output filename
            
        Returns:
            Path to saved file
        """
        filepath = self.processed_dir / filename
        df = dataset.to_dataframe()
        df.to_parquet(filepath, index=False)
        print(f"Saved {len(df)} records to {filepath}")
        return filepath
    
    def load_unified_dataset(self, filename: str = "unified_sales.parquet") -> SaleDataset:
        """
        Load previously saved unified dataset.
        
        Args:
            filename: Parquet filename
            
        Returns:
            SaleDataset
        """
        filepath = self.processed_dir / filename
        
        if not filepath.exists():
            raise FileNotFoundError(f"No unified dataset found at {filepath}")
        
        df = pd.read_parquet(filepath)
        return SaleDataset.from_dataframe(df)
    
    def generate_sample_data(
        self,
        municipalities: Optional[list[str]] = None,
        samples_per_muni: int = 10
    ) -> SaleDataset:
        """
        Generate sample/synthetic data for testing.
        
        Creates realistic-looking sale records for testing the model.
        
        Args:
            municipalities: List of municipality keys
            samples_per_muni: Number of samples per municipality
            
        Returns:
            SaleDataset with synthetic data
        """
        import random
        
        municipalities = municipalities or [
            'bronxville', 'eastchester_unincorp', 'tuckahoe', 
            'scarsdale', 'larchmont'
        ]
        
        # Realistic ranges by municipality
        price_ranges = {
            'bronxville': (900_000, 3_500_000),
            'eastchester_unincorp': (500_000, 1_200_000),
            'tuckahoe': (450_000, 1_000_000),
            'scarsdale': (800_000, 4_000_000),
            'larchmont': (700_000, 2_500_000),
            'mamaroneck_village': (600_000, 2_000_000),
            'pelham': (500_000, 1_500_000),
        }
        
        sqft_ranges = {
            'bronxville': (1_500, 4_500),
            'eastchester_unincorp': (1_200, 3_000),
            'tuckahoe': (1_000, 2_500),
            'scarsdale': (2_000, 5_500),
            'larchmont': (1_500, 4_000),
            'mamaroneck_village': (1_400, 3_500),
            'pelham': (1_200, 3_200),
        }
        
        records = []
        
        for muni in municipalities:
            price_range = price_ranges.get(muni, (500_000, 1_500_000))
            sqft_range = sqft_ranges.get(muni, (1_200, 3_000))
            
            muni_config = MUNICIPALITIES.get(muni)
            
            for i in range(samples_per_muni):
                # Generate realistic values
                sqft = random.randint(sqft_range[0], sqft_range[1])
                
                # Price correlates somewhat with sqft
                base_price = random.uniform(price_range[0], price_range[1])
                price_per_sqft = base_price / sqft
                # Add some variance
                price = sqft * price_per_sqft * random.uniform(0.85, 1.15)
                
                # Calculate assessed value based on RAR
                rar = muni_config.rar if muni_config else 0.01
                assessed = price * rar
                
                # Calculate realistic taxes
                if muni_config:
                    tax_rate = muni_config.tax_rates.total
                    taxes = (assessed / 1000) * tax_rate
                else:
                    taxes = price * 0.025  # Assume 2.5% effective rate
                
                # Random sale date in last 6 months
                days_back = random.randint(0, 180)
                sale_date = date.today() - pd.Timedelta(days=days_back)
                
                records.append(SaleRecord(
                    address=f"{random.randint(1, 999)} Sample Street {i+1}",
                    municipality=muni,
                    sqft=float(sqft),
                    sale_price=round(price, -3),  # Round to nearest thousand
                    sale_date=sale_date,
                    assessed_value=round(assessed, 2),
                    annual_taxes=round(taxes, 2),
                    bedrooms=random.randint(2, 5),
                    bathrooms=random.choice([1.5, 2.0, 2.5, 3.0, 3.5]),
                    year_built=random.randint(1920, 2020),
                    source='synthetic',
                ))
        
        return SaleDataset(records=records)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    loader = DataLoader()
    
    print("=" * 60)
    print("DATA LOADER DEMO")
    print("=" * 60)
    
    # Generate sample data for testing
    print("\nGenerating sample data...")
    sample_data = loader.generate_sample_data(
        municipalities=['bronxville', 'eastchester_unincorp', 'tuckahoe', 'scarsdale', 'larchmont'],
        samples_per_muni=10
    )
    
    print(f"Generated {len(sample_data)} sample records")
    
    # Convert to DataFrame and display
    df = sample_data.to_dataframe()
    
    print("\nSample Data Summary by Municipality:")
    print("-" * 60)
    
    summary = df.groupby('municipality').agg({
        'sale_price': ['count', 'mean', 'median'],
        'price_per_sqft': ['mean', 'median'],
        'tax_per_sqft': ['mean'],
        'effective_tax_rate': ['mean'],
    }).round(2)
    
    print(summary)
    
    # Save sample data
    print("\nSaving sample data...")
    loader.save_unified_dataset(sample_data, "sample_sales.parquet")
    
    print("\nSample records:")
    for record in sample_data.records[:3]:
        print(f"  {record.address} ({record.municipality})")
        print(f"    ${record.sale_price:,.0f} | {record.sqft:,.0f} sqft | ${record.price_per_sqft:,.0f}/sqft")
        print(f"    Tax: ${record.annual_taxes:,.0f}/yr | {record.effective_tax_rate:.2f}%")
        print()


