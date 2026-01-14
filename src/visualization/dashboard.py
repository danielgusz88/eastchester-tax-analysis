"""
Streamlit Dashboard for Property Tax Analysis.

Interactive web dashboard for exploring and comparing
property taxes and home values across Westchester municipalities.

Run with: streamlit run src/visualization/dashboard.py
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from config import MUNICIPALITIES, EASTCHESTER_AREA, get_municipality
from models.tax_calculator import TaxCalculator
from models.metrics import MetricsCalculator
from data_collection.data_loader import DataLoader
from analysis.comparison import ComparisonEngine
from analysis.fire_comparison import compare_fire_departments, load_fire_budgets
from analysis.school_comparison import compare_school_districts, load_school_budgets
from analysis.town_budget_comparison import compare_town_budgets
from visualization.map_view import create_combined_map


# =============================================================================
# Page Configuration
# =============================================================================

def configure_page():
    """Configure Streamlit page settings."""
    st.set_page_config(
        page_title="Eastchester Tax Analysis",
        page_icon="🏠",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    # Custom CSS
    st.markdown("""
        <style>
        .main-header {
            font-size: 2.5rem;
            font-weight: bold;
            color: #1f77b4;
            margin-bottom: 0.5rem;
        }
        .sub-header {
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }
        .metric-card {
            background-color: #f0f2f6;
            padding: 1rem;
            border-radius: 0.5rem;
            margin: 0.5rem 0;
        }
        .highlight {
            color: #2ecc71;
            font-weight: bold;
        }
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        /* Better spacing */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            padding: 10px 20px;
        }
        </style>
    """, unsafe_allow_html=True)


# =============================================================================
# Data Loading
# =============================================================================

@st.cache_data
def load_data():
    """Load data - tries real data first, falls back to sample."""
    loader = DataLoader()
    
    # Try to load real data
    try:
        dataset = loader.load_all_sales()
        if len(dataset) > 0:
            st.success(f"✅ Loaded {len(dataset)} real sales records")
            return dataset, True
    except Exception:
        pass
    
    # Try unified dataset
    try:
        dataset = loader.load_unified_dataset('unified_sales.parquet')
        if len(dataset) > 0:
            st.info(f"📊 Loaded {len(dataset)} sales from unified dataset")
            return dataset, True
    except Exception:
        pass
    
    # Fall back to sample data
    st.warning("⚠️ Using sample data. Add real sales data to data/raw/sales/ for actual analysis.")
    dataset = loader.generate_sample_data(
        municipalities=['bronxville', 'eastchester_unincorp', 'tuckahoe', 
                       'scarsdale', 'larchmont', 'mamaroneck_village'],
        samples_per_muni=30
    )
    return dataset, False


@st.cache_data
def generate_comparison_report(_dataset):
    """Generate comparison report (cached)."""
    engine = ComparisonEngine()
    engine.load_from_dataset(_dataset)
    return engine.generate_full_report()


# =============================================================================
# Dashboard Components
# =============================================================================

def render_sidebar():
    """Render sidebar with controls."""
    st.sidebar.title("🏠 Analysis Controls")
    
    # Municipality selection
    st.sidebar.subheader("Municipalities")
    all_munis = list(MUNICIPALITIES.keys())
    
    default_munis = ['bronxville', 'eastchester_unincorp', 'tuckahoe', 'scarsdale', 'larchmont']
    
    selected_munis = st.sidebar.multiselect(
        "Select municipalities to compare:",
        options=all_munis,
        default=default_munis,
        format_func=lambda x: MUNICIPALITIES[x].name
    )
    
    # Home value for scenarios
    st.sidebar.subheader("Tax Calculator")
    home_value = st.sidebar.slider(
        "Home Value ($)",
        min_value=300_000,
        max_value=5_000_000,
        value=1_000_000,
        step=50_000,
        format="$%d"
    )
    
    sqft = st.sidebar.slider(
        "Square Footage",
        min_value=500,
        max_value=6000,
        value=2000,
        step=100
    )
    
    return {
        'selected_munis': selected_munis,
        'home_value': home_value,
        'sqft': sqft
    }


def render_header():
    """Render page header."""
    st.markdown('<p class="main-header">Eastchester Property Tax & Value Analysis</p>', unsafe_allow_html=True)
    st.markdown(
        '<p class="sub-header">Compare property taxes and home values across Westchester County municipalities</p>',
        unsafe_allow_html=True
    )


def render_key_metrics(report):
    """Render key metrics cards."""
    col1, col2, col3, col4 = st.columns(4)
    
    metrics = report.metrics
    
    # Calculate overall stats
    if metrics:
        avg_value = sum(m.value_per_sqft_median for m in metrics.values()) / len(metrics)
        avg_tax = sum(m.tax_per_sqft_median for m in metrics.values()) / len(metrics)
        avg_rate = sum(m.effective_rate_median for m in metrics.values()) / len(metrics)
        
        with col1:
            st.metric(
                "Municipalities Compared",
                len(metrics),
                delta=f"{report.total_sales_analyzed} sales"
            )
        
        with col2:
            st.metric(
                "Avg Value/sqft",
                f"${avg_value:,.0f}",
                delta=f"Range: ${min(m.value_per_sqft_median for m in metrics.values()):,.0f} - ${max(m.value_per_sqft_median for m in metrics.values()):,.0f}"
            )
        
        with col3:
            st.metric(
                "Avg Tax/sqft",
                f"${avg_tax:,.2f}",
                delta=f"~${avg_tax * 2000:,.0f}/yr for 2000sqft"
            )
        
        with col4:
            st.metric(
                "Avg Effective Rate",
                f"{avg_rate:.2f}%",
                delta="of market value"
            )


def render_map_view(report):
    """Render map view with municipalities."""
    df = report.to_dataframe()
    
    # Create combined map
    fig = create_combined_map(df)
    
    if fig:
        st.plotly_chart(fig, use_container_width=True)
        
        col1, col2 = st.columns(2)
        with col1:
            st.info("""
            **Map Legend:**
            - **Circle Size** = Home value per sqft (larger = higher value)
            - **Circle Color** = Tax per sqft (redder = higher taxes)
            - **Hover** over circles for detailed metrics
            """)
        with col2:
            st.info("""
            **Tips:**
            - Zoom in/out with mouse wheel
            - Click and drag to pan
            - Click markers to see full details
            """)
    else:
        st.warning("No map data available. Add municipality coordinates to map_view.py")


def render_comparison_charts(report):
    """Render comparison charts."""
    df = report.to_dataframe()
    
    # Value vs Tax scatter
    fig_scatter = px.scatter(
        df,
        x='value_per_sqft_median',
        y='tax_per_sqft_median',
        size='sample_size',
        color='municipality',
        hover_data=['effective_rate_median', 'sample_size'],
        title='Home Value vs Property Tax by Municipality',
        labels={
            'value_per_sqft_median': 'Home Value ($/sqft)',
            'tax_per_sqft_median': 'Annual Tax ($/sqft)',
            'municipality': 'Municipality'
        },
        template='plotly_white'
    )
    fig_scatter.update_layout(height=500, hovermode='closest')
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    # Side by side bars
    col1, col2 = st.columns(2)
    
    with col1:
        df_sorted = df.sort_values('value_per_sqft_median', ascending=True)
        fig_value = px.bar(
            df_sorted,
            x='value_per_sqft_median',
            y='municipality',
            orientation='h',
            title='Home Value Ranking ($/sqft)',
            labels={'value_per_sqft_median': '$/sqft', 'municipality': ''},
            color='value_per_sqft_median',
            color_continuous_scale='Blues'
        )
        fig_value.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_value, use_container_width=True)
    
    with col2:
        df_sorted = df.sort_values('tax_per_sqft_median', ascending=True)
        fig_tax = px.bar(
            df_sorted,
            x='tax_per_sqft_median',
            y='municipality',
            orientation='h',
            title='Tax Burden Ranking ($/sqft/year)',
            labels={'tax_per_sqft_median': '$/sqft', 'municipality': ''},
            color='tax_per_sqft_median',
            color_continuous_scale='Reds'
        )
        fig_tax.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig_tax, use_container_width=True)


def render_tax_calculator(home_value: float, sqft: float, municipalities: list):
    """Render tax calculator section."""
    st.subheader("🧮 Tax Calculator")
    st.write(f"Compare annual taxes for a **${home_value:,.0f}** home with **{sqft:,} sqft**")
    
    calc = TaxCalculator()
    
    results = []
    for muni in municipalities:
        try:
            breakdown = calc.calculate_from_market_value(home_value, muni)
            results.append({
                'Municipality': MUNICIPALITIES[muni].name,
                'Annual Tax': breakdown.total,
                'Monthly': breakdown.total / 12,
                'Tax/sqft': breakdown.total / sqft,
                'Effective Rate': breakdown.effective_rate,
                'School %': breakdown.school_percentage,
            })
        except Exception:
            continue
    
    if results:
        df = pd.DataFrame(results).sort_values('Annual Tax')
        
        # Format for display
        df_display = df.copy()
        df_display['Annual Tax'] = df_display['Annual Tax'].apply(lambda x: f"${x:,.0f}")
        df_display['Monthly'] = df_display['Monthly'].apply(lambda x: f"${x:,.0f}")
        df_display['Tax/sqft'] = df_display['Tax/sqft'].apply(lambda x: f"${x:.2f}")
        df_display['Effective Rate'] = df_display['Effective Rate'].apply(lambda x: f"{x:.2f}%")
        df_display['School %'] = df_display['School %'].apply(lambda x: f"{x:.1f}%")
        
        st.dataframe(df_display, use_container_width=True, hide_index=True)
        
        # Difference analysis
        min_tax = df['Annual Tax'].min()
        max_tax = df['Annual Tax'].max()
        diff = max_tax - min_tax
        
        st.info(
            f"💡 **Tax Difference:** ${diff:,.0f}/year between lowest and highest "
            f"(${diff/12:,.0f}/month, ${diff/sqft:.2f}/sqft)"
        )


def render_tax_breakdown(home_value: float, municipalities: list):
    """Render tax component breakdown chart."""
    st.subheader("📊 Tax Component Breakdown")
    
    calc = TaxCalculator()
    
    data = []
    for muni in municipalities:
        try:
            breakdown = calc.calculate_from_market_value(home_value, muni)
            data.append({
                'Municipality': MUNICIPALITIES[muni].name,
                'School': breakdown.school_tax,
                'County': breakdown.county_tax,
                'Town': breakdown.town_tax,
                'Village': breakdown.village_tax,
                'Fire/Library/Other': breakdown.fire_district_tax + breakdown.library_tax + breakdown.special_district_tax,
            })
        except Exception:
            continue
    
    if data:
        df = pd.DataFrame(data)
        df = df.set_index('Municipality')
        
        fig = px.bar(
            df.reset_index().melt(id_vars='Municipality', var_name='Component', value_name='Amount'),
            x='Municipality',
            y='Amount',
            color='Component',
            title=f'Tax Component Breakdown for ${home_value:,.0f} Home',
            labels={'Amount': 'Annual Tax ($)'},
        )
        fig.update_layout(height=500, barmode='stack')
        st.plotly_chart(fig, use_container_width=True)


def render_efficiency_analysis(report):
    """Render tax efficiency analysis."""
    st.subheader("⚡ Tax Efficiency Analysis")
    st.write("*Lower efficiency ratio = better value for your tax dollar*")
    
    df = report.to_dataframe()
    df = df.sort_values('tax_efficiency_ratio')
    
    fig = px.bar(
        df,
        x='tax_efficiency_ratio',
        y='municipality',
        orientation='h',
        title='Tax Efficiency Ranking',
        labels={
            'tax_efficiency_ratio': 'Efficiency Ratio (lower is better)',
            'municipality': ''
        },
        color='tax_efficiency_ratio',
        color_continuous_scale='RdYlGn_r'  # Red=high, Green=low
    )
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # Interpretation
    best = df.iloc[0]
    worst = df.iloc[-1]
    
    col1, col2 = st.columns(2)
    with col1:
        st.success(
            f"🏆 **Most Efficient:** {best['municipality']}\n\n"
            f"Ratio: {best['tax_efficiency_ratio']:.2f}"
        )
    with col2:
        st.warning(
            f"📉 **Least Efficient:** {worst['municipality']}\n\n"
            f"Ratio: {worst['tax_efficiency_ratio']:.2f}"
        )


def render_town_budget_comparison():
    """Render town budget comparison with concerns analysis."""
    st.subheader("🏛️ Town Budget Comparison")
    st.write("Comparing Eastchester town budget against Scarsdale, Pelham, and Larchmont")
    
    try:
        comparison = compare_town_budgets()
        concerns = comparison.find_concerns()
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Eastchester",
                f"${comparison.eastchester.per_resident_cost:,.0f}/resident",
                f"${comparison.eastchester.total_budget:,.0f} total"
            )
        
        avg_comp = sum(t.per_resident_cost for t in comparison.comparison_towns.values()) / len(comparison.comparison_towns)
        diff = comparison.eastchester.per_resident_cost - avg_comp
        
        with col2:
            st.metric(
                "Comparison Avg",
                f"${avg_comp:,.0f}/resident",
                f"{'+' if diff > 0 else ''}${diff:,.0f} vs Eastchester"
            )
        
        with col3:
            st.metric(
                "Key Concerns",
                len(concerns),
                "Areas of concern identified"
            )
        
        with col4:
            high_severity = sum(1 for c in concerns if c.get('severity') == 'high')
            st.metric(
                "High Severity",
                high_severity,
                "Critical issues"
            )
        
        st.divider()
        
        # Top 5 Concerns
        st.subheader("⚠️ Top 5 Concerns for Eastchester Residents")
        st.write("Based on comparison with Scarsdale, Pelham, and Larchmont")
        
        for i, concern in enumerate(concerns, 1):
            severity_color = {
                'high': '🔴',
                'medium': '🟡',
                'low': '🟢'
            }.get(concern.get('severity', 'medium'), '🟡')
            
            with st.expander(f"{severity_color} {i}. {concern['category']}: {concern['issue']}", expanded=(i <= 2)):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Eastchester:** {concern['eastchester']}")
                    st.write(f"**Comparison Average:** {concern['comparison_avg']}")
                    st.write(f"**Difference:** {concern['difference']}")
                    st.write(f"**Percentage:** {concern['percentage']}")
                
                with col2:
                    st.write(f"**Impact:**")
                    st.info(concern['impact'])
                    st.write(f"**Severity:** {concern['severity'].upper()}")
        
        st.divider()
        
        # Budget breakdown comparison
        st.subheader("📊 Budget Category Comparison")
        
        # Create comparison chart
        categories = ['Public Safety', 'Public Works', 'Parks & Recreation', 'Administration']
        eastchester_data = [
            comparison.eastchester.per_resident_public_safety,
            comparison.eastchester.per_resident_public_works,
            comparison.eastchester.per_resident_parks,
            comparison.eastchester.per_resident_admin,
        ]
        
        avg_data = []
        for cat in categories:
            if cat == 'Public Safety':
                avg = sum(t.per_resident_public_safety for t in comparison.comparison_towns.values()) / len(comparison.comparison_towns)
            elif cat == 'Public Works':
                avg = sum(t.per_resident_public_works for t in comparison.comparison_towns.values()) / len(comparison.comparison_towns)
            elif cat == 'Parks & Recreation':
                avg = sum(t.per_resident_parks for t in comparison.comparison_towns.values()) / len(comparison.comparison_towns)
            else:  # Administration
                avg = sum(t.per_resident_admin for t in comparison.comparison_towns.values()) / len(comparison.comparison_towns)
            avg_data.append(avg)
        
        df = pd.DataFrame({
            'Category': categories,
            'Eastchester': eastchester_data,
            'Comparison Average': avg_data,
        })
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            name='Eastchester',
            x=df['Category'],
            y=df['Eastchester'],
            marker_color='#3498db'
        ))
        fig.add_trace(go.Bar(
            name='Comparison Average',
            x=df['Category'],
            y=df['Comparison Average'],
            marker_color='#e74c3c'
        ))
        
        fig.update_layout(
            title='Per-Resident Spending by Category',
            xaxis_title='Category',
            yaxis_title='Cost Per Resident ($)',
            barmode='group',
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        with st.expander("📋 Detailed Budget Breakdown"):
            detail_df = pd.DataFrame([
                {
                    'Municipality': 'Eastchester',
                    'Total Budget': comparison.eastchester.total_budget,
                    'Population': comparison.eastchester.population,
                    'Per Resident': comparison.eastchester.per_resident_cost,
                    'Public Safety': comparison.eastchester.per_resident_public_safety,
                    'Public Works': comparison.eastchester.per_resident_public_works,
                    'Parks/Rec': comparison.eastchester.per_resident_parks,
                    'Administration': comparison.eastchester.per_resident_admin,
                }
            ])
            
            for name, town in comparison.comparison_towns.items():
                detail_df = pd.concat([
                    detail_df,
                    pd.DataFrame([{
                        'Municipality': name.title(),
                        'Total Budget': town.total_budget,
                        'Population': town.population,
                        'Per Resident': town.per_resident_cost,
                        'Public Safety': town.per_resident_public_safety,
                        'Public Works': town.per_resident_public_works,
                        'Parks/Rec': town.per_resident_parks,
                        'Administration': town.per_resident_admin,
                    }])
                ], ignore_index=True)
            
            # Format for display
            display_df = detail_df.copy()
            for col in ['Total Budget', 'Per Resident', 'Public Safety', 'Public Works', 'Parks/Rec', 'Administration']:
                if col in display_df.columns:
                    display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
            display_df['Population'] = display_df['Population'].apply(lambda x: f"{x:,}" if isinstance(x, (int, float)) else x)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Data source
        st.caption(f"📅 Data collected: {comparison.eastchester.collection_date}")
        st.caption(f"📊 Sources: Municipal budgets and websites")
        
        st.divider()
        
        # =====================================================================
        # TAX BURDEN ANALYSIS
        # =====================================================================
        st.subheader("💰 Tax Burden vs Services Analysis")
        st.write("Comparing property taxes paid vs services received for combined Eastchester area")
        
        # Get tax burden analysis
        typical_home = st.slider(
            "Typical Home Value for Analysis",
            min_value=500_000,
            max_value=2_500_000,
            value=1_000_000,
            step=50_000,
            format="$%d",
            key="tax_burden_home_value"
        )
        
        typical_sqft = st.slider(
            "Typical Square Footage",
            min_value=1000,
            max_value=4000,
            value=2000,
            step=100,
            key="tax_burden_sqft"
        )
        
        try:
            # Calculate tax burdens
            combined_eastchester = comparison.get_combined_eastchester_tax_analysis(typical_home, typical_sqft)
            all_burdens = comparison.calculate_tax_burdens(typical_home, typical_sqft)
            
            # Summary metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Eastchester Area\n(Combined)",
                    f"${combined_eastchester.weighted_avg_tax_per_sqft:.2f}/sqft",
                    f"${combined_eastchester.weighted_avg_tax_per_taxpayer:,.0f}/taxpayer"
                )
                st.caption("Weighted average across 3 municipalities")
            
            # Calculate comparison average
            comp_burdens = [b for k, b in all_burdens.items() if k in ['scarsdale', 'pelham', 'larchmont']]
            if comp_burdens:
                avg_tax_per_sqft = sum(b.tax_per_sqft for b in comp_burdens) / len(comp_burdens)
                avg_tax_per_taxpayer = sum(b.tax_per_taxpayer for b in comp_burdens) / len(comp_burdens)
                
                with col2:
                    st.metric(
                        "Comparison Avg\n(Scarsdale, Pelham, Larchmont)",
                        f"${avg_tax_per_sqft:.2f}/sqft",
                        f"${avg_tax_per_taxpayer:,.0f}/taxpayer"
                    )
                    st.caption("Average of comparison towns")
                
                diff_sqft = combined_eastchester.weighted_avg_tax_per_sqft - avg_tax_per_sqft
                diff_taxpayer = combined_eastchester.weighted_avg_tax_per_taxpayer - avg_tax_per_taxpayer
                
                with col3:
                    st.metric(
                        "Tax Difference",
                        f"${diff_sqft:+.2f}/sqft",
                        f"${diff_taxpayer:+,.0f}/taxpayer"
                    )
                    st.caption("Eastchester vs comparison average")
                
                # Value for tax dollar
                eastchester_services = comparison.eastchester.per_resident_cost
                avg_services = sum(t.per_resident_cost for t in comparison.comparison_towns.values()) / len(comparison.comparison_towns)
                service_ratio = eastchester_services / avg_services if avg_services > 0 else 0
                
                with col4:
                    st.metric(
                        "Service Value Ratio",
                        f"{service_ratio:.2f}x",
                        f"{((service_ratio - 1) * 100):+.1f}% vs avg"
                    )
                    st.caption("Services received per tax dollar")
            
            st.divider()
            
            # Tax per sqft comparison chart
            st.subheader("📊 Tax Per Square Foot Comparison")
            
            tax_df = pd.DataFrame([
                {
                    'Municipality': 'Eastchester Area\n(Combined)',
                    'Tax per sqft': combined_eastchester.weighted_avg_tax_per_sqft,
                    'Municipal Tax per sqft': combined_eastchester.weighted_avg_municipal_tax_per_sqft,
                }
            ])
            
            for muni_key, burden in all_burdens.items():
                if muni_key in ['scarsdale', 'pelham', 'larchmont']:
                    tax_df = pd.concat([
                        tax_df,
                        pd.DataFrame([{
                            'Municipality': burden.municipality,
                            'Tax per sqft': burden.tax_per_sqft,
                            'Municipal Tax per sqft': burden.municipal_tax_per_sqft,
                        }])
                    ], ignore_index=True)
            
            fig = go.Figure()
            fig.add_trace(go.Bar(
                name='Total Tax per sqft',
                x=tax_df['Municipality'],
                y=tax_df['Tax per sqft'],
                marker_color='#3498db'
            ))
            fig.add_trace(go.Bar(
                name='Municipal Tax per sqft\n(Town+Village only)',
                x=tax_df['Municipality'],
                y=tax_df['Municipal Tax per sqft'],
                marker_color='#e74c3c'
            ))
            
            fig.update_layout(
                title=f'Property Tax Per Square Foot (${typical_home:,.0f} home, {typical_sqft:,} sqft)',
                xaxis_title='Municipality',
                yaxis_title='Tax Per Square Foot ($)',
                barmode='group',
                height=500
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Key insight: Tax vs Services
            st.info(f"""
            **Key Finding:** Eastchester area residents pay **${abs(diff_sqft):.2f} {'more' if diff_sqft > 0 else 'less'} per sqft** 
            in property taxes compared to the average of Scarsdale, Pelham, and Larchmont.
            
            However, Eastchester provides **{((service_ratio - 1) * 100):+.1f}%** 
            {'more' if service_ratio > 1 else 'less'} services per resident than the comparison average.
            
            **This suggests:** {'Eastchester residents may be paying comparable taxes but receiving fewer services' if service_ratio < 0.9 else 'Eastchester provides good value for tax dollars' if service_ratio > 1.1 else 'Eastchester provides average value for tax dollars'}.
            """)
            
            # Detailed tax breakdown table
            st.subheader("📋 Detailed Tax Breakdown")
            
            detail_tax_df = pd.DataFrame([
                {
                    'Municipality': 'Eastchester Area (Combined)',
                    'Total Tax': combined_eastchester.weighted_avg_tax_per_taxpayer,
                    'Tax per sqft': combined_eastchester.weighted_avg_tax_per_sqft,
                    'Municipal Tax': combined_eastchester.weighted_avg_municipal_tax_per_sqft * typical_sqft,
                    'Municipal Tax per sqft': combined_eastchester.weighted_avg_municipal_tax_per_sqft,
                    'Services per Resident': comparison.eastchester.per_resident_cost,
                }
            ])
            
            for muni_key, burden in all_burdens.items():
                if muni_key in ['scarsdale', 'pelham', 'larchmont']:
                    # Map tax burden keys to comparison_towns keys
                    town_key_map = {
                        'scarsdale': 'scarsdale',
                        'pelham': 'pelham',
                        'larchmont': 'larchmont',
                    }
                    town = comparison.comparison_towns.get(town_key_map.get(muni_key, muni_key), None)
                    if town:
                        detail_tax_df = pd.concat([
                            detail_tax_df,
                            pd.DataFrame([{
                                'Municipality': burden.municipality,
                                'Total Tax': burden.tax_per_taxpayer,
                                'Tax per sqft': burden.tax_per_sqft,
                                'Municipal Tax': burden.municipal_tax_per_taxpayer,
                                'Municipal Tax per sqft': burden.municipal_tax_per_sqft,
                                'Services per Resident': town.per_resident_cost,
                            }])
                        ], ignore_index=True)
            
            # Calculate value ratio
            detail_tax_df['Tax to Services Ratio'] = (
                detail_tax_df['Municipal Tax per sqft'] / detail_tax_df['Services per Resident'] * 1000
            ).round(2)
            
            # Format for display
            display_tax_df = detail_tax_df.copy()
            for col in ['Total Tax', 'Tax per sqft', 'Municipal Tax', 'Municipal Tax per sqft', 'Services per Resident']:
                if col in display_tax_df.columns:
                    display_tax_df[col] = display_tax_df[col].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) else x)
            
            st.dataframe(display_tax_df, use_container_width=True, hide_index=True)
            
            # Individual municipality breakdown for Eastchester area
            with st.expander("🏘️ Eastchester Area Individual Municipalities"):
                st.write("**Breakdown by Municipality:**")
                for muni_key, burden in combined_eastchester.tax_burdens.items():
                    st.write(f"**{burden.municipality}:**")
                    st.write(f"- Total Tax: ${burden.annual_tax:,.0f}/year")
                    st.write(f"- Tax per sqft: ${burden.tax_per_sqft:.2f}")
                    st.write(f"- Municipal Tax (Town+Village): ${burden.municipal_tax_only:,.0f}/year")
                    st.write(f"- Municipal Tax per sqft: ${burden.municipal_tax_per_sqft:.2f}")
                    st.write(f"- Effective Tax Rate: {burden.effective_rate:.2f}%")
                    st.write("")
            
            st.divider()
            
            # =====================================================================
            # DEEP MUNICIPAL TAX ANALYSIS
            # =====================================================================
            st.subheader("🔍 Deep Analysis: Municipal Tax vs Services")
            st.write("Comparing municipal tax rates (town+village only) against services and budgets provided")
            
            try:
                # Get detailed efficiency analysis
                efficiency_analysis = comparison.analyze_municipal_tax_efficiency(typical_home, typical_sqft)
                municipal_concerns = comparison.find_municipal_tax_concerns(typical_home, typical_sqft)
                
                # Summary metrics
                col1, col2, col3, col4 = st.columns(4)
                
                eastchester_eff = efficiency_analysis['eastchester_area']
                comp_avg = efficiency_analysis.get('comparison_averages', {})
                
                with col1:
                    st.metric(
                        "Eastchester Area\nMunicipal Tax per sqft",
                        f"${eastchester_eff['municipal_tax_per_sqft']:.2f}",
                        f"{((eastchester_eff['municipal_tax_per_sqft'] / comp_avg.get('municipal_tax_per_sqft', 1)) - 1) * 100:+.1f}% vs avg" if comp_avg.get('municipal_tax_per_sqft') else ""
                    )
                
                with col2:
                    st.metric(
                        "Eastchester Area\nServices per Resident",
                        f"${eastchester_eff['services_per_resident']:.2f}",
                        f"{((eastchester_eff['services_per_resident'] / comp_avg.get('services_per_resident', 1)) - 1) * 100:+.1f}% vs avg" if comp_avg.get('services_per_resident') else ""
                    )
                
                with col3:
                    efficiency_ratio = eastchester_eff['municipal_tax_efficiency']
                    avg_efficiency = comp_avg.get('municipal_tax_efficiency', 0)
                    st.metric(
                        "Tax Efficiency\n(Services per $1 municipal tax)",
                        f"{efficiency_ratio:.2f}x",
                        f"{((efficiency_ratio / avg_efficiency) - 1) * 100:+.1f}% vs avg" if avg_efficiency > 0 else ""
                    )
                    st.caption("Higher = better value")
                
                with col4:
                    if municipal_concerns:
                        st.metric(
                            "Key Concerns",
                            len(municipal_concerns),
                            "Issues identified"
                        )
                    else:
                        st.metric(
                            "Status",
                            "✅ Good",
                            "No major concerns"
                        )
                
                # Municipal tax efficiency concerns
                if municipal_concerns:
                    st.subheader("⚠️ Municipal Tax Value Concerns")
                    for i, concern in enumerate(municipal_concerns, 1):
                        severity_color = {'high': '🔴', 'medium': '🟡', 'low': '🟢'}.get(concern.get('severity', 'medium'), '🟡')
                        
                        with st.expander(f"{severity_color} {i}. {concern['category']}: {concern['issue']}", expanded=True):
                            col_a, col_b = st.columns(2)
                            
                            with col_a:
                                st.write("**Municipal Tax Rates:**")
                                st.write(f"- Eastchester: {concern.get('eastchester_municipal_tax_per_sqft', 'N/A')}/sqft")
                                st.write(f"- Comparison Avg: {concern.get('comparison_avg_municipal_tax_per_sqft', 'N/A')}/sqft")
                                if 'tax_difference' in concern:
                                    st.write(f"- Difference: {concern['tax_difference']}")
                            
                            with col_b:
                                st.write("**Services Provided:**")
                                st.write(f"- Eastchester: {concern.get('eastchester_services', 'N/A')}/resident")
                                st.write(f"- Comparison Avg: {concern.get('comparison_avg_services', 'N/A')}/resident")
                                if 'services_difference' in concern:
                                    st.write(f"- Difference: {concern['services_difference']}")
                            
                            st.write("")
                            st.write(f"**Impact:** {concern['impact']}")
                            if 'efficiency_difference' in concern:
                                st.write(f"**Efficiency Difference:** {concern['efficiency_difference']}")
                
                # Municipal tax vs services scatter plot
                st.subheader("📊 Municipal Tax Rate vs Services Provided")
                
                scatter_data = []
                
                # Add Eastchester area
                scatter_data.append({
                    'Municipality': 'Eastchester Area\n(Combined)',
                    'Municipal Tax per sqft': eastchester_eff['municipal_tax_per_sqft'],
                    'Services per Resident': eastchester_eff['services_per_resident'],
                    'Efficiency': eastchester_eff['municipal_tax_efficiency'],
                    'Type': 'Eastchester Area'
                })
                
                # Add comparison towns
                for town_name, town_data in efficiency_analysis['comparison_towns'].items():
                    scatter_data.append({
                        'Municipality': town_data['municipality'],
                        'Municipal Tax per sqft': town_data['municipal_tax_per_sqft'],
                        'Services per Resident': town_data['services_per_resident'],
                        'Efficiency': town_data['municipal_tax_efficiency'],
                        'Type': 'Comparison Town'
                    })
                
                scatter_df = pd.DataFrame(scatter_data)
                
                fig = px.scatter(
                    scatter_df,
                    x='Municipal Tax per sqft',
                    y='Services per Resident',
                    size='Efficiency',
                    color='Type',
                    hover_name='Municipality',
                    hover_data=['Efficiency'],
                    title='Municipal Tax Rate vs Services: Value Analysis',
                    labels={
                        'Municipal Tax per sqft': 'Municipal Tax per sqft ($)',
                        'Services per Resident': 'Services per Resident ($)',
                        'Efficiency': 'Efficiency (Services per $1 tax)'
                    },
                    color_discrete_map={
                        'Eastchester Area': '#3498db',
                        'Comparison Town': '#e74c3c'
                    }
                )
                fig.update_layout(height=500)
                st.plotly_chart(fig, use_container_width=True)
                
                # Interpretation
                st.info("""
                **Chart Interpretation:**
                - **X-axis**: Municipal tax per sqft (what residents pay)
                - **Y-axis**: Services per resident (what residents receive)
                - **Bubble size**: Efficiency ratio (larger = better value)
                - **Ideal position**: Upper left (low tax, high services) = best value
                - **Worst position**: Lower right (high tax, low services) = poor value
                """)
                
                # Detailed efficiency table
                st.subheader("📋 Municipal Tax Efficiency Comparison")
                
                efficiency_df = pd.DataFrame([
                    {
                        'Municipality': 'Eastchester Area (Combined)',
                        'Municipal Tax per sqft': eastchester_eff['municipal_tax_per_sqft'],
                        'Municipal Tax per Taxpayer': eastchester_eff['municipal_tax_per_taxpayer'],
                        'Services per Resident': eastchester_eff['services_per_resident'],
                        'Efficiency Ratio': eastchester_eff['municipal_tax_efficiency'],
                        'Municipal Tax % of Total': eastchester_eff.get('municipal_tax_rate', 0),
                    }
                ])
                
                for town_name, town_data in efficiency_analysis['comparison_towns'].items():
                    efficiency_df = pd.concat([
                        efficiency_df,
                        pd.DataFrame([{
                            'Municipality': town_data['municipality'],
                            'Municipal Tax per sqft': town_data['municipal_tax_per_sqft'],
                            'Municipal Tax per Taxpayer': town_data['municipal_tax_per_taxpayer'],
                            'Services per Resident': town_data['services_per_resident'],
                            'Efficiency Ratio': town_data['municipal_tax_efficiency'],
                            'Municipal Tax % of Total': town_data['municipal_tax_rate'],
                        }])
                    ], ignore_index=True)
                
                # Add comparison average row
                if comp_avg:
                    efficiency_df = pd.concat([
                        efficiency_df,
                        pd.DataFrame([{
                            'Municipality': '**Comparison Average**',
                            'Municipal Tax per sqft': comp_avg['municipal_tax_per_sqft'],
                            'Municipal Tax per Taxpayer': comp_avg.get('municipal_tax_per_resident', 0) * (typical_sqft / 2000),
                            'Services per Resident': comp_avg['services_per_resident'],
                            'Efficiency Ratio': comp_avg['municipal_tax_efficiency'],
                            'Municipal Tax % of Total': 0,
                        }])
                    ], ignore_index=True)
                
                # Format for display
                display_eff_df = efficiency_df.copy()
                for col in ['Municipal Tax per sqft', 'Municipal Tax per Taxpayer', 'Services per Resident']:
                    if col in display_eff_df.columns:
                        display_eff_df[col] = display_eff_df[col].apply(lambda x: f"${x:,.2f}" if isinstance(x, (int, float)) and x > 0 else x)
                
                display_eff_df['Efficiency Ratio'] = display_eff_df['Efficiency Ratio'].apply(lambda x: f"{x:.2f}x" if isinstance(x, (int, float)) and x > 0 else x)
                display_eff_df['Municipal Tax % of Total'] = display_eff_df['Municipal Tax % of Total'].apply(lambda x: f"{x:.1f}%" if isinstance(x, (int, float)) and x > 0 else x)
                
                st.dataframe(display_eff_df, use_container_width=True, hide_index=True)
                
                # Key insights
                st.subheader("💡 Key Insights")
                
                if eastchester_eff['municipal_tax_efficiency'] < comp_avg.get('municipal_tax_efficiency', 1) * 0.9:
                    st.warning(f"""
                    **⚠️ Lower Efficiency:** Eastchester area provides **{((comp_avg.get('municipal_tax_efficiency', 1) / eastchester_eff['municipal_tax_efficiency']) - 1) * 100:.1f}% less** 
                    services per dollar of municipal tax compared to the average of comparison towns.
                    
                    This suggests residents are paying similar municipal tax rates but receiving fewer services.
                    """)
                elif eastchester_eff['municipal_tax_efficiency'] > comp_avg.get('municipal_tax_efficiency', 1) * 1.1:
                    st.success(f"""
                    **✅ Higher Efficiency:** Eastchester area provides **{((eastchester_eff['municipal_tax_efficiency'] / comp_avg.get('municipal_tax_efficiency', 1)) - 1) * 100:.1f}% more** 
                    services per dollar of municipal tax compared to the average.
                    
                    This suggests good value for municipal tax dollars.
                    """)
                else:
                    st.info("""
                    **ℹ️ Average Efficiency:** Eastchester area provides services at a level comparable to other towns 
                    relative to municipal tax rates.
                    """)
                
            except Exception as eff_error:
                st.warning(f"Could not calculate efficiency analysis: {eff_error}")
        
        except Exception as tax_error:
            st.warning(f"Could not calculate tax burden analysis: {tax_error}")
            st.info("Tax burden analysis requires tax rate data from config.py")
        
    except Exception as e:
        st.warning(f"Could not load town budget data: {e}")
        st.info("""
        **Note:** Town budget data is being collected from municipal websites.
        
        This analysis compares:
        - **Eastchester** (Town) - unincorporated area
        - **Scarsdale** (Village/Town)
        - **Pelham** (Town)
        - **Larchmont** (Village)
        
        The comparison identifies areas where Eastchester may be spending less
        or more than comparable municipalities, which could indicate service
        level differences or efficiency issues.
        """)


def render_school_comparison():
    """Render school district budget comparison."""
    st.subheader("🎓 School District Budget Comparison")
    st.write("Comparing per-student costs: Combined Eastchester Area (3 districts) vs Scarsdale")
    
    try:
        comparison = compare_school_districts()
        
        # Summary metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Eastchester Area (Combined)",
                f"${comparison.eastchester_area.total_budget:,.0f}",
                f"${comparison.eastchester_area.per_student_cost:,.0f}/student"
            )
            st.caption(f"{comparison.eastchester_area.total_enrollment:,} students")
            st.caption(f"3 districts: Eastchester, Bronxville, Tuckahoe")
        
        with col2:
            st.metric(
                "Scarsdale UFSD",
                f"${comparison.scarsdale.total_budget:,.0f}",
                f"${comparison.scarsdale.per_student_cost:,.0f}/student"
            )
            st.caption(f"{comparison.scarsdale.enrollment:,} students")
            st.caption("Single district")
        
        with col3:
            diff = comparison.per_student_difference
            st.metric(
                "Difference",
                f"${abs(diff):,.0f}/student",
                f"{comparison.per_student_difference_pct:+.1f}%"
            )
            st.caption("Per-student cost difference")
        
        # Per-student comparison chart
        df = pd.DataFrame([
            {
                'District': 'Eastchester Area\n(Combined)',
                'Per Student': comparison.eastchester_area.per_student_cost,
                'Total Budget': comparison.eastchester_area.total_budget,
                'Enrollment': comparison.eastchester_area.total_enrollment,
            },
            {
                'District': 'Scarsdale UFSD',
                'Per Student': comparison.scarsdale.per_student_cost,
                'Total Budget': comparison.scarsdale.total_budget,
                'Enrollment': comparison.scarsdale.enrollment,
            }
        ])
        
        fig = px.bar(
            df,
            x='District',
            y='Per Student',
            color='District',
            title='School District Cost Per Student',
            labels={'Per Student': 'Cost Per Student ($)'},
            color_discrete_map={
                'Eastchester Area\n(Combined)': '#3498db',
                'Scarsdale UFSD': '#e74c3c'
            }
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Individual district breakdown
        st.subheader("📊 Individual District Breakdown")
        
        individual_df = pd.DataFrame([
            {
                'District': d.district_name,
                'Budget': d.total_budget,
                'Enrollment': d.enrollment,
                'Per Student': d.per_student_cost,
            }
            for d in comparison.eastchester_area.districts
        ])
        
        # Add Scarsdale for comparison
        individual_df = pd.concat([
            individual_df,
            pd.DataFrame([{
                'District': comparison.scarsdale.district_name,
                'Budget': comparison.scarsdale.total_budget,
                'Enrollment': comparison.scarsdale.enrollment,
                'Per Student': comparison.scarsdale.per_student_cost,
            }])
        ], ignore_index=True)
        
        # Format for display
        display_df = individual_df.copy()
        display_df['Budget'] = display_df['Budget'].apply(lambda x: f"${x:,.0f}")
        display_df['Enrollment'] = display_df['Enrollment'].apply(lambda x: f"{x:,}")
        display_df['Per Student'] = display_df['Per Student'].apply(lambda x: f"${x:,.0f}")
        display_df.columns = ['District', 'Total Budget', 'Enrollment', 'Per Student']
        
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        # Key findings
        st.info(f"""
        **Key Finding:** {'Scarsdale' if comparison.per_student_difference > 0 else 'Eastchester Area'} spends 
        **${abs(comparison.per_student_difference):,.0f} more per student** on education.
        
        **Difference:** {abs(comparison.per_student_difference_pct):.1f}% 
        ({'+' if comparison.per_student_difference > 0 else ''}{comparison.per_student_difference_pct:.1f}%)
        
        **Note:** Eastchester area has 3 separate school districts (Eastchester, Bronxville, Tuckahoe) 
        while Scarsdale has a single unified district.
        """)
        
        # Detailed breakdown
        with st.expander("📊 Detailed Breakdown"):
            st.write("**Eastchester Area (Combined):**")
            st.write(f"- Total Budget: ${comparison.eastchester_area.total_budget:,.0f}")
            st.write(f"- Total Enrollment: {comparison.eastchester_area.total_enrollment:,}")
            st.write(f"- Per Student: ${comparison.eastchester_area.per_student_cost:,.2f}")
            st.write(f"- Number of Districts: {len(comparison.eastchester_area.districts)}")
            st.write("")
            st.write("**Individual Districts:**")
            for district in comparison.eastchester_area.districts:
                st.write(f"- **{district.district_name}**:")
                st.write(f"  - Budget: ${district.total_budget:,.0f}")
                st.write(f"  - Enrollment: {district.enrollment:,}")
                st.write(f"  - Per Student: ${district.per_student_cost:,.2f}")
            
            st.write("")
            st.write("**Scarsdale UFSD:**")
            st.write(f"- Total Budget: ${comparison.scarsdale.total_budget:,.0f}")
            st.write(f"- Enrollment: {comparison.scarsdale.enrollment:,}")
            st.write(f"- Per Student: ${comparison.scarsdale.per_student_cost:,.2f}")
            st.write(f"- Fiscal Year: {comparison.scarsdale.fiscal_year}")
            
            st.write("")
            st.write("**Comparison:**")
            st.write(f"- Per Student Difference: ${comparison.per_student_difference:,.2f}")
            st.write(f"- Percentage Difference: {comparison.per_student_difference_pct:+.1f}%")
            st.write(f"- Total Budget Difference: ${comparison.total_budget_difference:,.0f}")
            st.write(f"- Enrollment Difference: {comparison.enrollment_difference:,} students")
        
        # Data source
        st.caption(f"📅 Data collected: {comparison.eastchester_area.districts[0].collection_date}")
        st.caption(f"📊 Sources: School district budgets and websites")
        
    except Exception as e:
        st.warning(f"Could not load school budget data: {e}")
        st.info("""
        **Note:** School budget data is being collected from district websites.
        
        **Eastchester Area Districts:**
        - Eastchester UFSD (covers Eastchester unincorporated)
        - Bronxville UFSD (covers Bronxville)
        - Tuckahoe UFSD (covers Tuckahoe)
        
        **Scarsdale:**
        - Scarsdale UFSD (single unified district)
        
        The comparison shows combined budgets and enrollment for the Eastchester area
        vs Scarsdale's single district to understand per-student spending differences.
        """)


def render_fire_comparison():
    """Render fire department budget comparison."""
    st.subheader("🔥 Fire Department Budget Comparison")
    st.write("Comparing per-resident fire department costs: Eastchester vs Scarsdale")
    
    try:
        comparison = compare_fire_departments()
        
        # Create comparison chart
        df = pd.DataFrame([
            {
                'Department': 'Eastchester FD',
                'Total Budget': comparison.eastchester_budget.total_budget,
                'Population': comparison.eastchester_budget.population,
                'Per Resident': comparison.eastchester_budget.per_resident_cost,
                'Coverage': comparison.eastchester_budget.coverage_area,
            },
            {
                'Department': 'Scarsdale FD',
                'Total Budget': comparison.scarsdale_budget.total_budget,
                'Population': comparison.scarsdale_budget.population,
                'Per Resident': comparison.scarsdale_budget.per_resident_cost,
                'Coverage': comparison.scarsdale_budget.coverage_area,
            }
        ])
        
        # Side-by-side comparison
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Eastchester FD Budget",
                f"${comparison.eastchester_budget.total_budget:,.0f}",
                f"${comparison.eastchester_budget.per_resident_cost:.2f}/resident"
            )
            st.caption(f"Coverage: {comparison.eastchester_budget.coverage_area}")
            st.caption(f"Population: {comparison.eastchester_budget.population:,}")
        
        with col2:
            st.metric(
                "Scarsdale FD Budget",
                f"${comparison.scarsdale_budget.total_budget:,.0f}",
                f"${comparison.scarsdale_budget.per_resident_cost:.2f}/resident"
            )
            st.caption(f"Coverage: {comparison.scarsdale_budget.coverage_area}")
            st.caption(f"Population: {comparison.scarsdale_budget.population:,}")
        
        # Per resident comparison chart
        fig = px.bar(
            df,
            x='Department',
            y='Per Resident',
            color='Department',
            title='Fire Department Cost Per Resident',
            labels={'Per Resident': 'Cost Per Resident ($)'},
            color_discrete_map={
                'Eastchester FD': '#3498db',
                'Scarsdale FD': '#e74c3c'
            }
        )
        fig.update_layout(showlegend=False, height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Key findings
        st.info(f"""
        **Key Finding:** {'Scarsdale' if comparison.per_resident_difference > 0 else 'Eastchester'} spends 
        **${abs(comparison.per_resident_difference):.2f} more per resident** on fire services.
        
        **Difference:** {abs(comparison.per_resident_difference_pct):.1f}% 
        ({'+' if comparison.per_resident_difference > 0 else ''}{comparison.per_resident_difference_pct:.1f}%)
        """)
        
        # Detailed breakdown
        with st.expander("📊 Detailed Breakdown"):
            st.write("**Eastchester Fire Department:**")
            st.write(f"- Total Budget: ${comparison.eastchester_budget.total_budget:,.0f}")
            st.write(f"- Population Served: {comparison.eastchester_budget.population:,}")
            st.write(f"- Per Resident: ${comparison.eastchester_budget.per_resident_cost:.2f}")
            st.write(f"- Coverage: {comparison.eastchester_budget.coverage_area}")
            st.write(f"- Fiscal Year: {comparison.eastchester_budget.fiscal_year}")
            
            st.write("")
            st.write("**Scarsdale Fire Department:**")
            st.write(f"- Total Budget: ${comparison.scarsdale_budget.total_budget:,.0f}")
            st.write(f"- Population Served: {comparison.scarsdale_budget.population:,}")
            st.write(f"- Per Resident: ${comparison.scarsdale_budget.per_resident_cost:.2f}")
            st.write(f"- Coverage: {comparison.scarsdale_budget.coverage_area}")
            st.write(f"- Fiscal Year: {comparison.scarsdale_budget.fiscal_year}")
            
            st.write("")
            st.write("**Comparison:**")
            st.write(f"- Per Resident Difference: ${comparison.per_resident_difference:,.2f}")
            st.write(f"- Percentage Difference: {comparison.per_resident_difference_pct:+.1f}%")
            st.write(f"- Total Budget Difference: ${comparison.total_budget_difference:,.0f}")
        
        # Data source
        st.caption(f"📅 Data collected: {comparison.eastchester_budget.collection_date}")
        st.caption(f"📊 Sources: {comparison.eastchester_budget.data_source}, {comparison.scarsdale_budget.data_source}")
        
    except Exception as e:
        st.warning(f"Could not load fire department budget data: {e}")
        st.info("""
        **Note:** Fire department budget data is being collected from municipal websites.
        The Eastchester Fire Department covers:
        - Eastchester (unincorporated)
        - Tuckahoe
        - Bronxville
        
        This shared service model may result in different per-resident costs compared to 
        municipalities with dedicated fire departments.
        """)


def render_insights(report):
    """Render key insights section."""
    st.subheader("💡 Key Insights")
    
    for insight in report.insights:
        st.write(f"• {insight}")
    
    if report.eastchester_comparison:
        st.subheader("🏘️ Eastchester Area Analysis")
        for key, value in report.eastchester_comparison.items():
            st.write(f"**{key}:** {value}")


def render_data_table(report):
    """Render full data table."""
    st.subheader("📋 Full Data Table")
    
    df = report.to_dataframe()
    
    # Format numeric columns
    format_dict = {
        'value_per_sqft_median': '${:,.0f}',
        'value_per_sqft_mean': '${:,.0f}',
        'tax_per_sqft_median': '${:,.2f}',
        'effective_rate_median': '{:.2f}%',
        'sale_price_median': '${:,.0f}',
        'monthly_tax_typical': '${:,.0f}',
        'tax_efficiency_ratio': '{:.2f}',
    }
    
    # Select and rename columns for display
    display_cols = [
        'municipality', 'sample_size', 'value_per_sqft_median', 
        'tax_per_sqft_median', 'effective_rate_median', 
        'sale_price_median', 'tax_efficiency_ratio'
    ]
    
    df_display = df[display_cols].copy()
    df_display.columns = [
        'Municipality', 'Sales', 'Value/sqft', 'Tax/sqft', 
        'Eff. Rate', 'Median Price', 'Efficiency'
    ]
    
    st.dataframe(df_display, use_container_width=True, hide_index=True)
    
    # Download buttons
    col1, col2, col3 = st.columns(3)
    
    with col1:
        csv = df.to_csv(index=False)
        st.download_button(
            "📥 Download CSV",
            csv,
            "eastchester_analysis.csv",
            "text/csv",
            use_container_width=True
        )
    
    with col2:
        # Export as JSON
        json_data = df.to_json(orient='records', indent=2)
        st.download_button(
            "📥 Download JSON",
            json_data,
            "eastchester_analysis.json",
            "application/json",
            use_container_width=True
        )
    
    with col3:
        # Export summary report
        summary_text = report.summary()
        st.download_button(
            "📥 Download Report",
            summary_text,
            "eastchester_report.txt",
            "text/plain",
            use_container_width=True
        )


# =============================================================================
# Main Dashboard
# =============================================================================

def create_dashboard():
    """Create and run the Streamlit dashboard."""
    configure_page()
    
    # Sidebar
    controls = render_sidebar()
    
    # Header
    render_header()
    
    # Load data
    with st.spinner("Loading data..."):
        dataset, is_real_data = load_data()
        report = generate_comparison_report(dataset)
    
    # Filter to selected municipalities
    filtered_metrics = {
        k: v for k, v in report.metrics.items() 
        if k in controls['selected_munis']
    }
    report.metrics = filtered_metrics
    
    # Key metrics
    render_key_metrics(report)
    
    st.divider()
    
    # Main tabs
    tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
        "🗺️ Map", "📊 Comparison", "🧮 Calculator", "⚡ Efficiency", "🔥 Fire Dept", "🎓 Schools", "🏛️ Town Budget", "📋 Data"
    ])
    
    with tab1:
        st.subheader("📍 Geographic View")
        render_map_view(report)
        st.divider()
        render_insights(report)
    
    with tab2:
        render_comparison_charts(report)
        st.divider()
        render_insights(report)
    
    with tab3:
        render_tax_calculator(
            controls['home_value'],
            controls['sqft'],
            controls['selected_munis']
        )
        render_tax_breakdown(controls['home_value'], controls['selected_munis'])
    
    with tab4:
        render_efficiency_analysis(report)
    
    with tab5:
        render_fire_comparison()
    
    with tab6:
        render_school_comparison()
    
    with tab7:
        render_town_budget_comparison()
    
    with tab8:
        render_data_table(report)
    
    # Footer
    st.divider()
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.caption("📊 Tax rates from municipal budgets & NY State ORPTS")
    with col2:
        if is_real_data:
            st.caption("✅ Using real sales data")
        else:
            st.caption("⚠️ Using sample data - add real data to data/raw/sales/")
    with col3:
        st.caption(f"📅 Last updated: {report.generated_date}")


# =============================================================================
# Entry Point
# =============================================================================

if __name__ == "__main__":
    create_dashboard()


