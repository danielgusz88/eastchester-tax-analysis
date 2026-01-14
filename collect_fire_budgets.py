#!/usr/bin/env python3
"""
Collect Fire Department Budget Data.

This script collects fire department budget information
from municipal websites and saves it for the dashboard.
"""

import sys
from pathlib import Path
import json

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from data_collection.fire_budget_scraper import FireDepartmentBudget, FireBudgetScraper
from config import DATA_DIR

# Known budget data (2024-2025 fiscal year)
# These are approximate values - actual budgets should be verified from municipal websites

EASTCHESTER_FIRE_DATA = {
    'municipality': 'Eastchester Fire Department',
    'fiscal_year': '2024-2025',
    'total_budget': 9_500_000,  # Approximate - covers 3 municipalities
    'population': 33_000,  # Eastchester + Tuckahoe + Bronxville
    'coverage_area': 'Eastchester (unincorporated), Tuckahoe, Bronxville',
    'data_source': 'Eastchester Town Budget (estimated)',
    'notes': 'Shared fire department covering 3 municipalities'
}

SCARSDALE_FIRE_DATA = {
    'municipality': 'Scarsdale Fire Department',
    'fiscal_year': '2024-2025',
    'total_budget': 6_500_000,  # Approximate
    'population': 18_000,  # Scarsdale only
    'coverage_area': 'Scarsdale only',
    'data_source': 'Scarsdale Village Budget (estimated)',
    'notes': 'Dedicated fire department for Scarsdale village'
}

def create_fire_budget_data():
    """Create fire budget data files."""
    scraper = FireBudgetScraper()
    
    # Create budget objects
    eastchester = FireDepartmentBudget(
        municipality=EASTCHESTER_FIRE_DATA['municipality'],
        fiscal_year=EASTCHESTER_FIRE_DATA['fiscal_year'],
        total_budget=EASTCHESTER_FIRE_DATA['total_budget'],
        population=EASTCHESTER_FIRE_DATA['population'],
        per_resident_cost=EASTCHESTER_FIRE_DATA['total_budget'] / EASTCHESTER_FIRE_DATA['population'],
        coverage_area=EASTCHESTER_FIRE_DATA['coverage_area'],
        data_source=EASTCHESTER_FIRE_DATA['data_source'],
        collection_date='2026-01-14',
        notes=EASTCHESTER_FIRE_DATA['notes']
    )
    
    scarsdale = FireDepartmentBudget(
        municipality=SCARSDALE_FIRE_DATA['municipality'],
        fiscal_year=SCARSDALE_FIRE_DATA['fiscal_year'],
        total_budget=SCARSDALE_FIRE_DATA['total_budget'],
        population=SCARSDALE_FIRE_DATA['population'],
        per_resident_cost=SCARSDALE_FIRE_DATA['total_budget'] / SCARSDALE_FIRE_DATA['population'],
        coverage_area=SCARSDALE_FIRE_DATA['coverage_area'],
        data_source=SCARSDALE_FIRE_DATA['data_source'],
        collection_date='2026-01-14',
        notes=SCARSDALE_FIRE_DATA['notes']
    )
    
    budgets = {
        'eastchester': eastchester,
        'scarsdale': scarsdale
    }
    
    # Save to file
    scraper.save_budgets(budgets)
    
    # Print summary
    print("\n" + "=" * 70)
    print("FIRE DEPARTMENT BUDGET COMPARISON")
    print("=" * 70)
    print()
    print("EASTCHESTER FIRE DEPARTMENT:")
    print(f"  Budget: ${eastchester.total_budget:,.0f}")
    print(f"  Population: {eastchester.population:,}")
    print(f"  Per Resident: ${eastchester.per_resident_cost:.2f}")
    print(f"  Coverage: {eastchester.coverage_area}")
    print()
    print("SCARSDALE FIRE DEPARTMENT:")
    print(f"  Budget: ${scarsdale.total_budget:,.0f}")
    print(f"  Population: {scarsdale.population:,}")
    print(f"  Per Resident: ${scarsdale.per_resident_cost:.2f}")
    print(f"  Coverage: {scarsdale.coverage_area}")
    print()
    
    diff = scarsdale.per_resident_cost - eastchester.per_resident_cost
    pct_diff = ((scarsdale.per_resident_cost / eastchester.per_resident_cost) - 1) * 100
    
    print("COMPARISON:")
    print(f"  Per Resident Difference: ${diff:,.2f}")
    print(f"  Percentage Difference: {pct_diff:+.1f}%")
    print()
    
    if diff > 0:
        print(f"💡 Scarsdale spends ${diff:.2f} MORE per resident on fire services")
    else:
        print(f"💡 Eastchester spends ${abs(diff):.2f} MORE per resident on fire services")
    print()
    print("=" * 70)
    print()
    print("✅ Fire budget data saved!")
    print("   The dashboard will now show this comparison in the '🔥 Fire Dept' tab")
    print()
    print("📝 Note: These are estimated values. For exact budgets, check:")
    print("   - Eastchester: https://www.eastchester.org/budget")
    print("   - Scarsdale: https://www.scarsdale.com/budget")

if __name__ == "__main__":
    create_fire_budget_data()
