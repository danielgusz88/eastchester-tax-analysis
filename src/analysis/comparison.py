"""
Comparison Engine for cross-municipality analysis.

Generates comprehensive comparison reports between Eastchester-area
municipalities and comparable Westchester towns.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from pathlib import Path
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from config import MUNICIPALITIES, EASTCHESTER_AREA, COMPARISON_TOWNS, get_municipality
from models.property import SaleRecord, SaleDataset
from models.tax_calculator import TaxCalculator
from models.metrics import MetricsCalculator, MunicipalityMetrics


@dataclass
class ComparisonReport:
    """
    Comprehensive comparison report between municipalities.
    
    Contains metrics, rankings, and insights for comparing
    property values and tax burdens.
    """
    generated_date: date
    municipalities_compared: list[str]
    total_sales_analyzed: int
    
    # Core metrics by municipality
    metrics: dict[str, MunicipalityMetrics] = field(default_factory=dict)
    
    # Rankings
    value_ranking: list[tuple[str, float]] = field(default_factory=list)  # (muni, $/sqft)
    tax_ranking: list[tuple[str, float]] = field(default_factory=list)    # (muni, $/sqft tax)
    efficiency_ranking: list[tuple[str, float]] = field(default_factory=list)  # (muni, ratio)
    
    # Key insights
    insights: list[str] = field(default_factory=list)
    
    # Eastchester-specific analysis
    eastchester_comparison: dict = field(default_factory=dict)
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to DataFrame for display."""
        data = [m.to_dict() for m in self.metrics.values()]
        df = pd.DataFrame(data)
        return df.sort_values('value_per_sqft_median', ascending=False)
    
    def summary(self) -> str:
        """Generate text summary of report."""
        lines = [
            "=" * 70,
            "WESTCHESTER PROPERTY TAX & VALUE COMPARISON REPORT",
            f"Generated: {self.generated_date}",
            f"Municipalities: {len(self.municipalities_compared)}",
            f"Total Sales Analyzed: {self.total_sales_analyzed}",
            "=" * 70,
            "",
            "VALUE PER SQFT RANKING (Highest to Lowest):",
            "-" * 50,
        ]
        
        for i, (muni, value) in enumerate(self.value_ranking, 1):
            lines.append(f"  {i}. {muni:<25} ${value:,.0f}/sqft")
        
        lines.extend([
            "",
            "TAX PER SQFT RANKING (Lowest to Highest):",
            "-" * 50,
        ])
        
        for i, (muni, tax) in enumerate(self.tax_ranking, 1):
            lines.append(f"  {i}. {muni:<25} ${tax:,.2f}/sqft")
        
        lines.extend([
            "",
            "TAX EFFICIENCY RANKING (Best to Worst):",
            "(Lower ratio = more value for your tax dollar)",
            "-" * 50,
        ])
        
        for i, (muni, ratio) in enumerate(self.efficiency_ranking, 1):
            lines.append(f"  {i}. {muni:<25} {ratio:.2f}")
        
        if self.insights:
            lines.extend([
                "",
                "KEY INSIGHTS:",
                "-" * 50,
            ])
            for insight in self.insights:
                lines.append(f"  • {insight}")
        
        if self.eastchester_comparison:
            lines.extend([
                "",
                "EASTCHESTER AREA ANALYSIS:",
                "-" * 50,
            ])
            for key, value in self.eastchester_comparison.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)
    
    def __str__(self) -> str:
        return self.summary()


class ComparisonEngine:
    """
    Engine for generating comprehensive municipality comparisons.
    
    Coordinates between data loading, metric calculation, and
    report generation.
    
    Example:
        >>> engine = ComparisonEngine()
        >>> # Load your sales data
        >>> engine.load_data(sales_records)
        >>> # Generate full report
        >>> report = engine.generate_full_report()
        >>> print(report)
    """
    
    def __init__(
        self,
        tax_calculator: Optional[TaxCalculator] = None,
        metrics_calculator: Optional[MetricsCalculator] = None
    ):
        """Initialize with optional custom calculators."""
        self.tax_calc = tax_calculator or TaxCalculator()
        self.metrics_calc = metrics_calculator or MetricsCalculator(self.tax_calc)
        
        self.sales_data: list[SaleRecord] = []
        self._metrics_cache: dict[str, MunicipalityMetrics] = {}
    
    def load_data(self, sales: list[SaleRecord]) -> None:
        """Load sales data for analysis."""
        self.sales_data = sales
        self._metrics_cache.clear()
        print(f"Loaded {len(sales)} sales records")
    
    def load_from_dataset(self, dataset: SaleDataset) -> None:
        """Load data from SaleDataset."""
        self.load_data(dataset.records)
    
    def get_metrics(self, municipality: str) -> MunicipalityMetrics:
        """Get or calculate metrics for a municipality."""
        if municipality not in self._metrics_cache:
            self._metrics_cache[municipality] = self.metrics_calc.calculate_municipality_metrics(
                self.sales_data, municipality
            )
        return self._metrics_cache[municipality]
    
    def calculate_all_metrics(
        self,
        municipalities: Optional[list[str]] = None
    ) -> dict[str, MunicipalityMetrics]:
        """Calculate metrics for all or specified municipalities."""
        if municipalities is None:
            # Get unique municipalities from data
            municipalities = list(set(r.municipality for r in self.sales_data))
        
        return {
            muni: self.get_metrics(muni)
            for muni in municipalities
        }
    
    def generate_full_report(
        self,
        municipalities: Optional[list[str]] = None
    ) -> ComparisonReport:
        """
        Generate comprehensive comparison report.
        
        Args:
            municipalities: List of municipalities to compare
                          (default: all with data)
        
        Returns:
            ComparisonReport with all analyses
        """
        # Calculate metrics
        metrics = self.calculate_all_metrics(municipalities)
        
        # Filter out municipalities with no data
        metrics = {k: v for k, v in metrics.items() if v.sample_size > 0}
        
        if not metrics:
            return ComparisonReport(
                generated_date=date.today(),
                municipalities_compared=[],
                total_sales_analyzed=0,
                insights=["No valid sales data available"]
            )
        
        # Generate rankings
        value_ranking = sorted(
            [(m, v.value_per_sqft_median) for m, v in metrics.items()],
            key=lambda x: x[1],
            reverse=True
        )
        
        tax_ranking = sorted(
            [(m, v.tax_per_sqft_median) for m, v in metrics.items()],
            key=lambda x: x[1]
        )
        
        efficiency_ranking = sorted(
            [(m, v.tax_efficiency_ratio) for m, v in metrics.items() if v.tax_efficiency_ratio > 0],
            key=lambda x: x[1]
        )
        
        # Generate insights
        insights = self._generate_insights(metrics, value_ranking, tax_ranking, efficiency_ranking)
        
        # Eastchester-specific analysis
        eastchester_comparison = self._analyze_eastchester_area(metrics)
        
        total_sales = sum(m.sample_size for m in metrics.values())
        
        return ComparisonReport(
            generated_date=date.today(),
            municipalities_compared=list(metrics.keys()),
            total_sales_analyzed=total_sales,
            metrics=metrics,
            value_ranking=value_ranking,
            tax_ranking=tax_ranking,
            efficiency_ranking=efficiency_ranking,
            insights=insights,
            eastchester_comparison=eastchester_comparison,
        )
    
    def _generate_insights(
        self,
        metrics: dict[str, MunicipalityMetrics],
        value_ranking: list,
        tax_ranking: list,
        efficiency_ranking: list
    ) -> list[str]:
        """Generate automatic insights from the data."""
        insights = []
        
        if not value_ranking:
            return ["Insufficient data for insights"]
        
        # Highest/lowest value areas
        highest_value = value_ranking[0]
        lowest_value = value_ranking[-1]
        
        insights.append(
            f"{highest_value[0]} has the highest home values at ${highest_value[1]:,.0f}/sqft, "
            f"while {lowest_value[0]} is lowest at ${lowest_value[1]:,.0f}/sqft"
        )
        
        # Value premium calculation
        if len(value_ranking) >= 2:
            premium = ((highest_value[1] / lowest_value[1]) - 1) * 100
            insights.append(
                f"Premium of {premium:.0f}% between highest and lowest value municipalities"
            )
        
        # Tax efficiency insights
        if efficiency_ranking:
            best_efficiency = efficiency_ranking[0]
            worst_efficiency = efficiency_ranking[-1]
            
            insights.append(
                f"{best_efficiency[0]} offers best tax efficiency ({best_efficiency[1]:.1f} tax/value ratio), "
                f"while {worst_efficiency[0]} is least efficient ({worst_efficiency[1]:.1f})"
            )
        
        # Tax burden insights
        if tax_ranking:
            lowest_tax = tax_ranking[0]
            highest_tax = tax_ranking[-1]
            
            if highest_tax[1] > 0 and lowest_tax[1] > 0:
                tax_difference = highest_tax[1] - lowest_tax[1]
                # For a 2000 sqft home
                annual_diff = tax_difference * 2000
                
                insights.append(
                    f"Tax difference: ${tax_difference:.2f}/sqft between {highest_tax[0]} and {lowest_tax[0]}. "
                    f"For a 2,000 sqft home, that's ${annual_diff:,.0f}/year"
                )
        
        # School district analysis
        bronxville_metrics = metrics.get('bronxville')
        if bronxville_metrics and bronxville_metrics.sample_size > 0:
            # Bronxville premium analysis
            avg_value = sum(m.value_per_sqft_median for m in metrics.values()) / len(metrics)
            bronxville_premium = ((bronxville_metrics.value_per_sqft_median / avg_value) - 1) * 100
            
            if bronxville_premium > 20:
                insights.append(
                    f"Bronxville commands a {bronxville_premium:.0f}% premium over area average, "
                    f"likely due to its highly-rated school district"
                )
        
        return insights
    
    def _analyze_eastchester_area(
        self,
        metrics: dict[str, MunicipalityMetrics]
    ) -> dict:
        """Generate Eastchester-specific analysis."""
        analysis = {}
        
        # Get metrics for Eastchester area
        eastchester = metrics.get('eastchester_unincorp')
        bronxville = metrics.get('bronxville')
        tuckahoe = metrics.get('tuckahoe')
        
        if bronxville and eastchester and bronxville.sample_size > 0 and eastchester.sample_size > 0:
            # Bronxville vs Eastchester unincorporated
            value_premium = bronxville.value_per_sqft_median - eastchester.value_per_sqft_median
            value_premium_pct = ((bronxville.value_per_sqft_median / eastchester.value_per_sqft_median) - 1) * 100
            
            analysis['Bronxville Premium vs Eastchester'] = f"${value_premium:,.0f}/sqft ({value_premium_pct:.0f}%)"
            
            # Tax comparison
            if bronxville.tax_per_sqft_median > 0 and eastchester.tax_per_sqft_median > 0:
                tax_diff = bronxville.tax_per_sqft_median - eastchester.tax_per_sqft_median
                analysis['Tax Difference (Bronxville - Eastchester)'] = f"${tax_diff:,.2f}/sqft/year"
        
        if tuckahoe and eastchester and tuckahoe.sample_size > 0 and eastchester.sample_size > 0:
            tuckahoe_diff = tuckahoe.value_per_sqft_median - eastchester.value_per_sqft_median
            analysis['Tuckahoe vs Eastchester Value'] = f"${tuckahoe_diff:+,.0f}/sqft"
        
        # School district value impact estimate
        if bronxville and eastchester and bronxville.sample_size > 0 and eastchester.sample_size > 0:
            # Estimate how much of premium is school-related
            # Rough estimate: similar tax structure, so difference is primarily schools + village services
            school_premium_estimate = bronxville.value_per_sqft_median - eastchester.value_per_sqft_median
            analysis['Estimated School District Premium'] = f"~${school_premium_estimate:,.0f}/sqft"
        
        return analysis
    
    def compare_tax_scenarios(
        self,
        market_value: float,
        sqft: float
    ) -> pd.DataFrame:
        """
        Compare tax scenarios for a hypothetical home across municipalities.
        
        Args:
            market_value: Home market value
            sqft: Home square footage
            
        Returns:
            DataFrame with tax comparison
        """
        results = []
        
        for muni_key in self._metrics_cache.keys():
            breakdown = self.tax_calc.calculate_from_market_value(market_value, muni_key)
            
            results.append({
                'Municipality': muni_key,
                'Annual Tax': breakdown.total,
                'Monthly Tax': breakdown.total / 12,
                'Tax/sqft': breakdown.total / sqft,
                'Effective Rate': breakdown.effective_rate,
                'School Tax %': breakdown.school_percentage,
            })
        
        df = pd.DataFrame(results)
        return df.sort_values('Annual Tax')
    
    def value_for_tax_analysis(
        self,
        annual_tax_budget: float
    ) -> pd.DataFrame:
        """
        Show what home value you can afford in each municipality
        for a given tax budget.
        
        Args:
            annual_tax_budget: Maximum annual property tax
            
        Returns:
            DataFrame showing affordable home values
        """
        results = []
        
        for muni_key, muni in MUNICIPALITIES.items():
            # Calculate: what market value gives us this tax?
            # tax = (market_value * rar / 1000) * total_rate
            # market_value = (tax * 1000) / (rar * total_rate)
            
            total_rate = muni.tax_rates.total
            if total_rate == 0:
                continue
            
            market_value = (annual_tax_budget * 1000) / (muni.rar * total_rate)
            
            # Get typical $/sqft for this municipality
            metrics = self._metrics_cache.get(muni_key)
            if metrics and metrics.value_per_sqft_median > 0:
                affordable_sqft = market_value / metrics.value_per_sqft_median
            else:
                affordable_sqft = None
            
            results.append({
                'Municipality': muni.name,
                'Affordable Home Value': market_value,
                'Typical $/sqft': metrics.value_per_sqft_median if metrics else None,
                'Affordable sqft': affordable_sqft,
            })
        
        df = pd.DataFrame(results)
        return df.sort_values('Affordable Home Value', ascending=False)


# =============================================================================
# Quick Comparison Functions
# =============================================================================

def quick_compare(
    sales_data: list[SaleRecord],
    municipalities: Optional[list[str]] = None
) -> ComparisonReport:
    """
    Quick comparison of municipalities.
    
    Convenience function for one-line comparisons.
    
    Args:
        sales_data: List of sale records
        municipalities: Optional list of specific municipalities
        
    Returns:
        ComparisonReport
    """
    engine = ComparisonEngine()
    engine.load_data(sales_data)
    return engine.generate_full_report(municipalities)


def compare_eastchester_area(sales_data: list[SaleRecord]) -> ComparisonReport:
    """
    Compare only Eastchester-area municipalities.
    
    Focuses on Bronxville, Tuckahoe, and unincorporated Eastchester.
    """
    return quick_compare(sales_data, EASTCHESTER_AREA)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    from data_collection.data_loader import DataLoader
    
    print("=" * 70)
    print("COMPARISON ENGINE DEMO")
    print("=" * 70)
    
    # Generate sample data
    loader = DataLoader()
    sample_data = loader.generate_sample_data(
        municipalities=[
            'bronxville', 'eastchester_unincorp', 'tuckahoe',
            'scarsdale', 'larchmont', 'mamaroneck_village'
        ],
        samples_per_muni=15
    )
    
    # Run comparison
    engine = ComparisonEngine()
    engine.load_from_dataset(sample_data)
    
    report = engine.generate_full_report()
    print(report)
    
    # Tax scenario comparison
    print("\n" + "=" * 70)
    print("TAX SCENARIO: $1,000,000 Home, 2,000 sqft")
    print("=" * 70)
    
    tax_comparison = engine.compare_tax_scenarios(1_000_000, 2000)
    print(tax_comparison.to_string(index=False))
    
    # Value for tax budget
    print("\n" + "=" * 70)
    print("WHAT CAN YOU AFFORD FOR $25,000/year IN TAXES?")
    print("=" * 70)
    
    affordability = engine.value_for_tax_analysis(25_000)
    print(affordability.to_string(index=False))


