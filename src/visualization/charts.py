"""
Chart Generation for Property Tax Analysis.

Creates visualizations for comparing municipalities
using Matplotlib, Seaborn, and Plotly.
"""

from pathlib import Path
from typing import Optional
import sys

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.metrics import MunicipalityMetrics


# Set style
sns.set_theme(style="whitegrid", palette="husl")
plt.rcParams['figure.figsize'] = (12, 8)
plt.rcParams['font.size'] = 11


class ChartGenerator:
    """
    Generator for property tax and value comparison charts.
    
    Creates publication-ready visualizations for reports
    and dashboards.
    
    Example:
        >>> from analysis.comparison import ComparisonEngine
        >>> engine = ComparisonEngine()
        >>> engine.load_data(sales)
        >>> report = engine.generate_full_report()
        >>> 
        >>> charts = ChartGenerator(report.metrics)
        >>> charts.plot_value_comparison()
        >>> charts.save_all('output/charts/')
    """
    
    # Color palette for municipalities
    COLORS = {
        'bronxville': '#2ecc71',      # Green - premium
        'eastchester_unincorp': '#3498db',  # Blue
        'tuckahoe': '#9b59b6',        # Purple
        'scarsdale': '#e74c3c',       # Red - premium
        'larchmont': '#f39c12',       # Orange
        'mamaroneck_village': '#1abc9c',  # Teal
        'mamaroneck_town': '#1abc9c',
        'pelham': '#34495e',          # Dark gray
        'pelham_manor': '#95a5a6',    # Gray
        'rye_city': '#e67e22',        # Dark orange
    }
    
    def __init__(
        self,
        metrics: Optional[dict[str, MunicipalityMetrics]] = None,
        output_dir: Optional[Path] = None
    ):
        """
        Initialize chart generator.
        
        Args:
            metrics: Dict of municipality -> MunicipalityMetrics
            output_dir: Directory to save charts
        """
        self.metrics = metrics or {}
        self.output_dir = output_dir or Path('output/charts')
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def load_metrics(self, metrics: dict[str, MunicipalityMetrics]) -> None:
        """Load metrics data."""
        self.metrics = metrics
    
    def get_color(self, municipality: str) -> str:
        """Get color for municipality."""
        return self.COLORS.get(municipality, '#7f8c8d')
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert metrics to DataFrame."""
        data = [m.to_dict() for m in self.metrics.values()]
        return pd.DataFrame(data)
    
    def plot_value_comparison(
        self,
        show: bool = True,
        save: bool = False,
        filename: str = 'value_comparison.png'
    ) -> plt.Figure:
        """
        Bar chart comparing home values per sqft.
        
        Args:
            show: Display the plot
            save: Save to file
            filename: Output filename
            
        Returns:
            Matplotlib Figure
        """
        df = self.to_dataframe().sort_values('value_per_sqft_median', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = [self.get_color(m) for m in df['municipality']]
        
        bars = ax.barh(df['municipality'], df['value_per_sqft_median'], color=colors)
        
        # Add value labels
        for bar, val in zip(bars, df['value_per_sqft_median']):
            ax.text(
                bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                f'${val:,.0f}',
                va='center', fontsize=10
            )
        
        # Add error bars for std dev
        if 'value_per_sqft_std' in df.columns:
            ax.errorbar(
                df['value_per_sqft_median'],
                range(len(df)),
                xerr=df['value_per_sqft_std'],
                fmt='none', color='black', capsize=3, alpha=0.5
            )
        
        ax.set_xlabel('Home Value ($/sqft)', fontsize=12)
        ax.set_ylabel('Municipality', fontsize=12)
        ax.set_title('Home Value per Square Foot by Municipality', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save:
            fig.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_tax_comparison(
        self,
        show: bool = True,
        save: bool = False,
        filename: str = 'tax_comparison.png'
    ) -> plt.Figure:
        """
        Bar chart comparing taxes per sqft.
        
        Args:
            show: Display the plot
            save: Save to file
            filename: Output filename
            
        Returns:
            Matplotlib Figure
        """
        df = self.to_dataframe().sort_values('tax_per_sqft_median', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = [self.get_color(m) for m in df['municipality']]
        
        bars = ax.barh(df['municipality'], df['tax_per_sqft_median'], color=colors)
        
        # Add value labels
        for bar, val in zip(bars, df['tax_per_sqft_median']):
            ax.text(
                bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'${val:,.2f}',
                va='center', fontsize=10
            )
        
        ax.set_xlabel('Annual Tax ($/sqft)', fontsize=12)
        ax.set_ylabel('Municipality', fontsize=12)
        ax.set_title('Property Tax per Square Foot by Municipality', fontsize=14, fontweight='bold')
        
        plt.tight_layout()
        
        if save:
            fig.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_value_vs_tax(
        self,
        show: bool = True,
        save: bool = False,
        filename: str = 'value_vs_tax.png'
    ) -> plt.Figure:
        """
        Scatter plot of value vs tax per sqft.
        
        Shows relationship between home values and tax burden.
        
        Args:
            show: Display the plot
            save: Save to file
            filename: Output filename
            
        Returns:
            Matplotlib Figure
        """
        df = self.to_dataframe()
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Plot each municipality
        for _, row in df.iterrows():
            color = self.get_color(row['municipality'])
            ax.scatter(
                row['value_per_sqft_median'],
                row['tax_per_sqft_median'],
                s=row['sample_size'] * 20,  # Size by sample size
                c=color,
                alpha=0.7,
                edgecolors='white',
                linewidth=2
            )
            
            # Label point
            ax.annotate(
                row['municipality'],
                (row['value_per_sqft_median'], row['tax_per_sqft_median']),
                xytext=(5, 5), textcoords='offset points',
                fontsize=9
            )
        
        # Add trend line
        if len(df) >= 3:
            z = np.polyfit(df['value_per_sqft_median'], df['tax_per_sqft_median'], 1)
            p = np.poly1d(z)
            x_line = np.linspace(df['value_per_sqft_median'].min(), df['value_per_sqft_median'].max(), 100)
            ax.plot(x_line, p(x_line), '--', color='gray', alpha=0.5, label='Trend')
        
        ax.set_xlabel('Home Value ($/sqft)', fontsize=12)
        ax.set_ylabel('Annual Tax ($/sqft)', fontsize=12)
        ax.set_title('Home Value vs Property Tax by Municipality', fontsize=14, fontweight='bold')
        ax.legend(loc='upper right')
        
        plt.tight_layout()
        
        if save:
            fig.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_tax_efficiency(
        self,
        show: bool = True,
        save: bool = False,
        filename: str = 'tax_efficiency.png'
    ) -> plt.Figure:
        """
        Bar chart showing tax efficiency ratio.
        
        Lower ratio = better value for your tax dollar.
        
        Args:
            show: Display the plot
            save: Save to file
            filename: Output filename
            
        Returns:
            Matplotlib Figure
        """
        df = self.to_dataframe().sort_values('tax_efficiency_ratio', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        # Color code: green = efficient, red = less efficient
        efficiency_colors = []
        max_ratio = df['tax_efficiency_ratio'].max()
        min_ratio = df['tax_efficiency_ratio'].min()
        
        for ratio in df['tax_efficiency_ratio']:
            # Normalize to 0-1
            norm = (ratio - min_ratio) / (max_ratio - min_ratio) if max_ratio > min_ratio else 0.5
            # Green to red gradient
            r = norm
            g = 1 - norm
            efficiency_colors.append((r, g, 0.3))
        
        bars = ax.barh(df['municipality'], df['tax_efficiency_ratio'], color=efficiency_colors)
        
        # Add value labels
        for bar, val in zip(bars, df['tax_efficiency_ratio']):
            ax.text(
                bar.get_width() + 0.5, bar.get_y() + bar.get_height()/2,
                f'{val:.1f}',
                va='center', fontsize=10
            )
        
        ax.set_xlabel('Tax Efficiency Ratio (Tax$/sqft per $1000 Value/sqft)', fontsize=11)
        ax.set_ylabel('Municipality', fontsize=12)
        ax.set_title('Tax Efficiency Ranking\n(Lower = Better Value for Tax Dollar)', fontsize=14, fontweight='bold')
        
        # Add explanation
        ax.text(
            0.95, 0.05,
            'Green = More Efficient\nRed = Less Efficient',
            transform=ax.transAxes,
            fontsize=9,
            verticalalignment='bottom',
            horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='white', alpha=0.8)
        )
        
        plt.tight_layout()
        
        if save:
            fig.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_effective_tax_rate(
        self,
        show: bool = True,
        save: bool = False,
        filename: str = 'effective_tax_rate.png'
    ) -> plt.Figure:
        """
        Bar chart comparing effective tax rates.
        
        Args:
            show: Display the plot
            save: Save to file
            filename: Output filename
            
        Returns:
            Matplotlib Figure
        """
        df = self.to_dataframe().sort_values('effective_rate_median', ascending=True)
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        colors = [self.get_color(m) for m in df['municipality']]
        
        bars = ax.barh(df['municipality'], df['effective_rate_median'], color=colors)
        
        # Add value labels
        for bar, val in zip(bars, df['effective_rate_median']):
            ax.text(
                bar.get_width() + 0.05, bar.get_y() + bar.get_height()/2,
                f'{val:.2f}%',
                va='center', fontsize=10
            )
        
        ax.set_xlabel('Effective Tax Rate (%)', fontsize=12)
        ax.set_ylabel('Municipality', fontsize=12)
        ax.set_title('Effective Property Tax Rate by Municipality', fontsize=14, fontweight='bold')
        
        # Add NY state average line
        ax.axvline(x=2.0, color='red', linestyle='--', alpha=0.5, label='NY State Avg (~2%)')
        ax.legend()
        
        plt.tight_layout()
        
        if save:
            fig.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_price_distribution(
        self,
        sales_df: pd.DataFrame,
        show: bool = True,
        save: bool = False,
        filename: str = 'price_distribution.png'
    ) -> plt.Figure:
        """
        Box plot showing price distribution by municipality.
        
        Args:
            sales_df: DataFrame with sales data
            show: Display the plot
            save: Save to file
            filename: Output filename
            
        Returns:
            Matplotlib Figure
        """
        fig, ax = plt.subplots(figsize=(14, 8))
        
        # Order by median
        order = sales_df.groupby('municipality')['price_per_sqft'].median().sort_values(ascending=False).index.tolist()
        
        palette = {m: self.get_color(m) for m in order}
        
        sns.boxplot(
            data=sales_df,
            x='municipality',
            y='price_per_sqft',
            order=order,
            palette=palette,
            ax=ax
        )
        
        ax.set_xlabel('Municipality', fontsize=12)
        ax.set_ylabel('Price ($/sqft)', fontsize=12)
        ax.set_title('Home Price Distribution by Municipality', fontsize=14, fontweight='bold')
        
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        if save:
            fig.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def plot_tax_breakdown(
        self,
        market_value: float = 1_000_000,
        show: bool = True,
        save: bool = False,
        filename: str = 'tax_breakdown.png'
    ) -> plt.Figure:
        """
        Stacked bar showing tax component breakdown.
        
        Args:
            market_value: Example home value for calculation
            show: Display the plot
            save: Save to file
            filename: Output filename
            
        Returns:
            Matplotlib Figure
        """
        from models.tax_calculator import TaxCalculator
        
        calc = TaxCalculator()
        municipalities = list(self.metrics.keys())
        
        # Calculate tax breakdowns
        data = []
        for muni in municipalities:
            try:
                breakdown = calc.calculate_from_market_value(market_value, muni)
                data.append({
                    'Municipality': muni,
                    'School': breakdown.school_tax,
                    'County': breakdown.county_tax,
                    'Town': breakdown.town_tax,
                    'Village': breakdown.village_tax,
                    'Fire/Other': breakdown.fire_district_tax + breakdown.library_tax + breakdown.special_district_tax,
                })
            except Exception:
                continue
        
        if not data:
            return plt.figure()
        
        df = pd.DataFrame(data)
        df = df.set_index('Municipality')
        
        # Sort by total
        df['Total'] = df.sum(axis=1)
        df = df.sort_values('Total', ascending=True)
        df = df.drop('Total', axis=1)
        
        fig, ax = plt.subplots(figsize=(14, 8))
        
        df.plot(
            kind='barh',
            stacked=True,
            ax=ax,
            colormap='Set2'
        )
        
        ax.set_xlabel('Annual Tax ($)', fontsize=12)
        ax.set_ylabel('Municipality', fontsize=12)
        ax.set_title(f'Property Tax Breakdown for ${market_value:,.0f} Home', fontsize=14, fontweight='bold')
        ax.legend(title='Tax Component', bbox_to_anchor=(1.02, 1), loc='upper left')
        
        plt.tight_layout()
        
        if save:
            fig.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
        
        if show:
            plt.show()
        
        return fig
    
    def save_all(
        self,
        output_dir: Optional[Path] = None,
        sales_df: Optional[pd.DataFrame] = None
    ) -> list[Path]:
        """
        Save all charts to directory.
        
        Args:
            output_dir: Output directory
            sales_df: Optional sales DataFrame for distribution charts
            
        Returns:
            List of saved file paths
        """
        if output_dir:
            self.output_dir = Path(output_dir)
            self.output_dir.mkdir(parents=True, exist_ok=True)
        
        saved = []
        
        # Generate and save all charts
        self.plot_value_comparison(show=False, save=True)
        saved.append(self.output_dir / 'value_comparison.png')
        
        self.plot_tax_comparison(show=False, save=True)
        saved.append(self.output_dir / 'tax_comparison.png')
        
        self.plot_value_vs_tax(show=False, save=True)
        saved.append(self.output_dir / 'value_vs_tax.png')
        
        self.plot_tax_efficiency(show=False, save=True)
        saved.append(self.output_dir / 'tax_efficiency.png')
        
        self.plot_effective_tax_rate(show=False, save=True)
        saved.append(self.output_dir / 'effective_tax_rate.png')
        
        self.plot_tax_breakdown(show=False, save=True)
        saved.append(self.output_dir / 'tax_breakdown.png')
        
        if sales_df is not None:
            self.plot_price_distribution(sales_df, show=False, save=True)
            saved.append(self.output_dir / 'price_distribution.png')
        
        print(f"Saved {len(saved)} charts to {self.output_dir}")
        return saved


# =============================================================================
# Interactive Plotly Charts
# =============================================================================

def create_interactive_comparison(
    metrics: dict[str, MunicipalityMetrics]
) -> 'plotly.graph_objects.Figure':
    """
    Create interactive Plotly comparison chart.
    
    Args:
        metrics: Municipality metrics dict
        
    Returns:
        Plotly Figure
    """
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    
    df = pd.DataFrame([m.to_dict() for m in metrics.values()])
    df = df.sort_values('value_per_sqft_median', ascending=False)
    
    fig = make_subplots(
        rows=1, cols=2,
        subplot_titles=('Home Value ($/sqft)', 'Tax ($/sqft)'),
        shared_yaxes=True
    )
    
    # Value bars
    fig.add_trace(
        go.Bar(
            x=df['value_per_sqft_median'],
            y=df['municipality'],
            orientation='h',
            name='Value/sqft',
            marker_color='steelblue',
            hovertemplate='$%{x:,.0f}/sqft<extra></extra>'
        ),
        row=1, col=1
    )
    
    # Tax bars
    fig.add_trace(
        go.Bar(
            x=df['tax_per_sqft_median'],
            y=df['municipality'],
            orientation='h',
            name='Tax/sqft',
            marker_color='coral',
            hovertemplate='$%{x:,.2f}/sqft<extra></extra>'
        ),
        row=1, col=2
    )
    
    fig.update_layout(
        title='Municipality Comparison: Home Values vs Property Taxes',
        height=500,
        showlegend=False,
    )
    
    return fig


# =============================================================================
# Example Usage
# =============================================================================

if __name__ == "__main__":
    from data_collection.data_loader import DataLoader
    from analysis.comparison import ComparisonEngine
    
    print("=" * 70)
    print("CHART GENERATOR DEMO")
    print("=" * 70)
    
    # Generate sample data
    loader = DataLoader()
    sample_data = loader.generate_sample_data(
        municipalities=['bronxville', 'eastchester_unincorp', 'tuckahoe', 'scarsdale', 'larchmont'],
        samples_per_muni=15
    )
    
    # Run comparison
    engine = ComparisonEngine()
    engine.load_from_dataset(sample_data)
    report = engine.generate_full_report()
    
    # Generate charts
    charts = ChartGenerator(report.metrics)
    
    print("\nGenerating charts...")
    charts.plot_value_comparison(show=True, save=False)
    charts.plot_tax_efficiency(show=True, save=False)
    
    print("\nTo save all charts:")
    print("  charts.save_all('output/charts/')")


