"""
Statistical Analysis Utilities.

Provides statistical tests and analysis functions for
deeper investigation of property tax and value relationships.
"""

from dataclasses import dataclass
from typing import Optional, Tuple
from pathlib import Path
import sys

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.property import SaleRecord


@dataclass
class StatisticalSummary:
    """Summary statistics for a dataset."""
    count: int
    mean: float
    median: float
    std: float
    min_val: float
    max_val: float
    q1: float  # 25th percentile
    q3: float  # 75th percentile
    iqr: float  # Interquartile range
    
    @property
    def cv(self) -> float:
        """Coefficient of variation (relative std dev)."""
        if self.mean == 0:
            return 0
        return self.std / self.mean
    
    def __str__(self) -> str:
        return (
            f"n={self.count}, mean={self.mean:.2f}, median={self.median:.2f}, "
            f"std={self.std:.2f}, range=[{self.min_val:.2f}, {self.max_val:.2f}]"
        )


class StatisticalAnalyzer:
    """
    Statistical analysis tools for property data.
    
    Provides methods for:
    - Distribution analysis
    - Correlation analysis
    - Outlier detection
    - Significance testing
    """
    
    def __init__(self, sales_data: Optional[list[SaleRecord]] = None):
        """Initialize with optional sales data."""
        self.sales_data = sales_data or []
    
    def load_data(self, sales: list[SaleRecord]) -> None:
        """Load sales data."""
        self.sales_data = sales
    
    def get_dataframe(self) -> pd.DataFrame:
        """Convert sales data to DataFrame."""
        return pd.DataFrame([s.to_dict() for s in self.sales_data])
    
    def calculate_summary(self, values: list[float]) -> StatisticalSummary:
        """Calculate summary statistics for a list of values."""
        arr = np.array(values)
        
        if len(arr) == 0:
            return StatisticalSummary(
                count=0, mean=0, median=0, std=0,
                min_val=0, max_val=0, q1=0, q3=0, iqr=0
            )
        
        q1, q3 = np.percentile(arr, [25, 75])
        
        return StatisticalSummary(
            count=len(arr),
            mean=float(np.mean(arr)),
            median=float(np.median(arr)),
            std=float(np.std(arr, ddof=1)) if len(arr) > 1 else 0,
            min_val=float(np.min(arr)),
            max_val=float(np.max(arr)),
            q1=float(q1),
            q3=float(q3),
            iqr=float(q3 - q1),
        )
    
    def analyze_distribution(
        self,
        column: str,
        by_municipality: bool = True
    ) -> dict:
        """
        Analyze distribution of a variable.
        
        Args:
            column: Column name to analyze (e.g., 'price_per_sqft')
            by_municipality: If True, analyze separately by municipality
            
        Returns:
            Dict with distribution statistics
        """
        df = self.get_dataframe()
        
        if column not in df.columns:
            raise ValueError(f"Column {column} not found. Available: {list(df.columns)}")
        
        results = {}
        
        # Overall stats
        results['overall'] = self.calculate_summary(df[column].dropna().tolist())
        
        if by_municipality and 'municipality' in df.columns:
            results['by_municipality'] = {}
            for muni in df['municipality'].unique():
                muni_data = df[df['municipality'] == muni][column].dropna().tolist()
                if muni_data:
                    results['by_municipality'][muni] = self.calculate_summary(muni_data)
        
        return results
    
    def correlation_analysis(self) -> pd.DataFrame:
        """
        Analyze correlations between numeric variables.
        
        Returns correlation matrix for key variables.
        """
        df = self.get_dataframe()
        
        # Select numeric columns of interest
        numeric_cols = [
            'sale_price', 'sqft', 'price_per_sqft', 
            'annual_taxes', 'tax_per_sqft', 'effective_tax_rate',
            'bedrooms', 'bathrooms'
        ]
        
        available_cols = [c for c in numeric_cols if c in df.columns]
        
        if not available_cols:
            return pd.DataFrame()
        
        return df[available_cols].corr().round(3)
    
    def price_tax_correlation(self) -> Tuple[float, str]:
        """
        Analyze correlation between price/sqft and tax/sqft.
        
        Returns:
            Tuple of (correlation coefficient, interpretation)
        """
        df = self.get_dataframe()
        
        if 'price_per_sqft' not in df.columns or 'tax_per_sqft' not in df.columns:
            return 0.0, "Insufficient data"
        
        # Drop NaN and zero values
        valid = df[(df['price_per_sqft'] > 0) & (df['tax_per_sqft'] > 0)]
        
        if len(valid) < 3:
            return 0.0, "Insufficient data"
        
        corr = valid['price_per_sqft'].corr(valid['tax_per_sqft'])
        
        if abs(corr) < 0.3:
            interp = "weak"
        elif abs(corr) < 0.7:
            interp = "moderate"
        else:
            interp = "strong"
        
        direction = "positive" if corr > 0 else "negative"
        
        interpretation = (
            f"{interp.capitalize()} {direction} correlation ({corr:.3f}). "
            f"{'Higher-value homes tend to have higher taxes per sqft.' if corr > 0 else 'Higher-value homes tend to have lower taxes per sqft.'}"
        )
        
        return corr, interpretation
    
    def detect_outliers(
        self,
        column: str,
        method: str = 'iqr',
        threshold: float = 1.5
    ) -> pd.DataFrame:
        """
        Detect outliers in a column.
        
        Args:
            column: Column to analyze
            method: 'iqr' (interquartile range) or 'zscore'
            threshold: IQR multiplier or z-score threshold
            
        Returns:
            DataFrame of outlier records
        """
        df = self.get_dataframe()
        
        if column not in df.columns:
            raise ValueError(f"Column {column} not found")
        
        values = df[column].dropna()
        
        if method == 'iqr':
            q1 = values.quantile(0.25)
            q3 = values.quantile(0.75)
            iqr = q3 - q1
            
            lower_bound = q1 - threshold * iqr
            upper_bound = q3 + threshold * iqr
            
            outliers = df[
                (df[column] < lower_bound) | (df[column] > upper_bound)
            ]
        
        elif method == 'zscore':
            mean = values.mean()
            std = values.std()
            
            z_scores = (df[column] - mean) / std
            outliers = df[abs(z_scores) > threshold]
        
        else:
            raise ValueError(f"Unknown method: {method}")
        
        return outliers
    
    def municipality_comparison_test(
        self,
        muni1: str,
        muni2: str,
        column: str = 'price_per_sqft'
    ) -> dict:
        """
        Statistical comparison between two municipalities.
        
        Performs t-test to determine if differences are significant.
        
        Args:
            muni1: First municipality
            muni2: Second municipality
            column: Variable to compare
            
        Returns:
            Dict with test results
        """
        from scipy import stats
        
        df = self.get_dataframe()
        
        group1 = df[df['municipality'] == muni1][column].dropna()
        group2 = df[df['municipality'] == muni2][column].dropna()
        
        if len(group1) < 2 or len(group2) < 2:
            return {
                'error': 'Insufficient data for statistical test',
                'muni1_n': len(group1),
                'muni2_n': len(group2),
            }
        
        # Welch's t-test (doesn't assume equal variances)
        t_stat, p_value = stats.ttest_ind(group1, group2, equal_var=False)
        
        # Effect size (Cohen's d)
        pooled_std = np.sqrt((group1.std()**2 + group2.std()**2) / 2)
        cohens_d = (group1.mean() - group2.mean()) / pooled_std if pooled_std > 0 else 0
        
        return {
            'muni1': muni1,
            'muni2': muni2,
            'muni1_mean': group1.mean(),
            'muni2_mean': group2.mean(),
            'muni1_n': len(group1),
            'muni2_n': len(group2),
            'difference': group1.mean() - group2.mean(),
            't_statistic': t_stat,
            'p_value': p_value,
            'significant_05': p_value < 0.05,
            'significant_01': p_value < 0.01,
            'cohens_d': cohens_d,
            'effect_size': 'small' if abs(cohens_d) < 0.5 else 'medium' if abs(cohens_d) < 0.8 else 'large',
        }
    
    def regression_analysis(
        self,
        x_column: str = 'sqft',
        y_column: str = 'sale_price'
    ) -> dict:
        """
        Simple linear regression analysis.
        
        Args:
            x_column: Independent variable
            y_column: Dependent variable
            
        Returns:
            Dict with regression results
        """
        from scipy import stats
        
        df = self.get_dataframe()
        
        valid = df[[x_column, y_column]].dropna()
        
        if len(valid) < 3:
            return {'error': 'Insufficient data for regression'}
        
        x = valid[x_column].values
        y = valid[y_column].values
        
        slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
        
        return {
            'slope': slope,
            'intercept': intercept,
            'r_squared': r_value**2,
            'p_value': p_value,
            'std_error': std_err,
            'interpretation': (
                f"For each additional {x_column} unit, {y_column} increases by ${slope:,.2f} "
                f"(R² = {r_value**2:.3f})"
            ),
        }
    
    def anova_municipalities(self, column: str = 'price_per_sqft') -> dict:
        """
        ANOVA test to determine if municipalities differ significantly.
        
        Args:
            column: Variable to analyze
            
        Returns:
            Dict with ANOVA results
        """
        from scipy import stats
        
        df = self.get_dataframe()
        
        # Get groups
        groups = []
        municipalities = []
        
        for muni in df['municipality'].unique():
            muni_data = df[df['municipality'] == muni][column].dropna().tolist()
            if len(muni_data) >= 2:
                groups.append(muni_data)
                municipalities.append(muni)
        
        if len(groups) < 2:
            return {'error': 'Need at least 2 municipalities with sufficient data'}
        
        # One-way ANOVA
        f_stat, p_value = stats.f_oneway(*groups)
        
        return {
            'municipalities_compared': municipalities,
            'f_statistic': f_stat,
            'p_value': p_value,
            'significant_05': p_value < 0.05,
            'significant_01': p_value < 0.01,
            'interpretation': (
                f"There {'is' if p_value < 0.05 else 'is NOT'} a statistically significant "
                f"difference in {column} between municipalities (p={p_value:.4f})"
            ),
        }
    
    def generate_report(self) -> str:
        """Generate a comprehensive statistical report."""
        lines = [
            "=" * 70,
            "STATISTICAL ANALYSIS REPORT",
            "=" * 70,
            "",
        ]
        
        # Distribution analysis
        lines.append("DISTRIBUTION ANALYSIS")
        lines.append("-" * 50)
        
        for col in ['price_per_sqft', 'tax_per_sqft', 'effective_tax_rate']:
            try:
                dist = self.analyze_distribution(col)
                lines.append(f"\n{col}:")
                lines.append(f"  Overall: {dist['overall']}")
            except Exception:
                continue
        
        # Correlation
        lines.append("\n" + "=" * 50)
        lines.append("CORRELATION ANALYSIS")
        lines.append("-" * 50)
        
        corr, interp = self.price_tax_correlation()
        lines.append(f"Price/Tax Correlation: {interp}")
        
        # ANOVA
        lines.append("\n" + "=" * 50)
        lines.append("ANOVA: Do municipalities differ significantly?")
        lines.append("-" * 50)
        
        try:
            anova = self.anova_municipalities()
            lines.append(anova.get('interpretation', 'Unable to perform ANOVA'))
        except Exception as e:
            lines.append(f"ANOVA failed: {e}")
        
        return "\n".join(lines)


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    from data_collection.data_loader import DataLoader
    
    print("=" * 70)
    print("STATISTICAL ANALYZER DEMO")
    print("=" * 70)
    
    # Generate sample data
    loader = DataLoader()
    sample_data = loader.generate_sample_data(
        municipalities=['bronxville', 'eastchester_unincorp', 'tuckahoe', 'scarsdale'],
        samples_per_muni=20
    )
    
    # Run analysis
    analyzer = StatisticalAnalyzer(sample_data.records)
    
    print(analyzer.generate_report())
    
    # Municipality comparison
    print("\n" + "=" * 70)
    print("BRONXVILLE vs EASTCHESTER COMPARISON")
    print("=" * 70)
    
    comparison = analyzer.municipality_comparison_test(
        'bronxville', 'eastchester_unincorp', 'price_per_sqft'
    )
    
    for key, value in comparison.items():
        print(f"  {key}: {value}")


