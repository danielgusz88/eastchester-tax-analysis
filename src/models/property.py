"""
Property and Sale data models.

Defines the core data structures for representing properties,
sales records, and computed metrics.
"""

from dataclasses import dataclass, field
from datetime import date, datetime
from typing import Optional
from enum import Enum


class PropertyType(Enum):
    """Type of residential property."""
    SINGLE_FAMILY = "single_family"
    CONDO = "condo"
    COOP = "coop"
    TOWNHOUSE = "townhouse"
    MULTI_FAMILY = "multi_family"
    OTHER = "other"


@dataclass
class Property:
    """
    Represents a residential property.
    
    Attributes:
        address: Full street address
        municipality: Municipality key (e.g., 'bronxville', 'eastchester_unincorp')
        sqft: Living area in square feet
        lot_sqft: Lot size in square feet (optional)
        bedrooms: Number of bedrooms
        bathrooms: Number of bathrooms (can be decimal, e.g., 2.5)
        year_built: Year the property was constructed
        property_type: Type of property
        assessed_value: Current assessed value for tax purposes
        tax_class: Property tax class (if applicable)
    """
    address: str
    municipality: str
    sqft: float
    lot_sqft: Optional[float] = None
    bedrooms: int = 0
    bathrooms: float = 0.0
    year_built: Optional[int] = None
    property_type: PropertyType = PropertyType.SINGLE_FAMILY
    assessed_value: Optional[float] = None
    tax_class: Optional[str] = None
    
    def __post_init__(self):
        if self.sqft <= 0:
            raise ValueError(f"Square footage must be positive, got {self.sqft}")
    
    @property
    def age(self) -> Optional[int]:
        """Property age in years."""
        if self.year_built:
            return datetime.now().year - self.year_built
        return None


@dataclass
class SaleRecord:
    """
    Represents a property sale transaction.
    
    Combines property details with sale-specific information.
    """
    # Property info
    address: str
    municipality: str
    sqft: float
    
    # Sale info
    sale_price: float
    sale_date: date
    
    # Tax info
    assessed_value: float
    annual_taxes: float
    
    # Optional property details
    lot_sqft: Optional[float] = None
    bedrooms: int = 0
    bathrooms: float = 0.0
    year_built: Optional[int] = None
    property_type: PropertyType = PropertyType.SINGLE_FAMILY
    
    # Metadata
    source: str = "unknown"  # e.g., 'redfin', 'zillow', 'mls'
    listing_url: Optional[str] = None
    
    def __post_init__(self):
        if self.sqft <= 0:
            raise ValueError(f"Square footage must be positive, got {self.sqft}")
        if self.sale_price <= 0:
            raise ValueError(f"Sale price must be positive, got {self.sale_price}")
    
    @property
    def price_per_sqft(self) -> float:
        """Sale price per square foot."""
        return self.sale_price / self.sqft
    
    @property
    def tax_per_sqft(self) -> float:
        """Annual taxes per square foot."""
        return self.annual_taxes / self.sqft
    
    @property
    def effective_tax_rate(self) -> float:
        """Tax as percentage of sale price."""
        return (self.annual_taxes / self.sale_price) * 100
    
    @property
    def assessed_to_sale_ratio(self) -> float:
        """Ratio of assessed value to sale price (indicates RAR accuracy)."""
        return self.assessed_value / self.sale_price
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            'address': self.address,
            'municipality': self.municipality,
            'sqft': self.sqft,
            'lot_sqft': self.lot_sqft,
            'bedrooms': self.bedrooms,
            'bathrooms': self.bathrooms,
            'year_built': self.year_built,
            'property_type': self.property_type.value,
            'sale_price': self.sale_price,
            'sale_date': self.sale_date,
            'assessed_value': self.assessed_value,
            'annual_taxes': self.annual_taxes,
            'source': self.source,
            'listing_url': self.listing_url,
            # Computed fields
            'price_per_sqft': self.price_per_sqft,
            'tax_per_sqft': self.tax_per_sqft,
            'effective_tax_rate': self.effective_tax_rate,
        }


@dataclass
class PropertyMetrics:
    """
    Computed metrics for a property or sale.
    
    Used for standardized comparison across municipalities.
    """
    # Core identifiers
    municipality: str
    address: Optional[str] = None
    
    # Value metrics
    market_value: float = 0.0
    sqft: float = 0.0
    value_per_sqft: float = 0.0
    
    # Tax metrics
    total_annual_tax: float = 0.0
    tax_per_sqft: float = 0.0
    effective_tax_rate: float = 0.0  # As percentage
    
    # Breakdown (optional)
    county_tax: float = 0.0
    town_tax: float = 0.0
    village_tax: float = 0.0
    school_tax: float = 0.0
    other_tax: float = 0.0
    
    @property
    def tax_efficiency_ratio(self) -> float:
        """
        Tax dollars per $1,000 of value per sqft.
        
        Lower is better - means less tax burden for the value you get.
        """
        if self.value_per_sqft == 0:
            return float('inf')
        return (self.tax_per_sqft / self.value_per_sqft) * 1000
    
    @property
    def school_tax_percentage(self) -> float:
        """School tax as percentage of total tax."""
        if self.total_annual_tax == 0:
            return 0.0
        return (self.school_tax / self.total_annual_tax) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame creation."""
        return {
            'municipality': self.municipality,
            'address': self.address,
            'market_value': self.market_value,
            'sqft': self.sqft,
            'value_per_sqft': self.value_per_sqft,
            'total_annual_tax': self.total_annual_tax,
            'tax_per_sqft': self.tax_per_sqft,
            'effective_tax_rate': self.effective_tax_rate,
            'tax_efficiency_ratio': self.tax_efficiency_ratio,
            'county_tax': self.county_tax,
            'town_tax': self.town_tax,
            'village_tax': self.village_tax,
            'school_tax': self.school_tax,
            'other_tax': self.other_tax,
            'school_tax_percentage': self.school_tax_percentage,
        }


@dataclass 
class SaleDataset:
    """
    Collection of sale records for analysis.
    """
    records: list[SaleRecord] = field(default_factory=list)
    municipality: Optional[str] = None
    collection_date: date = field(default_factory=date.today)
    
    def __len__(self) -> int:
        return len(self.records)
    
    def __iter__(self):
        return iter(self.records)
    
    def add(self, record: SaleRecord) -> None:
        """Add a sale record."""
        self.records.append(record)
    
    def filter_by_municipality(self, municipality: str) -> 'SaleDataset':
        """Return new dataset filtered to one municipality."""
        filtered = [r for r in self.records if r.municipality == municipality]
        return SaleDataset(
            records=filtered,
            municipality=municipality,
            collection_date=self.collection_date
        )
    
    def to_dataframe(self):
        """Convert to pandas DataFrame."""
        import pandas as pd
        return pd.DataFrame([r.to_dict() for r in self.records])
    
    @classmethod
    def from_dataframe(cls, df, municipality: Optional[str] = None) -> 'SaleDataset':
        """Create from pandas DataFrame."""
        records = []
        for _, row in df.iterrows():
            try:
                record = SaleRecord(
                    address=row['address'],
                    municipality=row['municipality'],
                    sqft=float(row['sqft']),
                    sale_price=float(row['sale_price']),
                    sale_date=row['sale_date'] if isinstance(row['sale_date'], date) 
                              else datetime.strptime(row['sale_date'], '%Y-%m-%d').date(),
                    assessed_value=float(row.get('assessed_value', 0)),
                    annual_taxes=float(row.get('annual_taxes', 0)),
                    lot_sqft=float(row['lot_sqft']) if row.get('lot_sqft') else None,
                    bedrooms=int(row.get('bedrooms', 0)),
                    bathrooms=float(row.get('bathrooms', 0)),
                    year_built=int(row['year_built']) if row.get('year_built') else None,
                    source=row.get('source', 'csv'),
                    listing_url=row.get('listing_url'),
                )
                records.append(record)
            except (ValueError, KeyError) as e:
                print(f"Warning: Skipping invalid record: {e}")
                continue
        
        return cls(records=records, municipality=municipality)


