"""
Tax Calculator Engine.

Calculates property taxes across different Westchester County municipalities,
handling the complexity of different assessment ratios, overlapping tax
jurisdictions, and varying rate structures.
"""

from dataclasses import dataclass
from typing import Optional
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import Municipality, MUNICIPALITIES, get_municipality, TaxRates


@dataclass
class TaxBreakdown:
    """
    Detailed breakdown of property tax components.
    
    All values are annual dollar amounts.
    """
    municipality: str
    assessed_value: float
    market_value: float
    
    # Tax components
    county_tax: float = 0.0
    town_tax: float = 0.0
    village_tax: float = 0.0
    school_tax: float = 0.0
    fire_district_tax: float = 0.0
    library_tax: float = 0.0
    special_district_tax: float = 0.0
    
    @property
    def total(self) -> float:
        """Total annual property tax."""
        return sum([
            self.county_tax,
            self.town_tax,
            self.village_tax,
            self.school_tax,
            self.fire_district_tax,
            self.library_tax,
            self.special_district_tax
        ])
    
    @property
    def effective_rate(self) -> float:
        """Effective tax rate as percentage of market value."""
        if self.market_value == 0:
            return 0.0
        return (self.total / self.market_value) * 100
    
    @property
    def school_percentage(self) -> float:
        """School tax as percentage of total."""
        if self.total == 0:
            return 0.0
        return (self.school_tax / self.total) * 100
    
    @property
    def municipal_percentage(self) -> float:
        """Town + Village tax as percentage of total."""
        if self.total == 0:
            return 0.0
        return ((self.town_tax + self.village_tax) / self.total) * 100
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            'municipality': self.municipality,
            'assessed_value': self.assessed_value,
            'market_value': self.market_value,
            'county_tax': self.county_tax,
            'town_tax': self.town_tax,
            'village_tax': self.village_tax,
            'school_tax': self.school_tax,
            'fire_district_tax': self.fire_district_tax,
            'library_tax': self.library_tax,
            'special_district_tax': self.special_district_tax,
            'total_tax': self.total,
            'effective_rate': self.effective_rate,
            'school_percentage': self.school_percentage,
        }
    
    def __str__(self) -> str:
        """Pretty print tax breakdown."""
        lines = [
            f"Tax Breakdown for {self.municipality}",
            f"{'='*50}",
            f"Market Value:     ${self.market_value:>15,.2f}",
            f"Assessed Value:   ${self.assessed_value:>15,.2f}",
            f"",
            f"Tax Components:",
            f"  County:         ${self.county_tax:>15,.2f}",
            f"  Town:           ${self.town_tax:>15,.2f}",
            f"  Village:        ${self.village_tax:>15,.2f}",
            f"  School:         ${self.school_tax:>15,.2f}",
            f"  Fire District:  ${self.fire_district_tax:>15,.2f}",
            f"  Library:        ${self.library_tax:>15,.2f}",
            f"  Special Dist:   ${self.special_district_tax:>15,.2f}",
            f"  {'-'*35}",
            f"  TOTAL:          ${self.total:>15,.2f}",
            f"",
            f"Effective Rate:   {self.effective_rate:>15.2f}%",
            f"School % of Tax:  {self.school_percentage:>15.1f}%",
        ]
        return "\n".join(lines)


class TaxCalculator:
    """
    Calculator for property taxes across Westchester municipalities.
    
    Handles the complexity of:
    - Different Residential Assessment Ratios (RAR)
    - Overlapping tax jurisdictions (town/village/county)
    - Multiple school districts
    - Various special districts
    
    Example:
        >>> calc = TaxCalculator()
        >>> # For a $1M home in Bronxville (100% RAR)
        >>> breakdown = calc.calculate_from_market_value(1_000_000, 'bronxville')
        >>> print(f"Total tax: ${breakdown.total:,.2f}")
        
        >>> # For a home in Eastchester with known assessed value
        >>> breakdown = calc.calculate_from_assessed_value(8800, 'eastchester_unincorp')
        >>> print(breakdown)
    """
    
    def __init__(self, municipalities: Optional[dict] = None):
        """
        Initialize calculator with municipality configurations.
        
        Args:
            municipalities: Override default municipality configs (for testing)
        """
        self.municipalities = municipalities or MUNICIPALITIES
    
    def get_municipality(self, key: str) -> Municipality:
        """Get municipality configuration."""
        if key not in self.municipalities:
            raise ValueError(
                f"Unknown municipality: {key}. "
                f"Valid options: {list(self.municipalities.keys())}"
            )
        return self.municipalities[key]
    
    def calculate_from_market_value(
        self, 
        market_value: float, 
        municipality_key: str
    ) -> TaxBreakdown:
        """
        Calculate taxes given a market value (e.g., sale price).
        
        Args:
            market_value: Property market value in dollars
            municipality_key: Municipality identifier
            
        Returns:
            TaxBreakdown with all tax components
        """
        muni = self.get_municipality(municipality_key)
        assessed_value = muni.market_to_assessed(market_value)
        return self._calculate(assessed_value, market_value, muni)
    
    def calculate_from_assessed_value(
        self,
        assessed_value: float,
        municipality_key: str
    ) -> TaxBreakdown:
        """
        Calculate taxes given an assessed value (from tax bill).
        
        Args:
            assessed_value: Property assessed value in dollars
            municipality_key: Municipality identifier
            
        Returns:
            TaxBreakdown with all tax components
        """
        muni = self.get_municipality(municipality_key)
        market_value = muni.assessed_to_market(assessed_value)
        return self._calculate(assessed_value, market_value, muni)
    
    def _calculate(
        self, 
        assessed_value: float,
        market_value: float,
        municipality: Municipality
    ) -> TaxBreakdown:
        """
        Internal calculation method.
        
        Tax formula: (assessed_value / 1000) * rate_per_thousand
        """
        rates = municipality.tax_rates
        base = assessed_value / 1000  # Convert to per-$1000 basis
        
        return TaxBreakdown(
            municipality=municipality.name,
            assessed_value=assessed_value,
            market_value=market_value,
            county_tax=base * rates.county,
            town_tax=base * rates.town,
            village_tax=base * rates.village if municipality.has_village_tax else 0.0,
            school_tax=base * rates.school,
            fire_district_tax=base * rates.fire_district,
            library_tax=base * rates.library,
            special_district_tax=base * rates.special_districts,
        )
    
    def estimate_monthly_tax(
        self,
        market_value: float,
        municipality_key: str
    ) -> float:
        """
        Estimate monthly tax payment (for mortgage calculations).
        
        Args:
            market_value: Property market value
            municipality_key: Municipality identifier
            
        Returns:
            Estimated monthly tax amount
        """
        breakdown = self.calculate_from_market_value(market_value, municipality_key)
        return breakdown.total / 12
    
    def compare_municipalities(
        self,
        market_value: float,
        municipality_keys: Optional[list[str]] = None
    ) -> dict[str, TaxBreakdown]:
        """
        Compare taxes for the same market value across municipalities.
        
        Args:
            market_value: Property market value to compare
            municipality_keys: List of municipalities (default: all)
            
        Returns:
            Dict of municipality -> TaxBreakdown
        """
        keys = municipality_keys or list(self.municipalities.keys())
        return {
            key: self.calculate_from_market_value(market_value, key)
            for key in keys
        }
    
    def find_lowest_tax(
        self,
        market_value: float,
        municipality_keys: Optional[list[str]] = None
    ) -> tuple[str, TaxBreakdown]:
        """
        Find municipality with lowest tax for given market value.
        
        Args:
            market_value: Property market value
            municipality_keys: Municipalities to compare
            
        Returns:
            Tuple of (municipality_key, TaxBreakdown)
        """
        comparisons = self.compare_municipalities(market_value, municipality_keys)
        lowest_key = min(comparisons, key=lambda k: comparisons[k].total)
        return lowest_key, comparisons[lowest_key]
    
    def tax_impact_analysis(
        self,
        market_value: float,
        municipality_key: str
    ) -> dict:
        """
        Analyze tax impact with various metrics.
        
        Returns dict with:
        - breakdown: Full TaxBreakdown
        - monthly: Monthly payment
        - per_sqft: Tax per sqft (assumes 2000 sqft average)
        - vs_average: Comparison to average of all municipalities
        """
        breakdown = self.calculate_from_market_value(market_value, municipality_key)
        
        # Calculate average across all municipalities
        all_breakdowns = self.compare_municipalities(market_value)
        avg_tax = sum(b.total for b in all_breakdowns.values()) / len(all_breakdowns)
        
        return {
            'breakdown': breakdown,
            'monthly': breakdown.total / 12,
            'per_sqft_2000': breakdown.total / 2000,  # Assumes 2000 sqft
            'vs_average': breakdown.total - avg_tax,
            'vs_average_pct': ((breakdown.total / avg_tax) - 1) * 100 if avg_tax > 0 else 0,
        }


def calculate_tax_per_sqft(
    market_value: float,
    sqft: float,
    municipality_key: str,
    calculator: Optional[TaxCalculator] = None
) -> float:
    """
    Convenience function to calculate tax per square foot.
    
    Args:
        market_value: Property market value
        sqft: Property square footage
        municipality_key: Municipality identifier
        calculator: Optional TaxCalculator instance
        
    Returns:
        Annual tax per square foot
    """
    calc = calculator or TaxCalculator()
    breakdown = calc.calculate_from_market_value(market_value, municipality_key)
    return breakdown.total / sqft


# =============================================================================
# STAR Exemption Calculator
# =============================================================================

@dataclass
class STARExemption:
    """
    STAR (School Tax Relief) exemption details.
    
    Basic STAR: For owner-occupied primary residences
    Enhanced STAR: For seniors 65+ with income <= $98,700
    """
    exemption_type: str  # 'basic' or 'enhanced'
    exemption_amount: float  # Dollar reduction in assessed value
    school_tax_savings: float  # Actual dollar savings
    
    @classmethod
    def calculate_basic(cls, municipality_key: str) -> 'STARExemption':
        """
        Calculate Basic STAR exemption.
        
        Basic STAR provides ~$30,000 exemption (varies by municipality).
        """
        # STAR exemption amounts vary; this is approximate
        calc = TaxCalculator()
        muni = calc.get_municipality(municipality_key)
        
        # Basic STAR is roughly $30,000 of market value equivalent
        # But actual exemption is applied to assessed value
        exemption_market = 30_000
        exemption_assessed = exemption_market * muni.rar
        
        # Calculate school tax savings
        school_rate = muni.tax_rates.school
        savings = (exemption_assessed / 1000) * school_rate
        
        return cls(
            exemption_type='basic',
            exemption_amount=exemption_assessed,
            school_tax_savings=savings
        )


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    # Demo the calculator
    calc = TaxCalculator()
    
    # Compare a $1M home across areas
    print("=" * 60)
    print("TAX COMPARISON: $1,000,000 Home")
    print("=" * 60)
    
    test_value = 1_000_000
    
    comparisons = calc.compare_municipalities(
        test_value,
        ['eastchester_unincorp', 'bronxville', 'tuckahoe', 'scarsdale', 'larchmont']
    )
    
    # Sort by total tax
    sorted_munis = sorted(comparisons.items(), key=lambda x: x[1].total)
    
    print(f"\n{'Municipality':<30} {'Annual Tax':>15} {'Eff. Rate':>12} {'Monthly':>12}")
    print("-" * 70)
    
    for key, breakdown in sorted_munis:
        print(
            f"{breakdown.municipality:<30} "
            f"${breakdown.total:>14,.0f} "
            f"{breakdown.effective_rate:>11.2f}% "
            f"${breakdown.total/12:>11,.0f}"
        )
    
    print("\n" + "=" * 60)
    print("DETAILED BREAKDOWN: Eastchester (Unincorporated)")
    print("=" * 60)
    print(comparisons['eastchester_unincorp'])
    
    print("\n" + "=" * 60)
    print("DETAILED BREAKDOWN: Bronxville")
    print("=" * 60)
    print(comparisons['bronxville'])


