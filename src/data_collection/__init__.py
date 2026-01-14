"""Data collection modules for gathering property and sales data."""

# Lazy imports to avoid requiring all dependencies at module load time
try:
    from .data_loader import DataLoader
except ImportError:
    DataLoader = None

try:
    from .redfin_scraper import RedfinScraper
except ImportError:
    RedfinScraper = None

try:
    from .tax_scraper import TaxDataScraper, collect_all_tax_data
except ImportError:
    TaxDataScraper = None
    collect_all_tax_data = None

try:
    from .zillow_scraper import ZillowScraper, RealtorScraper, collect_all_sales
except ImportError:
    ZillowScraper = None
    RealtorScraper = None
    collect_all_sales = None

__all__ = [
    "RedfinScraper", 
    "DataLoader",
    "TaxDataScraper",
    "collect_all_tax_data",
    "ZillowScraper",
    "RealtorScraper",
    "collect_all_sales",
]

