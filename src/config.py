"""
Configuration for Westchester County municipalities.

Contains Residential Assessment Ratios (RAR), tax rate structures,
and municipality metadata for the analysis model.
"""

from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class MunicipalityType(Enum):
    """Type of municipal entity."""
    TOWN = "town"
    VILLAGE = "village"
    CITY = "city"


class SchoolDistrict(Enum):
    """School districts in the analysis area."""
    EASTCHESTER = "Eastchester UFSD"
    BRONXVILLE = "Bronxville UFSD"
    TUCKAHOE = "Tuckahoe UFSD"
    SCARSDALE = "Scarsdale UFSD"
    MAMARONECK = "Mamaroneck UFSD"
    PELHAM = "Pelham UFSD"
    NEW_ROCHELLE = "New Rochelle City SD"
    RYE = "Rye City SD"
    RYE_NECK = "Rye Neck UFSD"


@dataclass
class TaxRates:
    """
    Tax rates per $1,000 of assessed value.
    
    Note: These rates should be updated annually from municipal sources.
    Last updated: 2024-2025 fiscal year
    """
    county: float = 0.0
    town: float = 0.0
    village: float = 0.0
    school: float = 0.0
    fire_district: float = 0.0
    library: float = 0.0
    special_districts: float = 0.0
    
    @property
    def total(self) -> float:
        """Total tax rate per $1,000 assessed."""
        return sum([
            self.county,
            self.town,
            self.village,
            self.school,
            self.fire_district,
            self.library,
            self.special_districts
        ])


@dataclass
class Municipality:
    """
    Configuration for a municipality.
    
    Attributes:
        name: Display name
        key: Internal identifier
        rar: Residential Assessment Ratio (as decimal, e.g., 0.0088 for 0.88%)
        municipality_type: Town, Village, or City
        school_district: Associated school district
        parent_town: For villages, the containing town
        has_village_tax: Whether village levies its own tax
        tax_rates: Current tax rates per $1,000 assessed
        redfin_url_slug: URL slug for Redfin searches
    """
    name: str
    key: str
    rar: float
    municipality_type: MunicipalityType
    school_district: SchoolDistrict
    parent_town: Optional[str] = None
    has_village_tax: bool = False
    tax_rates: TaxRates = field(default_factory=TaxRates)
    redfin_url_slug: str = ""
    zillow_region_id: str = ""
    
    def assessed_to_market(self, assessed_value: float) -> float:
        """Convert assessed value to estimated market value."""
        if self.rar == 0:
            raise ValueError(f"RAR not set for {self.name}")
        return assessed_value / self.rar
    
    def market_to_assessed(self, market_value: float) -> float:
        """Convert market value to assessed value."""
        return market_value * self.rar


# =============================================================================
# MUNICIPALITY CONFIGURATIONS
# =============================================================================

# Note: Tax rates are approximate and should be verified from municipal sources
# RAR values from NY State ORPTS / retiredassessor.com for 2025

MUNICIPALITIES = {
    # -------------------------------------------------------------------------
    # EASTCHESTER AREA
    # -------------------------------------------------------------------------
    "eastchester_unincorp": Municipality(
        name="Eastchester (Unincorporated)",
        key="eastchester_unincorp",
        rar=0.0088,  # 0.88%
        municipality_type=MunicipalityType.TOWN,
        school_district=SchoolDistrict.EASTCHESTER,
        has_village_tax=False,
        tax_rates=TaxRates(
            county=2.5,      # Approximate
            town=320.04,     # Town-outside rate (higher, no village services)
            village=0.0,
            school=850.0,    # Approximate - high due to low RAR
            fire_district=45.0,
            library=8.0,
        ),
        redfin_url_slug="eastchester",
    ),
    
    "bronxville": Municipality(
        name="Bronxville",
        key="bronxville",
        rar=1.0,  # 100% - assessed at full market value
        municipality_type=MunicipalityType.VILLAGE,
        school_district=SchoolDistrict.BRONXVILLE,
        parent_town="eastchester",
        has_village_tax=True,
        tax_rates=TaxRates(
            county=2.8,
            town=1.5,        # Lower town rate for village residents
            village=5.2,
            school=18.5,     # Much lower rate due to 100% RAR
            fire_district=0.5,
            library=0.3,
        ),
        redfin_url_slug="bronxville",
    ),
    
    "tuckahoe": Municipality(
        name="Tuckahoe",
        key="tuckahoe",
        rar=0.0098,  # 0.98%
        municipality_type=MunicipalityType.VILLAGE,
        school_district=SchoolDistrict.TUCKAHOE,
        parent_town="eastchester",
        has_village_tax=True,
        tax_rates=TaxRates(
            county=2.5,
            town=35.0,
            village=85.0,
            school=650.0,
            fire_district=40.0,
            library=7.0,
        ),
        redfin_url_slug="tuckahoe",
    ),
    
    # -------------------------------------------------------------------------
    # COMPARISON MUNICIPALITIES
    # -------------------------------------------------------------------------
    "scarsdale": Municipality(
        name="Scarsdale",
        key="scarsdale",
        rar=0.6973,  # 69.73%
        municipality_type=MunicipalityType.VILLAGE,
        school_district=SchoolDistrict.SCARSDALE,
        parent_town="scarsdale",  # Coterminous
        has_village_tax=True,
        tax_rates=TaxRates(
            county=4.0,
            town=0.0,  # Village is coterminous with town
            village=4.5,
            school=25.0,
            fire_district=0.8,
            library=0.4,
        ),
        redfin_url_slug="scarsdale",
    ),
    
    "larchmont": Municipality(
        name="Larchmont",
        key="larchmont",
        rar=1.0,  # 100%
        municipality_type=MunicipalityType.VILLAGE,
        school_district=SchoolDistrict.MAMARONECK,
        parent_town="mamaroneck",
        has_village_tax=True,
        tax_rates=TaxRates(
            county=4.27,
            town=0.0,  # Included in village
            village=4.70,
            school=12.64,
            fire_district=0.4,
            library=0.3,
        ),
        redfin_url_slug="larchmont",
    ),
    
    "mamaroneck_village": Municipality(
        name="Mamaroneck (Village)",
        key="mamaroneck_village",
        rar=1.0,  # 100%
        municipality_type=MunicipalityType.VILLAGE,
        school_district=SchoolDistrict.MAMARONECK,
        parent_town="mamaroneck",
        has_village_tax=True,
        tax_rates=TaxRates(
            county=3.86,
            town=0.0,
            village=6.34,
            school=12.64,
            fire_district=0.4,
            library=0.3,
        ),
        redfin_url_slug="mamaroneck",
    ),
    
    "mamaroneck_town": Municipality(
        name="Mamaroneck (Town/Unincorporated)",
        key="mamaroneck_town",
        rar=1.0,  # 100%
        municipality_type=MunicipalityType.TOWN,
        school_district=SchoolDistrict.MAMARONECK,
        has_village_tax=False,
        tax_rates=TaxRates(
            county=8.76,
            town=0.0,
            village=0.0,
            school=12.64,
            fire_district=0.5,
            library=0.3,
        ),
        redfin_url_slug="mamaroneck",
    ),
    
    "pelham": Municipality(
        name="Pelham (Village)",
        key="pelham",
        rar=0.025,  # ~2.5% (approximate)
        municipality_type=MunicipalityType.VILLAGE,
        school_district=SchoolDistrict.PELHAM,
        parent_town="pelham",
        has_village_tax=True,
        tax_rates=TaxRates(
            county=15.0,
            town=8.0,
            village=45.0,
            school=280.0,
            fire_district=12.0,
            library=3.0,
        ),
        redfin_url_slug="pelham",
    ),
    
    "pelham_manor": Municipality(
        name="Pelham Manor",
        key="pelham_manor",
        rar=0.025,  # ~2.5% (approximate)
        municipality_type=MunicipalityType.VILLAGE,
        school_district=SchoolDistrict.PELHAM,
        parent_town="pelham",
        has_village_tax=True,
        tax_rates=TaxRates(
            county=15.0,
            town=8.0,
            village=50.0,
            school=280.0,
            fire_district=12.0,
            library=3.0,
        ),
        redfin_url_slug="pelham-manor",
    ),
    
    "rye_city": Municipality(
        name="Rye (City)",
        key="rye_city",
        rar=0.0274,  # ~2.74%
        municipality_type=MunicipalityType.CITY,
        school_district=SchoolDistrict.RYE,
        has_village_tax=False,  # Cities don't have village tax
        tax_rates=TaxRates(
            county=12.0,
            town=0.0,
            village=0.0,  # City tax included in "town" equivalent
            school=320.0,
            fire_district=0.0,  # City provides
            library=4.0,
        ),
        redfin_url_slug="rye",
    ),
}

# Convenience groupings
EASTCHESTER_AREA = ["eastchester_unincorp", "bronxville", "tuckahoe"]
COMPARISON_TOWNS = ["scarsdale", "larchmont", "mamaroneck_village", "pelham", "pelham_manor"]
ALL_MUNICIPALITIES = list(MUNICIPALITIES.keys())


def get_municipality(key: str) -> Municipality:
    """Get municipality configuration by key."""
    if key not in MUNICIPALITIES:
        raise ValueError(f"Unknown municipality: {key}. Valid keys: {list(MUNICIPALITIES.keys())}")
    return MUNICIPALITIES[key]


def get_all_municipalities() -> list[Municipality]:
    """Get all municipality configurations."""
    return list(MUNICIPALITIES.values())


# =============================================================================
# DATA PATHS
# =============================================================================

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
SALES_DATA_DIR = RAW_DATA_DIR / "sales"
TAX_RATES_DIR = RAW_DATA_DIR / "tax_rates"
ASSESSMENTS_DIR = RAW_DATA_DIR / "assessments"

# Ensure directories exist
for dir_path in [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, 
                 SALES_DATA_DIR, TAX_RATES_DIR, ASSESSMENTS_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)


