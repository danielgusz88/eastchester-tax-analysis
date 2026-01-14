# 🚀 Quick Start Guide

## The Problem You Had

You were in the wrong directory (`website` instead of `Eastchester`) and streamlit wasn't installed.

## ✅ Solution - 3 Easy Ways to Launch

### Option 1: Python Launcher (RECOMMENDED - Works Everywhere)
```bash
cd /Users/dangusz/Eastchester
python3 launch_dashboard.py
```

This will:
- ✅ Automatically install dependencies if needed
- ✅ Check you're in the right directory
- ✅ Launch the dashboard

### Option 2: Bash Script
```bash
cd /Users/dangusz/Eastchester
./launch_dashboard.sh
```

### Option 3: Direct Command (After Installing)
```bash
cd /Users/dangusz/Eastchester
python3 -m pip install --user streamlit plotly pandas numpy seaborn matplotlib
python3 -m streamlit run src/visualization/dashboard.py
```

## 📍 Important: You Must Be in the Right Directory!

The dashboard files are in `/Users/dangusz/Eastchester/`

**Check your current directory:**
```bash
pwd
```

**If you're not in Eastchester, change to it:**
```bash
cd /Users/dangusz/Eastchester
```

## 🔧 If You Still Get Errors

### Error: "streamlit: command not found"
```bash
# Install streamlit
python3 -m pip install --user streamlit plotly pandas numpy seaborn matplotlib

# Then use python3 -m streamlit instead of just streamlit
python3 -m streamlit run src/visualization/dashboard.py
```

### Error: "No such file or directory"
Make sure you're in the Eastchester directory:
```bash
cd /Users/dangusz/Eastchester
ls -la  # Should show launch_dashboard.py, src/, data/, etc.
```

### Error: Permission denied
```bash
chmod +x launch_dashboard.sh
chmod +x launch_dashboard.py
```

## ✅ Success Looks Like This

When it works, you'll see:
```
======================================================================
🏠 Eastchester Tax Analysis Dashboard
======================================================================

📊 Launching dashboard...
   Dashboard will open at: http://localhost:8501

   Press Ctrl+C to stop the dashboard
======================================================================

  You can now view your Streamlit app in your browser.

  Local URL: http://localhost:8501
  Network URL: http://192.168.x.x:8501
```

Then your browser should automatically open to the dashboard!

## 🎯 Try This Now

```bash
# Step 1: Go to the right directory
cd /Users/dangusz/Eastchester

# Step 2: Run the Python launcher
python3 launch_dashboard.py
```

That's it! 🎉
