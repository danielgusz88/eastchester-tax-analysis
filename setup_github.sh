#!/bin/bash
# Setup script for GitHub and Streamlit Cloud deployment

echo "🚀 Setting up GitHub repository for Streamlit Cloud..."
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "❌ Git is not installed. Please install it first."
    exit 1
fi

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo "📦 Initializing git repository..."
    git init
    echo "✅ Git repository initialized"
else
    echo "✅ Git repository already exists"
fi

# Add all files
echo ""
echo "📝 Adding files to git..."
git add .

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo "ℹ️  No changes to commit (everything already committed)"
else
    echo "💾 Committing files..."
    git commit -m "Initial commit: Eastchester Tax Analysis Dashboard"
    echo "✅ Files committed"
fi

echo ""
echo "=" * 70
echo "✅ Local git repository is ready!"
echo "=" * 70
echo ""
echo "📋 Next steps:"
echo ""
echo "1. Create a GitHub repository:"
echo "   Go to https://github.com/new"
echo "   - Name: eastchester-tax-analysis (or your choice)"
echo "   - Make it PUBLIC (required for free Streamlit Cloud)"
echo "   - DO NOT initialize with README/gitignore"
echo ""
echo "2. Connect and push (replace YOUR_USERNAME):"
echo "   git remote add origin https://github.com/YOUR_USERNAME/eastchester-tax-analysis.git"
echo "   git branch -M main"
echo "   git push -u origin main"
echo ""
echo "3. Deploy to Streamlit Cloud:"
echo "   Go to https://share.streamlit.io/"
echo "   - Click 'New app'"
echo "   - Select your repository"
echo "   - Main file: streamlit_app.py"
echo "   - Click 'Deploy'"
echo ""
echo "Your dashboard will be live at:"
echo "   https://YOUR_USERNAME-eastchester-tax-analysis.streamlit.app"
echo ""
