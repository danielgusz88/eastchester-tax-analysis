#!/bin/bash
# Launch script for the Eastchester Tax Analysis Dashboard

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Change to project directory
cd "$SCRIPT_DIR"

# Check if we're in the right directory
if [ ! -f "src/visualization/dashboard.py" ]; then
    echo "❌ Error: Dashboard not found!"
    echo "   Current directory: $(pwd)"
    echo "   Expected: $SCRIPT_DIR"
    echo ""
    echo "Please run this script from the Eastchester project directory."
    exit 1
fi

echo "🏠 Starting Eastchester Tax Analysis Dashboard..."
echo ""

# Check if streamlit is installed
if ! command -v streamlit &> /dev/null; then
    echo "⚠️  Streamlit not found. Installing dependencies..."
    echo "   (This may take a minute)"
    echo ""
    python3 -m pip install --user streamlit plotly pandas numpy seaborn matplotlib
    if [ $? -ne 0 ]; then
        echo ""
        echo "❌ Failed to install dependencies."
        echo "   Please install manually:"
        echo "   pip3 install streamlit plotly pandas numpy seaborn matplotlib"
        exit 1
    fi
    echo ""
fi

# Launch dashboard
echo "📊 Launching dashboard at http://localhost:8501"
echo "   Press Ctrl+C to stop"
echo ""
python3 -m streamlit run src/visualization/dashboard.py
