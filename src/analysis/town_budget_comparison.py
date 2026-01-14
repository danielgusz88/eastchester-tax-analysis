"""
Town Budget Comparison Analysis.

Compares Eastchester town budget against Scarsdale, Pelham, and Larchmont
to identify areas where Eastchester may underperform or overspend.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import sys
from typing import List

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_collection.town_budget_scraper import TownBudget, collect_town_budgets


@dataclass
class BudgetComparison:
    """Comparison of town budgets."""
    eastchester: TownBudget
    comparison_towns: dict[str, TownBudget]  # Scarsdale, Pelham, Larchmont
    
    def find_concerns(self) -> List[dict]:
        """
        Find 5 key concerns where Eastchester underperforms.
        
        Returns list of concerns with details.
        """
        concerns = []
        
        # Calculate averages for comparison towns
        comp_towns = list(self.comparison_towns.values())
        
        # 1. Parks & Recreation spending
        eastchester_parks = self.eastchester.per_resident_parks
        avg_parks = sum(t.per_resident_parks for t in comp_towns) / len(comp_towns)
        if eastchester_parks < avg_parks * 0.8:  # 20% below average
            concerns.append({
                'category': 'Parks & Recreation',
                'issue': 'Low spending on parks and recreation',
                'eastchester': f"${eastchester_parks:.2f}/resident",
                'comparison_avg': f"${avg_parks:.2f}/resident",
                'difference': f"${avg_parks - eastchester_parks:.2f} less per resident",
                'percentage': f"{((avg_parks / eastchester_parks) - 1) * 100:.1f}% below average",
                'impact': 'Residents may have fewer park amenities, programs, and recreational facilities',
                'severity': 'high' if eastchester_parks < avg_parks * 0.7 else 'medium'
            })
        
        # 2. Public Works spending
        eastchester_pw = self.eastchester.per_resident_public_works
        avg_pw = sum(t.per_resident_public_works for t in comp_towns) / len(comp_towns)
        if eastchester_pw < avg_pw * 0.85:
            concerns.append({
                'category': 'Public Works',
                'issue': 'Lower infrastructure spending',
                'eastchester': f"${eastchester_pw:.2f}/resident",
                'comparison_avg': f"${avg_pw:.2f}/resident",
                'difference': f"${avg_pw - eastchester_pw:.2f} less per resident",
                'percentage': f"{((avg_pw / eastchester_pw) - 1) * 100:.1f}% below average",
                'impact': 'Roads, sidewalks, and infrastructure may be in worse condition or maintained less frequently',
                'severity': 'high' if eastchester_pw < avg_pw * 0.75 else 'medium'
            })
        
        # 3. Total per-resident spending
        eastchester_total = self.eastchester.per_resident_cost
        avg_total = sum(t.per_resident_cost for t in comp_towns) / len(comp_towns)
        if eastchester_total > avg_total * 1.1:  # 10% above average
            concerns.append({
                'category': 'Overall Spending',
                'issue': 'Higher total spending per resident',
                'eastchester': f"${eastchester_total:.2f}/resident",
                'comparison_avg': f"${avg_total:.2f}/resident",
                'difference': f"${eastchester_total - avg_total:.2f} more per resident",
                'percentage': f"{((eastchester_total / avg_total) - 1) * 100:.1f}% above average",
                'impact': 'Residents pay more in taxes but may not receive proportionally better services',
                'severity': 'high' if eastchester_total > avg_total * 1.2 else 'medium'
            })
        elif eastchester_total < avg_total * 0.9:  # 10% below average
            concerns.append({
                'category': 'Overall Spending',
                'issue': 'Lower total spending per resident',
                'eastchester': f"${eastchester_total:.2f}/resident",
                'comparison_avg': f"${avg_total:.2f}/resident",
                'difference': f"${avg_total - eastchester_total:.2f} less per resident",
                'percentage': f"{((avg_total / eastchester_total) - 1) * 100:.1f}% below average",
                'impact': 'May indicate underfunding of services or efficiency, but could also mean lower service levels',
                'severity': 'medium'
            })
        
        # 4. Debt service
        eastchester_debt_pct = (self.eastchester.debt_service / self.eastchester.total_budget) * 100
        avg_debt_pct = sum((t.debt_service / t.total_budget) * 100 for t in comp_towns) / len(comp_towns)
        if eastchester_debt_pct > avg_debt_pct * 1.15:
            concerns.append({
                'category': 'Debt Service',
                'issue': 'High debt service burden',
                'eastchester': f"{eastchester_debt_pct:.1f}% of budget",
                'comparison_avg': f"{avg_debt_pct:.1f}% of budget",
                'difference': f"{eastchester_debt_pct - avg_debt_pct:.1f} percentage points higher",
                'percentage': f"{((eastchester_debt_pct / avg_debt_pct) - 1) * 100:.1f}% above average",
                'impact': 'More tax dollars going to debt payments means less available for current services',
                'severity': 'high' if eastchester_debt_pct > avg_debt_pct * 1.25 else 'medium'
            })
        
        # 5. Administration efficiency
        eastchester_admin = self.eastchester.per_resident_admin
        avg_admin = sum(t.per_resident_admin for t in comp_towns) / len(comp_towns)
        if eastchester_admin > avg_admin * 1.2:
            concerns.append({
                'category': 'Administration',
                'issue': 'High administrative costs per resident',
                'eastchester': f"${eastchester_admin:.2f}/resident",
                'comparison_avg': f"${avg_admin:.2f}/resident",
                'difference': f"${eastchester_admin - avg_admin:.2f} more per resident",
                'percentage': f"{((eastchester_admin / avg_admin) - 1) * 100:.1f}% above average",
                'impact': 'Higher overhead costs may indicate inefficiency or bloated bureaucracy',
                'severity': 'high' if eastchester_admin > avg_admin * 1.3 else 'medium'
            })
        
        # 6. Public Safety (if significantly different)
        eastchester_safety = self.eastchester.per_resident_public_safety
        avg_safety = sum(t.per_resident_public_safety for t in comp_towns) / len(comp_towns)
        if eastchester_safety < avg_safety * 0.85:
            concerns.append({
                'category': 'Public Safety',
                'issue': 'Lower public safety spending',
                'eastchester': f"${eastchester_safety:.2f}/resident",
                'comparison_avg': f"${avg_safety:.2f}/resident",
                'difference': f"${avg_safety - eastchester_safety:.2f} less per resident",
                'percentage': f"{((avg_safety / eastchester_safety) - 1) * 100:.1f}% below average",
                'impact': 'May have fewer police officers, slower response times, or less safety infrastructure',
                'severity': 'high'
            })
        
        # Sort by severity (high first) then by difference amount
        severity_order = {'high': 3, 'medium': 2, 'low': 1}
        concerns.sort(key=lambda x: (severity_order.get(x.get('severity', 'low'), 0), 
                                     abs(float(x.get('difference', '0').replace('$', '').split()[0]))), 
                            reverse=True)
        
        return concerns[:5]  # Return top 5
    
    def summary(self) -> str:
        """Generate summary report."""
        concerns = self.find_concerns()
        
        lines = [
            "=" * 70,
            "TOWN BUDGET COMPARISON: EASTCHESTER vs COMPARABLE TOWNS",
            "=" * 70,
            "",
            "COMPARISON TOWNS: Scarsdale, Pelham, Larchmont",
            "",
            "EASTCHESTER BUDGET:",
            f"  Total: ${self.eastchester.total_budget:,.0f}",
            f"  Population: {self.eastchester.population:,}",
            f"  Per Resident: ${self.eastchester.per_resident_cost:,.2f}",
            "",
            "KEY CONCERNS FOR EASTCHESTER RESIDENTS:",
            "",
        ]
        
        for i, concern in enumerate(concerns, 1):
            lines.append(f"{i}. {concern['category']}: {concern['issue']}")
            lines.append(f"   Eastchester: {concern['eastchester']}")
            lines.append(f"   Comparison Avg: {concern['comparison_avg']}")
            lines.append(f"   Difference: {concern['difference']} ({concern['percentage']})")
            lines.append(f"   Impact: {concern['impact']}")
            lines.append(f"   Severity: {concern['severity'].upper()}")
            lines.append("")
        
        lines.append("=" * 70)
        
        return "\n".join(lines)


def load_town_budgets() -> dict[str, TownBudget]:
    """Load town budgets from file or collect new."""
    from config import DATA_DIR
    
    budget_file = DATA_DIR / 'raw' / 'town_budgets' / 'town_budgets.json'
    
    if budget_file.exists():
        with open(budget_file, 'r') as f:
            data = json.load(f)
        
        budgets = {}
        for key, budget_data in data.items():
            budgets[key] = TownBudget(**budget_data)
        
        return budgets
    else:
        return collect_town_budgets()


def compare_town_budgets() -> BudgetComparison:
    """Compare Eastchester against other towns."""
    budgets = load_town_budgets()
    
    if 'eastchester' not in budgets:
        raise ValueError("Missing Eastchester budget data")
    
    comparison_towns = {
        k: v for k, v in budgets.items() 
        if k in ['scarsdale', 'pelham', 'larchmont']
    }
    
    if not comparison_towns:
        raise ValueError("Missing comparison town budgets")
    
    return BudgetComparison(
        eastchester=budgets['eastchester'],
        comparison_towns=comparison_towns
    )


if __name__ == "__main__":
    comparison = compare_town_budgets()
    print(comparison.summary())
