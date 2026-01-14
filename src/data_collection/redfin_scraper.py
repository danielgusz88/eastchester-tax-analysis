"""
Redfin Web Scraper for Recent Home Sales.

Collects recent sale data from Redfin for Westchester County municipalities.
Handles rate limiting, pagination, and data extraction.

IMPORTANT: Web scraping should be done responsibly:
- Respect robots.txt
- Use reasonable rate limits
- Don't overload servers
- Consider using official APIs when available
"""

import json
import re
import time
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from urllib.parse import urlencode, quote
import sys

# Rate limiting
try:
    from ratelimit import limits, sleep_and_retry
    HAS_RATELIMIT = True
except ImportError:
    HAS_RATELIMIT = False

import requests
from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MUNICIPALITIES, get_municipality, SALES_DATA_DIR


@dataclass
class RedfinListing:
    """Raw listing data from Redfin."""
    address: str
    city: str
    state: str = "NY"
    zip_code: str = ""
    price: float = 0.0
    sqft: float = 0.0
    lot_sqft: Optional[float] = None
    beds: int = 0
    baths: float = 0.0
    year_built: Optional[int] = None
    sold_date: Optional[date] = None
    property_type: str = "Single Family"
    url: str = ""
    hoa: Optional[float] = None
    
    # Tax info (if available)
    annual_tax: Optional[float] = None
    tax_assessed_value: Optional[float] = None


class RedfinScraper:
    """
    Scraper for collecting recent home sales from Redfin.
    
    Uses Redfin's internal API endpoints to fetch sold listings data.
    
    Example:
        >>> scraper = RedfinScraper()
        >>> sales = scraper.collect_recent_sales('bronxville', num_sales=50)
        >>> print(f"Collected {len(sales)} sales")
        >>> scraper.save_to_csv(sales, 'bronxville_sales.csv')
    
    Note: Redfin's website structure may change. If scraping fails,
    you may need to update the selectors and API endpoints.
    """
    
    BASE_URL = "https://www.redfin.com"
    
    # Redfin region IDs for Westchester municipalities
    # These can be found by searching on Redfin and extracting from URLs
    REGION_IDS = {
        'bronxville': '12329',
        'eastchester': '22483',  # Note: This covers unincorporated area
        'tuckahoe': '19207',
        'scarsdale': '17205',
        'larchmont': '13260',
        'mamaroneck': '14001',
        'pelham': '15918',
        'pelham_manor': '15919',
        'rye': '17117',
    }
    
    # URL slugs for city searches
    CITY_SLUGS = {
        'bronxville': 'bronxville',
        'eastchester': 'eastchester',
        'eastchester_unincorp': 'eastchester',
        'tuckahoe': 'tuckahoe',
        'scarsdale': 'scarsdale',
        'larchmont': 'larchmont',
        'mamaroneck': 'mamaroneck',
        'mamaroneck_village': 'mamaroneck',
        'mamaroneck_town': 'mamaroneck',
        'pelham': 'pelham',
        'pelham_manor': 'pelham-manor',
        'rye_city': 'rye',
    }
    
    def __init__(
        self,
        rate_limit_calls: int = 5,
        rate_limit_period: int = 60,
        user_agent: Optional[str] = None
    ):
        """
        Initialize scraper with rate limiting.
        
        Args:
            rate_limit_calls: Max calls per period
            rate_limit_period: Period in seconds
            user_agent: Custom user agent string
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': user_agent or (
                'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
                'AppleWebKit/537.36 (KHTML, like Gecko) '
                'Chrome/120.0.0.0 Safari/537.36'
            ),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        })
        
        self.rate_limit_calls = rate_limit_calls
        self.rate_limit_period = rate_limit_period
        self._last_request_time = 0
    
    def _rate_limit(self):
        """Simple rate limiting."""
        elapsed = time.time() - self._last_request_time
        min_interval = self.rate_limit_period / self.rate_limit_calls
        
        if elapsed < min_interval:
            time.sleep(min_interval - elapsed)
        
        self._last_request_time = time.time()
    
    def _make_request(self, url: str, params: Optional[dict] = None) -> requests.Response:
        """Make rate-limited request."""
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            return response
        except requests.RequestException as e:
            print(f"Request failed: {e}")
            raise
    
    def get_sold_listings_url(self, municipality_key: str) -> str:
        """
        Build Redfin sold listings URL for a municipality.
        
        Args:
            municipality_key: Key from MUNICIPALITIES config
            
        Returns:
            URL for sold listings search
        """
        slug = self.CITY_SLUGS.get(municipality_key, municipality_key.replace('_', '-'))
        
        # Redfin sold listings URL format
        # /city/STATE-CODE/CITY-NAME/filter/include=sold-3mo
        return f"{self.BASE_URL}/city/6330/NY/{slug}/filter/include=sold-3mo"
    
    def get_stingray_api_url(self, municipality_key: str) -> str:
        """
        Build Redfin's internal API URL for data.
        
        The 'stingray' API returns JSON data for listings.
        """
        region_id = self.REGION_IDS.get(municipality_key, '')
        if not region_id:
            # Fall back to city search
            slug = self.CITY_SLUGS.get(municipality_key, municipality_key)
            return f"{self.BASE_URL}/stingray/api/gis?al=1&include_nearby_homes=true&market=nyc&num_homes=350&ord=redfin-recommended-asc&page_number=1&poly=-73.87%2040.91%2C-73.77%2040.91%2C-73.77%2040.99%2C-73.87%2040.99&sf=1,2,3,5,6,7&sold_within_days=90&status=9&uipt=1,2,3,4,5,6&v=8"
        
        return (
            f"{self.BASE_URL}/stingray/api/gis?"
            f"al=1&market=nyc&num_homes=350&"
            f"region_id={region_id}&region_type=6&"
            f"sold_within_days=90&status=9&uipt=1,2,3,4,5,6&v=8"
        )
    
    def parse_listing_from_html(self, soup: BeautifulSoup) -> list[RedfinListing]:
        """
        Parse listings from Redfin HTML search results page.
        
        Args:
            soup: BeautifulSoup parsed HTML
            
        Returns:
            List of RedfinListing objects
        """
        listings = []
        
        # Find home cards - Redfin uses data-rf-test-id attributes
        home_cards = soup.find_all('div', {'class': re.compile(r'HomeCard')})
        
        if not home_cards:
            # Try alternative selectors
            home_cards = soup.find_all('div', {'data-rf-test-id': 'home-card'})
        
        for card in home_cards:
            try:
                listing = self._parse_home_card(card)
                if listing:
                    listings.append(listing)
            except Exception as e:
                print(f"Warning: Failed to parse listing: {e}")
                continue
        
        return listings
    
    def _parse_home_card(self, card) -> Optional[RedfinListing]:
        """Parse a single home card element."""
        # Extract price
        price_elem = card.find('span', {'class': re.compile(r'homecardPrice|price')})
        price = 0.0
        if price_elem:
            price_text = price_elem.get_text().strip()
            price = self._parse_price(price_text)
        
        if price == 0:
            return None  # Skip listings without price
        
        # Extract address
        address_elem = card.find('div', {'class': re.compile(r'homeAddress|address')})
        if not address_elem:
            address_elem = card.find('span', {'class': re.compile(r'streetAddress')})
        
        address = address_elem.get_text().strip() if address_elem else "Unknown"
        
        # Extract beds/baths/sqft
        stats = card.find_all('div', {'class': re.compile(r'stats?|HomeStats')})
        beds, baths, sqft = 0, 0.0, 0.0
        
        for stat in stats:
            text = stat.get_text().lower()
            if 'bed' in text:
                beds = self._extract_number(text)
            elif 'bath' in text:
                baths = self._extract_number(text)
            elif 'sq' in text:
                sqft = self._extract_number(text)
        
        # Alternative: Parse from stat items
        stat_items = card.find_all('span', {'class': re.compile(r'HomeStatsV2')})
        for item in stat_items:
            text = item.get_text().lower()
            if 'bd' in text or 'bed' in text:
                beds = int(self._extract_number(text))
            elif 'ba' in text or 'bath' in text:
                baths = self._extract_number(text)
            elif 'sq' in text:
                sqft = self._extract_number(text)
        
        # Get URL
        link = card.find('a', href=True)
        url = ""
        if link:
            href = link['href']
            url = href if href.startswith('http') else f"{self.BASE_URL}{href}"
        
        # Get city from address or listing
        city = ""
        city_elem = card.find('span', {'class': re.compile(r'cityState')})
        if city_elem:
            city = city_elem.get_text().split(',')[0].strip()
        
        return RedfinListing(
            address=address,
            city=city,
            price=price,
            sqft=sqft,
            beds=beds,
            baths=baths,
            url=url,
        )
    
    def _parse_price(self, price_text: str) -> float:
        """Parse price string to float."""
        # Remove $ and commas, handle K/M suffixes
        price_text = price_text.replace('$', '').replace(',', '').strip()
        
        multiplier = 1
        if price_text.endswith('K'):
            multiplier = 1000
            price_text = price_text[:-1]
        elif price_text.endswith('M'):
            multiplier = 1_000_000
            price_text = price_text[:-1]
        
        try:
            return float(price_text) * multiplier
        except ValueError:
            return 0.0
    
    def _extract_number(self, text: str) -> float:
        """Extract first number from text."""
        match = re.search(r'[\d,]+\.?\d*', text.replace(',', ''))
        if match:
            try:
                return float(match.group())
            except ValueError:
                pass
        return 0.0
    
    def parse_listings_from_json(self, data: dict) -> list[RedfinListing]:
        """
        Parse listings from Redfin API JSON response.
        
        Args:
            data: JSON response from Redfin stingray API
            
        Returns:
            List of RedfinListing objects
        """
        listings = []
        
        # Navigate JSON structure
        homes = data.get('payload', {}).get('homes', [])
        
        for home in homes:
            try:
                listing = self._parse_json_home(home)
                if listing:
                    listings.append(listing)
            except Exception as e:
                print(f"Warning: Failed to parse JSON listing: {e}")
                continue
        
        return listings
    
    def _parse_json_home(self, home: dict) -> Optional[RedfinListing]:
        """Parse a single home from JSON data."""
        # Extract basic info
        price = home.get('price', {})
        if isinstance(price, dict):
            price_value = price.get('value', 0)
        else:
            price_value = price or 0
        
        if not price_value:
            return None
        
        # Address info
        address_info = home.get('streetLine', {})
        if isinstance(address_info, dict):
            address = address_info.get('value', '')
        else:
            address = address_info or home.get('addressLine', 'Unknown')
        
        # Location
        city = home.get('city', '')
        zip_code = home.get('zip', '')
        
        # Property details
        sqft = home.get('sqFt', {})
        if isinstance(sqft, dict):
            sqft_value = sqft.get('value', 0)
        else:
            sqft_value = sqft or 0
        
        beds = home.get('beds', 0)
        baths = home.get('baths', 0)
        
        # Lot size
        lot_sqft = home.get('lotSize', {})
        if isinstance(lot_sqft, dict):
            lot_value = lot_sqft.get('value')
        else:
            lot_value = lot_sqft
        
        # Year built
        year_built = home.get('yearBuilt', {})
        if isinstance(year_built, dict):
            year_value = year_built.get('value')
        else:
            year_value = year_built
        
        # Sold date
        sold_date = None
        sold_date_str = home.get('soldDate') or home.get('lastSoldDate')
        if sold_date_str:
            try:
                # Redfin uses epoch milliseconds
                if isinstance(sold_date_str, (int, float)):
                    sold_date = datetime.fromtimestamp(sold_date_str / 1000).date()
                else:
                    sold_date = datetime.strptime(sold_date_str, '%Y-%m-%d').date()
            except (ValueError, TypeError):
                pass
        
        # URL
        url = home.get('url', '')
        if url and not url.startswith('http'):
            url = f"{self.BASE_URL}{url}"
        
        # Property type
        property_type_map = {
            1: 'Single Family',
            2: 'Condo',
            3: 'Townhouse',
            4: 'Multi-Family',
            6: 'Coop',
        }
        prop_type = property_type_map.get(home.get('propertyType', 1), 'Other')
        
        # Tax info (may not always be available)
        tax_info = home.get('taxInfo', {})
        annual_tax = tax_info.get('taxAnnualAmount') if tax_info else None
        assessed_value = tax_info.get('taxAssessedValue') if tax_info else None
        
        return RedfinListing(
            address=address,
            city=city,
            zip_code=str(zip_code),
            price=float(price_value),
            sqft=float(sqft_value) if sqft_value else 0,
            lot_sqft=float(lot_value) if lot_value else None,
            beds=int(beds) if beds else 0,
            baths=float(baths) if baths else 0,
            year_built=int(year_value) if year_value else None,
            sold_date=sold_date,
            property_type=prop_type,
            url=url,
            annual_tax=annual_tax,
            tax_assessed_value=assessed_value,
        )
    
    def collect_recent_sales(
        self,
        municipality_key: str,
        num_sales: int = 50,
        days_back: int = 180
    ) -> list[RedfinListing]:
        """
        Collect recent sales for a municipality.
        
        This method tries multiple approaches:
        1. Redfin's internal API (JSON)
        2. HTML scraping fallback
        
        Args:
            municipality_key: Municipality identifier
            num_sales: Target number of sales to collect
            days_back: How far back to look for sales
            
        Returns:
            List of RedfinListing objects
        """
        print(f"Collecting sales for {municipality_key}...")
        
        listings = []
        
        # Try API first
        try:
            listings = self._collect_via_api(municipality_key, num_sales)
        except Exception as e:
            print(f"API collection failed: {e}")
            print("Falling back to HTML scraping...")
        
        # Fall back to HTML if needed
        if len(listings) < num_sales:
            try:
                html_listings = self._collect_via_html(municipality_key, num_sales - len(listings))
                listings.extend(html_listings)
            except Exception as e:
                print(f"HTML scraping failed: {e}")
        
        # Filter to only recent sales
        cutoff_date = date.today() - timedelta(days=days_back)
        listings = [
            l for l in listings
            if l.sold_date is None or l.sold_date >= cutoff_date
        ]
        
        # Limit to requested number
        listings = listings[:num_sales]
        
        print(f"Collected {len(listings)} sales for {municipality_key}")
        return listings
    
    def _collect_via_api(
        self,
        municipality_key: str,
        num_sales: int
    ) -> list[RedfinListing]:
        """Collect sales via Redfin's internal API."""
        url = self.get_stingray_api_url(municipality_key)
        response = self._make_request(url)
        
        # Redfin API returns data with a prefix we need to strip
        text = response.text
        if text.startswith('{}&&'):
            text = text[4:]
        
        data = json.loads(text)
        return self.parse_listings_from_json(data)
    
    def _collect_via_html(
        self,
        municipality_key: str,
        num_sales: int
    ) -> list[RedfinListing]:
        """Collect sales via HTML scraping."""
        url = self.get_sold_listings_url(municipality_key)
        response = self._make_request(url)
        
        soup = BeautifulSoup(response.text, 'lxml')
        return self.parse_listing_from_html(soup)
    
    def collect_all_municipalities(
        self,
        municipality_keys: Optional[list[str]] = None,
        num_sales_each: int = 50
    ) -> dict[str, list[RedfinListing]]:
        """
        Collect sales for multiple municipalities.
        
        Args:
            municipality_keys: List of municipalities (default: all configured)
            num_sales_each: Sales to collect per municipality
            
        Returns:
            Dict of municipality -> list of listings
        """
        keys = municipality_keys or list(self.CITY_SLUGS.keys())
        
        results = {}
        for key in keys:
            try:
                results[key] = self.collect_recent_sales(key, num_sales_each)
                time.sleep(2)  # Polite delay between municipalities
            except Exception as e:
                print(f"Failed to collect {key}: {e}")
                results[key] = []
        
        return results
    
    def save_to_csv(
        self,
        listings: list[RedfinListing],
        filename: str,
        output_dir: Optional[Path] = None
    ) -> Path:
        """
        Save listings to CSV file.
        
        Args:
            listings: List of RedfinListing objects
            filename: Output filename
            output_dir: Output directory (default: data/raw/sales)
            
        Returns:
            Path to saved file
        """
        import pandas as pd
        
        output_dir = output_dir or SALES_DATA_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        filepath = output_dir / filename
        
        # Convert to DataFrame
        data = []
        for l in listings:
            data.append({
                'address': l.address,
                'city': l.city,
                'state': l.state,
                'zip_code': l.zip_code,
                'sale_price': l.price,
                'sqft': l.sqft,
                'lot_sqft': l.lot_sqft,
                'bedrooms': l.beds,
                'bathrooms': l.baths,
                'year_built': l.year_built,
                'sale_date': l.sold_date,
                'property_type': l.property_type,
                'url': l.url,
                'annual_taxes': l.annual_tax,
                'assessed_value': l.tax_assessed_value,
                'source': 'redfin',
                'collection_date': date.today().isoformat(),
            })
        
        df = pd.DataFrame(data)
        df.to_csv(filepath, index=False)
        
        print(f"Saved {len(listings)} listings to {filepath}")
        return filepath


# =============================================================================
# Alternative: Manual Data Entry Helper
# =============================================================================

def create_manual_entry_template(municipality_key: str, output_dir: Optional[Path] = None) -> Path:
    """
    Create a CSV template for manual data entry.
    
    Use this when scraping isn't working or you want to
    manually enter data from Redfin.
    """
    import pandas as pd
    
    output_dir = output_dir or SALES_DATA_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    
    filepath = output_dir / f"{municipality_key}_template.csv"
    
    columns = [
        'address',
        'city', 
        'state',
        'zip_code',
        'sale_price',
        'sqft',
        'lot_sqft',
        'bedrooms',
        'bathrooms',
        'year_built',
        'sale_date',
        'property_type',
        'url',
        'annual_taxes',
        'assessed_value',
    ]
    
    # Create with example row
    muni = get_municipality(municipality_key) if municipality_key in MUNICIPALITIES else None
    
    df = pd.DataFrame([{
        'address': '123 Example St',
        'city': muni.name if muni else municipality_key.title(),
        'state': 'NY',
        'zip_code': '10708',
        'sale_price': 800000,
        'sqft': 2000,
        'lot_sqft': 8000,
        'bedrooms': 3,
        'bathrooms': 2.5,
        'year_built': 1950,
        'sale_date': '2024-01-15',
        'property_type': 'Single Family',
        'url': 'https://www.redfin.com/...',
        'annual_taxes': 25000,
        'assessed_value': 7000,
    }], columns=columns)
    
    df.to_csv(filepath, index=False)
    print(f"Created template at {filepath}")
    print("Fill in with actual sales data from Redfin")
    
    return filepath


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Demo the scraper
    scraper = RedfinScraper()
    
    # Create templates for manual entry (always works)
    print("Creating data entry templates...")
    for muni in ['bronxville', 'eastchester_unincorp', 'tuckahoe', 'scarsdale', 'larchmont']:
        create_manual_entry_template(muni)
    
    print("\n" + "="*60)
    print("To collect live data, uncomment the code below.")
    print("Note: Web scraping may be blocked or rate-limited.")
    print("="*60)
    
    # Uncomment to try live scraping:
    # listings = scraper.collect_recent_sales('bronxville', num_sales=10)
    # if listings:
    #     scraper.save_to_csv(listings, 'bronxville_sales.csv')
    #     for l in listings[:5]:
    #         print(f"{l.address}: ${l.price:,.0f}, {l.sqft:.0f} sqft")


