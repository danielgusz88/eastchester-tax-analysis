#!/usr/bin/env python3
"""
Python launcher for the Eastchester Tax Analysis Dashboard.
This works even if streamlit isn't in PATH.
"""

import sys
import subprocess
from pathlib import Path

def check_and_install_dependencies():
    """Check if required packages are installed."""
    required = ['streamlit', 'plotly', 'pandas', 'numpy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)
    
    if missing:
        print("⚠️  Missing dependencies:", ", ".join(missing))
        print("📦 Installing dependencies...")
        print("   (This may take a minute)")
        print()
        
        try:
            subprocess.check_call([
                sys.executable, '-m', 'pip', 'install', 
                '--user', 'streamlit', 'plotly', 'pandas', 'numpy', 'seaborn', 'matplotlib'
            ])
            print("✅ Dependencies installed!")
            print()
        except subprocess.CalledProcessError:
            print("❌ Failed to install dependencies automatically.")
            print()
            print("Please install manually:")
            print("  pip3 install streamlit plotly pandas numpy seaborn matplotlib")
            print()
            print("Or:")
            print("  python3 -m pip install --user streamlit plotly pandas numpy seaborn matplotlib")
            sys.exit(1)

def main():
    """Launch the dashboard."""
    # Change to script directory
    script_dir = Path(__file__).parent.absolute()
    import os
    os.chdir(script_dir)
    
    print("=" * 70)
    print("🏠 Eastchester Tax Analysis Dashboard")
    print("=" * 70)
    print()
    
    # Check dependencies
    check_and_install_dependencies()
    
    # Check if dashboard file exists
    dashboard_path = script_dir / 'src' / 'visualization' / 'dashboard.py'
    if not dashboard_path.exists():
        print(f"❌ Dashboard not found at: {dashboard_path}")
        print(f"   Current directory: {os.getcwd()}")
        sys.exit(1)
    
    print("📊 Launching dashboard...")
    print("   Dashboard will open at: http://localhost:8501")
    print()
    print("   Press Ctrl+C to stop the dashboard")
    print("=" * 70)
    print()
    
    # Launch streamlit
    try:
        subprocess.run([
            sys.executable, '-m', 'streamlit', 'run',
            str(dashboard_path),
            '--server.headless', 'true'
        ])
    except KeyboardInterrupt:
        print()
        print("👋 Dashboard stopped.")
    except FileNotFoundError:
        print("❌ Streamlit not found. Trying alternative method...")
        try:
            import streamlit.web.cli as stcli
            sys.argv = ['streamlit', 'run', str(dashboard_path)]
            stcli.main()
        except Exception as e:
            print(f"❌ Error: {e}")
            print()
            print("Please install streamlit:")
            print("  pip3 install streamlit")
            sys.exit(1)

if __name__ == "__main__":
    main()
