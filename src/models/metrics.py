"""
Metrics Calculator for municipality-level analysis.

Aggregates property data to compute comparative metrics
across municipalities.
"""

from dataclasses import dataclass, field
from typing import Optional
from statistics import mean, median, stdev
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.property import SaleRecord, SaleDataset, PropertyMetrics
from models.tax_calculator import TaxCalculator, TaxBreakdown


@dataclass
class MunicipalityMetrics:
    """
    Aggregated metrics for a municipality based on recent sales.
    
    Provides summary statistics for comparing areas.
    """
    municipality: str
    sample_size: int
    
    # Value metrics ($/sqft)
    value_per_sqft_mean: float = 0.0
    value_per_sqft_median: float = 0.0
    value_per_sqft_std: float = 0.0
    value_per_sqft_min: float = 0.0
    value_per_sqft_max: float = 0.0
    
    # Tax metrics ($/sqft)
    tax_per_sqft_mean: float = 0.0
    tax_per_sqft_median: float = 0.0
    tax_per_sqft_std: float = 0.0
    
    # Effective tax rate (%)
    effective_rate_mean: float = 0.0
    effective_rate_median: float = 0.0
    
    # Price metrics
    sale_price_mean: float = 0.0
    sale_price_median: float = 0.0
    sqft_mean: float = 0.0
    sqft_median: float = 0.0
    
    # Tax efficiency (lower is better)
    tax_efficiency_ratio: float = 0.0
    
    # Raw data for further analysis
    _records: list[SaleRecord] = field(default_factory=list, repr=False)
    
    @property
    def value_range(self) -> str:
        """Human-readable value range."""
        return f"${self.value_per_sqft_min:.0f} - ${self.value_per_sqft_max:.0f}/sqft"
    
    @property
    def monthly_tax_typical(self) -> float:
        """Typical monthly tax for median-priced home."""
        return (self.sale_price_median * self.effective_rate_median / 100) / 12
    
    def to_dict(self) -> dict:
        """Convert to dictionary for DataFrame."""
        return {
            'municipality': self.municipality,
            'sample_size': self.sample_size,
            'value_per_sqft_mean': self.value_per_sqft_mean,
            'value_per_sqft_median': self.value_per_sqft_median,
            'value_per_sqft_std': self.value_per_sqft_std,
            'value_per_sqft_min': self.value_per_sqft_min,
            'value_per_sqft_max': self.value_per_sqft_max,
            'tax_per_sqft_mean': self.tax_per_sqft_mean,
            'tax_per_sqft_median': self.tax_per_sqft_median,
            'tax_per_sqft_std': self.tax_per_sqft_std,
            'effective_rate_mean': self.effective_rate_mean,
            'effective_rate_median': self.effective_rate_median,
            'sale_price_mean': self.sale_price_mean,
            'sale_price_median': self.sale_price_median,
            'sqft_mean': self.sqft_mean,
            'sqft_median': self.sqft_median,
            'tax_efficiency_ratio': self.tax_efficiency_ratio,
            'monthly_tax_typical': self.monthly_tax_typical,
        }
    
    def __str__(self) -> str:
        """Pretty print metrics."""
        return f"""
Municipality Metrics: {self.municipality}
{'='*50}
Sample Size: {self.sample_size} sales

VALUE PER SQFT:
  Mean:   ${self.value_per_sqft_mean:,.0f}
  Median: ${self.value_per_sqft_median:,.0f}
  Range:  {self.value_range}
  Std Dev: ${self.value_per_sqft_std:,.0f}

TAX PER SQFT:
  Mean:   ${self.tax_per_sqft_mean:,.2f}
  Median: ${self.tax_per_sqft_median:,.2f}

EFFECTIVE TAX RATE:
  Mean:   {self.effective_rate_mean:.2f}%
  Median: {self.effective_rate_median:.2f}%

SALE PRICES:
  Mean:   ${self.sale_price_mean:,.0f}
  Median: ${self.sale_price_median:,.0f}

TAX EFFICIENCY:
  Ratio: {self.tax_efficiency_ratio:.2f} (lower is better)
  Typical Monthly Tax: ${self.monthly_tax_typical:,.0f}
"""


class MetricsCalculator:
    """
    Calculator for aggregating property metrics by municipality.
    
    Takes raw sale records and computes comparative statistics.
    
    Example:
        >>> calc = MetricsCalculator()
        >>> sales = load_sales_data()  # Your sale records
        >>> metrics = calc.calculate_municipality_metrics(sales, 'bronxville')
        >>> print(metrics)
    """
    
    def __init__(self, tax_calculator: Optional[TaxCalculator] = None):
        """Initialize with optional custom tax calculator."""
        self.tax_calc = tax_calculator or TaxCalculator()
    
    def calculate_municipality_metrics(
        self,
        records: list[SaleRecord],
        municipality: str
    ) -> MunicipalityMetrics:
        """
        Calculate aggregate metrics for a municipality from sale records.
        
        Args:
            records: List of SaleRecord objects
            municipality: Municipality key for filtering
            
        Returns:
            MunicipalityMetrics with computed statistics
        """
        # Filter to municipality
        filtered = [r for r in records if r.municipality == municipality]
        
        if not filtered:
            return MunicipalityMetrics(
                municipality=municipality,
                sample_size=0
            )
        
        # Extract values
        values_per_sqft = [r.price_per_sqft for r in filtered]
        taxes_per_sqft = [r.tax_per_sqft for r in filtered if r.annual_taxes > 0]
        effective_rates = [r.effective_tax_rate for r in filtered if r.annual_taxes > 0]
        prices = [r.sale_price for r in filtered]
        sqfts = [r.sqft for r in filtered]
        
        # Handle case where we have no tax data
        if not taxes_per_sqft:
            # Estimate taxes using calculator
            for r in filtered:
                breakdown = self.tax_calc.calculate_from_market_value(
                    r.sale_price, municipality
                )
                taxes_per_sqft.append(breakdown.total / r.sqft)
                effective_rates.append(breakdown.effective_rate)
        
        # Calculate statistics
        metrics = MunicipalityMetrics(
            municipality=municipality,
            sample_size=len(filtered),
            
            # Value per sqft
            value_per_sqft_mean=mean(values_per_sqft),
            value_per_sqft_median=median(values_per_sqft),
            value_per_sqft_std=stdev(values_per_sqft) if len(values_per_sqft) > 1 else 0,
            value_per_sqft_min=min(values_per_sqft),
            value_per_sqft_max=max(values_per_sqft),
            
            # Tax per sqft
            tax_per_sqft_mean=mean(taxes_per_sqft) if taxes_per_sqft else 0,
            tax_per_sqft_median=median(taxes_per_sqft) if taxes_per_sqft else 0,
            tax_per_sqft_std=stdev(taxes_per_sqft) if len(taxes_per_sqft) > 1 else 0,
            
            # Effective rate
            effective_rate_mean=mean(effective_rates) if effective_rates else 0,
            effective_rate_median=median(effective_rates) if effective_rates else 0,
            
            # Prices
            sale_price_mean=mean(prices),
            sale_price_median=median(prices),
            sqft_mean=mean(sqfts),
            sqft_median=median(sqfts),
            
            _records=filtered
        )
        
        # Calculate tax efficiency ratio
        if metrics.value_per_sqft_median > 0:
            metrics.tax_efficiency_ratio = (
                metrics.tax_per_sqft_median / metrics.value_per_sqft_median
            ) * 1000
        
        return metrics
    
    def calculate_all_metrics(
        self,
        records: list[SaleRecord],
        municipalities: Optional[list[str]] = None
    ) -> dict[str, MunicipalityMetrics]:
        """
        Calculate metrics for multiple municipalities.
        
        Args:
            records: All sale records
            municipalities: List of municipality keys (default: infer from data)
            
        Returns:
            Dict of municipality -> MunicipalityMetrics
        """
        if municipalities is None:
            municipalities = list(set(r.municipality for r in records))
        
        return {
            muni: self.calculate_municipality_metrics(records, muni)
            for muni in municipalities
        }
    
    def create_comparison_table(
        self,
        metrics: dict[str, MunicipalityMetrics]
    ):
        """
        Create a pandas DataFrame comparison table.
        
        Returns DataFrame sorted by value per sqft (descending).
        """
        import pandas as pd
        
        data = [m.to_dict() for m in metrics.values()]
        df = pd.DataFrame(data)
        
        # Sort by value per sqft descending
        df = df.sort_values('value_per_sqft_median', ascending=False)
        
        return df
    
    def rank_by_tax_efficiency(
        self,
        metrics: dict[str, MunicipalityMetrics]
    ) -> list[tuple[str, float]]:
        """
        Rank municipalities by tax efficiency (lowest ratio = best).
        
        Returns list of (municipality, efficiency_ratio) tuples.
        """
        rankings = [
            (muni, m.tax_efficiency_ratio)
            for muni, m in metrics.items()
            if m.tax_efficiency_ratio > 0
        ]
        return sorted(rankings, key=lambda x: x[1])
    
    def value_vs_tax_analysis(
        self,
        metrics: dict[str, MunicipalityMetrics]
    ) -> dict:
        """
        Analyze the relationship between value and tax burden.
        
        Returns analysis dict with:
        - correlation: Correlation between value/sqft and tax/sqft
        - best_value: Municipality with highest value per tax dollar
        - premium_analysis: How much extra you pay in premium areas
        """
        import numpy as np
        
        values = []
        taxes = []
        munis = []
        
        for muni, m in metrics.items():
            if m.sample_size > 0:
                values.append(m.value_per_sqft_median)
                taxes.append(m.tax_per_sqft_median)
                munis.append(muni)
        
        if len(values) < 2:
            return {'error': 'Insufficient data for analysis'}
        
        # Calculate correlation
        correlation = np.corrcoef(values, taxes)[0, 1]
        
        # Find best value (highest value/tax ratio)
        value_per_tax = [v/t for v, t in zip(values, taxes)]
        best_idx = np.argmax(value_per_tax)
        
        # Calculate premium (how much more Bronxville costs vs average)
        avg_value = np.mean(values)
        
        return {
            'correlation': correlation,
            'interpretation': (
                'Positive correlation means higher-value areas have higher taxes per sqft'
                if correlation > 0 else
                'Negative correlation means higher-value areas have lower taxes per sqft'
            ),
            'best_value_municipality': munis[best_idx],
            'best_value_ratio': value_per_tax[best_idx],
            'average_value_per_sqft': avg_value,
            'municipalities_above_average': [
                m for m, v in zip(munis, values) if v > avg_value
            ],
        }


# =============================================================================
# Utility Functions
# =============================================================================

def calculate_property_metrics(
    sale: SaleRecord,
    tax_calculator: Optional[TaxCalculator] = None
) -> PropertyMetrics:
    """
    Calculate detailed metrics for a single property sale.
    
    Args:
        sale: SaleRecord to analyze
        tax_calculator: Optional TaxCalculator (creates default if not provided)
        
    Returns:
        PropertyMetrics with all computed values
    """
    calc = tax_calculator or TaxCalculator()
    
    # Get tax breakdown
    breakdown = calc.calculate_from_market_value(
        sale.sale_price, 
        sale.municipality
    )
    
    return PropertyMetrics(
        municipality=sale.municipality,
        address=sale.address,
        market_value=sale.sale_price,
        sqft=sale.sqft,
        value_per_sqft=sale.price_per_sqft,
        total_annual_tax=breakdown.total,
        tax_per_sqft=breakdown.total / sale.sqft,
        effective_tax_rate=breakdown.effective_rate,
        county_tax=breakdown.county_tax,
        town_tax=breakdown.town_tax,
        village_tax=breakdown.village_tax,
        school_tax=breakdown.school_tax,
        other_tax=(
            breakdown.fire_district_tax + 
            breakdown.library_tax + 
            breakdown.special_district_tax
        ),
    )


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    from datetime import date
    from models.property import SaleRecord
    
    # Create sample data
    sample_sales = [
        SaleRecord(
            address="123 Main St",
            municipality="bronxville",
            sqft=2500,
            sale_price=1_500_000,
            sale_date=date(2024, 6, 1),
            assessed_value=1_500_000,  # 100% RAR
            annual_taxes=42_000,
        ),
        SaleRecord(
            address="456 Oak Ave",
            municipality="bronxville",
            sqft=2000,
            sale_price=1_200_000,
            sale_date=date(2024, 7, 15),
            assessed_value=1_200_000,
            annual_taxes=34_000,
        ),
        SaleRecord(
            address="789 Elm Rd",
            municipality="eastchester_unincorp",
            sqft=2200,
            sale_price=850_000,
            sale_date=date(2024, 5, 20),
            assessed_value=7_480,  # 0.88% RAR
            annual_taxes=35_000,
        ),
        SaleRecord(
            address="321 Pine St",
            municipality="eastchester_unincorp",
            sqft=1800,
            sale_price=720_000,
            sale_date=date(2024, 8, 1),
            assessed_value=6_336,
            annual_taxes=29_000,
        ),
    ]
    
    # Calculate metrics
    calc = MetricsCalculator()
    all_metrics = calc.calculate_all_metrics(sample_sales)
    
    print("=" * 60)
    print("MUNICIPALITY COMPARISON")
    print("=" * 60)
    
    for muni, metrics in all_metrics.items():
        print(metrics)
        print()
    
    # Create comparison table
    df = calc.create_comparison_table(all_metrics)
    print("\nComparison Table:")
    print(df[['municipality', 'sample_size', 'value_per_sqft_median', 
              'tax_per_sqft_median', 'tax_efficiency_ratio']].to_string())
    
    # Tax efficiency ranking
    print("\n\nTax Efficiency Ranking (lower = better):")
    rankings = calc.rank_by_tax_efficiency(all_metrics)
    for i, (muni, ratio) in enumerate(rankings, 1):
        print(f"  {i}. {muni}: {ratio:.2f}")


