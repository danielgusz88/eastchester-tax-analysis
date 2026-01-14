"""
Map Visualization Component for Dashboard.

Creates interactive maps showing municipalities with
color-coded metrics.
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Municipality coordinates (approximate centers in Westchester County)
MUNICIPALITY_COORDS = {
    'bronxville': {
        'lat': 40.9381,
        'lon': -73.8321,
        'name': 'Bronxville'
    },
    'eastchester_unincorp': {
        'lat': 40.9556,
        'lon': -73.8156,
        'name': 'Eastchester (Unincorporated)'
    },
    'tuckahoe': {
        'lat': 40.9504,
        'lon': -73.8274,
        'name': 'Tuckahoe'
    },
    'scarsdale': {
        'lat': 40.9881,
        'lon': -73.7976,
        'name': 'Scarsdale'
    },
    'larchmont': {
        'lat': 40.9276,
        'lon': -73.7528,
        'name': 'Larchmont'
    },
    'mamaroneck_village': {
        'lat': 40.9489,
        'lon': -73.7326,
        'name': 'Mamaroneck (Village)'
    },
    'mamaroneck_town': {
        'lat': 40.9489,
        'lon': -73.7326,
        'name': 'Mamaroneck (Town)'
    },
    'pelham': {
        'lat': 40.9095,
        'lon': -73.8071,
        'name': 'Pelham'
    },
    'pelham_manor': {
        'lat': 40.8954,
        'lon': -73.8082,
        'name': 'Pelham Manor'
    },
    'rye_city': {
        'lat': 40.9807,
        'lon': -73.6837,
        'name': 'Rye (City)'
    },
}


def create_value_map(metrics_df: pd.DataFrame, metric: str = 'value_per_sqft_median') -> go.Figure:
    """
    Create map showing municipalities colored by a metric.
    
    Args:
        metrics_df: DataFrame with municipality metrics
        metric: Column name to use for coloring
        
    Returns:
        Plotly figure
    """
    # Add coordinates
    df = metrics_df.copy()
    df['lat'] = df['municipality'].map(lambda x: MUNICIPALITY_COORDS.get(x, {}).get('lat', 40.95))
    df['lon'] = df['municipality'].map(lambda x: MUNICIPALITY_COORDS.get(x, {}).get('lon', -73.8))
    df['name'] = df['municipality'].map(lambda x: MUNICIPALITY_COORDS.get(x, {}).get('name', x))
    
    # Filter to municipalities with coordinates
    df = df[df['lat'].notna()]
    
    if len(df) == 0:
        return None
    
    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        size=metric,
        color=metric,
        hover_name='name',
        hover_data={
            'value_per_sqft_median': ':.0f',
            'tax_per_sqft_median': ':.2f',
            'effective_rate_median': ':.2f',
            'sample_size': True,
            'lat': False,
            'lon': False,
            'municipality': False,
        },
        color_continuous_scale='Blues',
        size_max=40,
        zoom=10,
        height=600,
        mapbox_style='open-street-map',
        title=f'Municipality Map: {metric.replace("_", " ").title()}'
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        mapbox=dict(
            center=dict(lat=40.95, lon=-73.8),
            zoom=10
        )
    )
    
    return fig


def create_tax_map(metrics_df: pd.DataFrame) -> go.Figure:
    """Create map colored by tax burden."""
    return create_value_map(metrics_df, 'tax_per_sqft_median')


def create_combined_map(metrics_df: pd.DataFrame) -> go.Figure:
    """Create map with both value (size) and tax (color)."""
    df = metrics_df.copy()
    df['lat'] = df['municipality'].map(lambda x: MUNICIPALITY_COORDS.get(x, {}).get('lat', 40.95))
    df['lon'] = df['municipality'].map(lambda x: MUNICIPALITY_COORDS.get(x, {}).get('lon', -73.8))
    df['name'] = df['municipality'].map(lambda x: MUNICIPALITY_COORDS.get(x, {}).get('name', x))
    
    df = df[df['lat'].notna()]
    
    if len(df) == 0:
        return None
    
    fig = px.scatter_mapbox(
        df,
        lat='lat',
        lon='lon',
        size='value_per_sqft_median',
        color='tax_per_sqft_median',
        hover_name='name',
        hover_data={
            'value_per_sqft_median': ':.0f',
            'tax_per_sqft_median': ':.2f',
            'effective_rate_median': ':.2f',
            'tax_efficiency_ratio': ':.2f',
            'lat': False,
            'lon': False,
        },
        color_continuous_scale='Reds',
        size_max=40,
        zoom=10,
        height=600,
        mapbox_style='open-street-map',
        title='Municipality Map: Size = Home Value, Color = Tax Burden'
    )
    
    fig.update_layout(
        margin=dict(l=0, r=0, t=40, b=0),
        mapbox=dict(
            center=dict(lat=40.95, lon=-73.8),
            zoom=10
        )
    )
    
    return fig
