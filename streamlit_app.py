"""
Streamlit Cloud entry point.

This file is required for Streamlit Community Cloud deployment.
It simply imports and runs the main dashboard.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

# Import and run the dashboard
from visualization.dashboard import create_dashboard

if __name__ == "__main__":
    create_dashboard()
