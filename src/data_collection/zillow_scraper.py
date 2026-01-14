"""
Zillow/Realtor Data Scraper for Home Sales.

Uses publicly available data sources to collect recent home sales
with price, square footage, and property details.
"""

import json
import re
import time
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional, List
from urllib.parse import urlencode, quote
import random

import requests
from bs4 import BeautifulSoup

import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import SALES_DATA_DIR


@dataclass
class HomeSale:
    """Represents a home sale record."""
    address: str
    city: str
    state: str = "NY"
    zip_code: str = ""
    sale_price: float = 0.0
    sqft: float = 0.0
    lot_sqft: Optional[float] = None
    bedrooms: int = 0
    bathrooms: float = 0.0
    year_built: Optional[int] = None
    sale_date: Optional[str] = None
    property_type: str = "Single Family"
    
    # Tax info
    annual_taxes: Optional[float] = None
    assessed_value: Optional[float] = None
    
    # Metadata
    source: str = "zillow"
    url: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


class ZillowScraper:
    """
    Scraper for Zillow recently sold homes data.
    
    Uses Zillow's search API to find recently sold properties.
    """
    
    BASE_URL = "https://www.zillow.com"
    
    # Zillow region IDs for Westchester municipalities
    REGION_IDS = {
        'bronxville': '52869',
        'eastchester': '52996',
        'tuckahoe': '54574',
        'scarsdale': '54198',
        'larchmont': '53380',
        'mamaroneck': '53477',
        'pelham': '53870',
        'pelham_manor': '269196',
        'rye': '54146',
        'new_rochelle': '53666',
    }
    
    # Zip codes for each municipality
    ZIP_CODES = {
        'bronxville': ['10708'],
        'eastchester': ['10709', '10707'],
        'tuckahoe': ['10707'],
        'scarsdale': ['10583'],
        'larchmont': ['10538'],
        'mamaroneck': ['10543'],
        'pelham': ['10803'],
        'pelham_manor': ['10803'],
        'rye': ['10580'],
        'new_rochelle': ['10801', '10802', '10804', '10805'],
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        self._last_request = 0
    
    def _rate_limit(self, min_delay: float = 2.0):
        """Enforce rate limiting between requests."""
        elapsed = time.time() - self._last_request
        if elapsed < min_delay:
            sleep_time = min_delay - elapsed + random.uniform(0.5, 1.5)
            time.sleep(sleep_time)
        self._last_request = time.time()
    
    def get_sold_url(self, municipality: str) -> str:
        """Get Zillow sold homes URL for a municipality."""
        city_slug = municipality.replace('_', '-').lower()
        return f"{self.BASE_URL}/{city_slug}-ny/sold/"
    
    def search_sold_homes_api(self, municipality: str, limit: int = 50) -> List[HomeSale]:
        """
        Search for sold homes using Zillow's internal API.
        
        Note: Zillow's API may block automated requests.
        This is a best-effort approach.
        """
        results = []
        
        # Try to get region ID
        region_id = self.REGION_IDS.get(municipality.replace('_unincorp', '').replace('_village', ''))
        
        if not region_id:
            print(f"Warning: No region ID for {municipality}, trying zip code search")
            return self.search_by_zip(municipality, limit)
        
        # Zillow search API endpoint
        api_url = f"{self.BASE_URL}/search/GetSearchPageState.htm"
        
        search_params = {
            'searchQueryState': json.dumps({
                'pagination': {},
                'usersSearchTerm': municipality.replace('_', ' ').title() + ', NY',
                'mapBounds': {
                    'west': -73.9,
                    'east': -73.7,
                    'south': 40.9,
                    'north': 41.1,
                },
                'regionSelection': [{'regionId': int(region_id), 'regionType': 6}],
                'isMapVisible': False,
                'filterState': {
                    'sortSelection': {'value': 'days'},
                    'isRecentlySold': {'value': True},
                    'isForSaleByAgent': {'value': False},
                    'isForSaleByOwner': {'value': False},
                    'isNewConstruction': {'value': False},
                    'isComingSoon': {'value': False},
                    'isAuction': {'value': False},
                    'isForSaleForeclosure': {'value': False},
                },
                'isListVisible': True,
            }),
            'wants': json.dumps({
                'cat1': ['listResults'],
            }),
            'requestId': 1,
        }
        
        try:
            self._rate_limit()
            response = self.session.get(api_url, params=search_params, timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = self._parse_zillow_response(data, municipality)
            else:
                print(f"API request failed with status {response.status_code}")
                
        except Exception as e:
            print(f"API search failed: {e}")
        
        return results[:limit]
    
    def search_by_zip(self, municipality: str, limit: int = 50) -> List[HomeSale]:
        """Search sold homes by zip code."""
        results = []
        
        zip_codes = self.ZIP_CODES.get(
            municipality.replace('_unincorp', '').replace('_village', ''),
            []
        )
        
        for zip_code in zip_codes:
            url = f"{self.BASE_URL}/homes/recently_sold/{zip_code}_rb/"
            
            try:
                self._rate_limit()
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    homes = self._parse_html_listings(response.text, municipality)
                    results.extend(homes)
                    
                    if len(results) >= limit:
                        break
                        
            except Exception as e:
                print(f"Error fetching {url}: {e}")
        
        return results[:limit]
    
    def _parse_zillow_response(self, data: dict, municipality: str) -> List[HomeSale]:
        """Parse Zillow API JSON response."""
        results = []
        
        try:
            search_results = data.get('cat1', {}).get('searchResults', {}).get('listResults', [])
            
            for item in search_results:
                try:
                    home = HomeSale(
                        address=item.get('address', 'Unknown'),
                        city=municipality.replace('_', ' ').title(),
                        zip_code=str(item.get('addressZipcode', '')),
                        sale_price=float(item.get('unformattedPrice', 0) or item.get('price', 0)),
                        sqft=float(item.get('area', 0) or 0),
                        lot_sqft=float(item.get('lotAreaValue', 0) or 0) if item.get('lotAreaValue') else None,
                        bedrooms=int(item.get('beds', 0) or 0),
                        bathrooms=float(item.get('baths', 0) or 0),
                        property_type=item.get('hdpData', {}).get('homeInfo', {}).get('homeType', 'Single Family'),
                        url=item.get('detailUrl', ''),
                        source='zillow',
                    )
                    
                    if home.sale_price > 0 and home.sqft > 0:
                        results.append(home)
                        
                except Exception as e:
                    continue
                    
        except Exception as e:
            print(f"Error parsing Zillow response: {e}")
        
        return results
    
    def _parse_html_listings(self, html: str, municipality: str) -> List[HomeSale]:
        """Parse home listings from HTML page."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find listing cards
        cards = soup.find_all('article', {'data-test': 'property-card'})
        
        if not cards:
            # Try alternative selector
            cards = soup.find_all('div', class_=re.compile(r'ListItem|property-card|StyledPropertyCard'))
        
        for card in cards:
            try:
                home = self._parse_card(card, municipality)
                if home and home.sale_price > 0:
                    results.append(home)
            except Exception:
                continue
        
        return results
    
    def _parse_card(self, card, municipality: str) -> Optional[HomeSale]:
        """Parse a single listing card."""
        # Extract price
        price_elem = card.find('span', {'data-test': 'property-card-price'})
        if not price_elem:
            price_elem = card.find('span', class_=re.compile(r'Price|price'))
        
        price = 0.0
        if price_elem:
            price_text = price_elem.get_text().replace('$', '').replace(',', '').strip()
            try:
                price = float(re.sub(r'[^\d.]', '', price_text))
            except ValueError:
                pass
        
        if price == 0:
            return None
        
        # Extract address
        address_elem = card.find('address') or card.find('a', {'data-test': 'property-card-link'})
        address = address_elem.get_text().strip() if address_elem else "Unknown"
        
        # Extract beds/baths/sqft
        beds, baths, sqft = 0, 0.0, 0.0
        
        stats = card.find_all('b') + card.find_all('span', class_=re.compile(r'bed|bath|sqft', re.I))
        
        for stat in stats:
            text = stat.get_text().lower()
            parent_text = stat.parent.get_text().lower() if stat.parent else ""
            
            if 'bd' in text or 'bed' in parent_text:
                try:
                    beds = int(re.search(r'\d+', text).group())
                except:
                    pass
            elif 'ba' in text or 'bath' in parent_text:
                try:
                    baths = float(re.search(r'[\d.]+', text).group())
                except:
                    pass
            elif 'sqft' in text or 'sq ft' in parent_text:
                try:
                    sqft = float(re.sub(r'[^\d]', '', text))
                except:
                    pass
        
        # Get URL
        link = card.find('a', href=True)
        url = link['href'] if link else ""
        if url and not url.startswith('http'):
            url = f"{self.BASE_URL}{url}"
        
        return HomeSale(
            address=address.split(',')[0] if ',' in address else address,
            city=municipality.replace('_', ' ').title(),
            sale_price=price,
            sqft=sqft,
            bedrooms=beds,
            bathrooms=baths,
            url=url,
            source='zillow',
        )
    
    def collect_sales(self, municipality: str, num_sales: int = 50) -> List[HomeSale]:
        """
        Collect recent home sales for a municipality.
        
        Tries multiple methods in order of preference.
        """
        print(f"Collecting sales for {municipality}...")
        
        results = []
        
        # Try API first
        try:
            results = self.search_sold_homes_api(municipality, num_sales)
        except Exception as e:
            print(f"  API method failed: {e}")
        
        # Fall back to zip code search
        if len(results) < num_sales:
            try:
                zip_results = self.search_by_zip(municipality, num_sales - len(results))
                results.extend(zip_results)
            except Exception as e:
                print(f"  Zip search failed: {e}")
        
        print(f"  Found {len(results)} sales")
        return results[:num_sales]


class RealtorScraper:
    """
    Alternative scraper using Realtor.com data.
    """
    
    BASE_URL = "https://www.realtor.com"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        })
        self._last_request = 0
    
    def _rate_limit(self):
        elapsed = time.time() - self._last_request
        if elapsed < 2:
            time.sleep(2 - elapsed + random.uniform(0.5, 1))
        self._last_request = time.time()
    
    def get_sold_url(self, city: str, state: str = "NY") -> str:
        """Get Realtor.com sold listings URL."""
        city_slug = city.lower().replace(' ', '-')
        return f"{self.BASE_URL}/realestateandhomes-search/{city_slug}_{state}/show-recently-sold"
    
    def collect_sales(self, municipality: str, num_sales: int = 50) -> List[HomeSale]:
        """Collect sales from Realtor.com."""
        results = []
        city = municipality.replace('_unincorp', '').replace('_village', '').replace('_', ' ').title()
        
        url = self.get_sold_url(city)
        
        try:
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            
            if response.status_code == 200:
                results = self._parse_listings(response.text, municipality)
        except Exception as e:
            print(f"Realtor.com error: {e}")
        
        return results[:num_sales]
    
    def _parse_listings(self, html: str, municipality: str) -> List[HomeSale]:
        """Parse Realtor.com listings."""
        results = []
        soup = BeautifulSoup(html, 'html.parser')
        
        # Find property cards
        cards = soup.find_all('div', {'data-testid': 'property-card'})
        
        for card in cards:
            try:
                # Price
                price_elem = card.find('span', {'data-testid': 'card-price'})
                price = 0.0
                if price_elem:
                    price_text = price_elem.get_text().replace('$', '').replace(',', '')
                    price = float(re.sub(r'[^\d]', '', price_text))
                
                if price == 0:
                    continue
                
                # Address
                address_elem = card.find('div', {'data-testid': 'card-address'})
                address = address_elem.get_text().strip() if address_elem else "Unknown"
                
                # Beds/baths/sqft
                beds, baths, sqft = 0, 0.0, 0.0
                
                meta = card.find('ul', {'data-testid': 'card-meta'})
                if meta:
                    items = meta.find_all('li')
                    for item in items:
                        text = item.get_text().lower()
                        if 'bed' in text:
                            beds = int(re.search(r'\d+', text).group())
                        elif 'bath' in text:
                            baths = float(re.search(r'[\d.]+', text).group())
                        elif 'sqft' in text:
                            sqft = float(re.sub(r'[^\d]', '', text))
                
                results.append(HomeSale(
                    address=address.split(',')[0],
                    city=municipality.replace('_', ' ').title(),
                    sale_price=price,
                    sqft=sqft if sqft > 0 else 2000,  # Default if not found
                    bedrooms=beds,
                    bathrooms=baths,
                    source='realtor',
                ))
                
            except Exception:
                continue
        
        return results


def save_sales_data(sales: List[HomeSale], municipality: str) -> Path:
    """Save sales data to CSV."""
    import pandas as pd
    
    SALES_DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = SALES_DATA_DIR / f"{municipality}_sales.csv"
    
    data = [s.to_dict() for s in sales]
    df = pd.DataFrame(data)
    df.to_csv(filepath, index=False)
    
    print(f"Saved {len(sales)} sales to {filepath}")
    return filepath


def collect_all_sales(municipalities: List[str] = None, num_per_muni: int = 50) -> dict:
    """
    Collect sales data for all municipalities.
    
    Returns dict of municipality -> List[HomeSale]
    """
    if municipalities is None:
        municipalities = [
            'bronxville', 'eastchester', 'tuckahoe',
            'scarsdale', 'larchmont', 'mamaroneck',
            'pelham', 'pelham_manor'
        ]
    
    zillow = ZillowScraper()
    realtor = RealtorScraper()
    
    all_results = {}
    
    print("=" * 60)
    print("COLLECTING HOME SALES DATA")
    print("=" * 60)
    
    for muni in municipalities:
        print(f"\n{muni}:")
        
        # Try Zillow first
        results = zillow.collect_sales(muni, num_per_muni)
        
        # Fall back to Realtor if needed
        if len(results) < 10:
            print(f"  Trying Realtor.com...")
            realtor_results = realtor.collect_sales(muni, num_per_muni - len(results))
            results.extend(realtor_results)
        
        if results:
            save_sales_data(results, muni)
        
        all_results[muni] = results
        
        # Be polite
        time.sleep(3)
    
    # Summary
    print("\n" + "=" * 60)
    print("COLLECTION SUMMARY")
    print("=" * 60)
    
    total = 0
    for muni, sales in all_results.items():
        print(f"  {muni:<25} {len(sales):>5} sales")
        total += len(sales)
    
    print(f"\n  TOTAL: {total} sales collected")
    
    return all_results


if __name__ == "__main__":
    collect_all_sales()


