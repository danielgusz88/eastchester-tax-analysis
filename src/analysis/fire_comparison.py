"""
Fire Department Budget Comparison Analysis.

Compares fire department budgets and per-resident costs
across municipalities.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_collection.fire_budget_scraper import FireDepartmentBudget, collect_fire_budgets


@dataclass
class FireComparison:
    """Comparison of fire department budgets."""
    eastchester_budget: FireDepartmentBudget
    scarsdale_budget: FireDepartmentBudget
    
    @property
    def per_resident_difference(self) -> float:
        """Difference in per-resident cost."""
        return self.scarsdale_budget.per_resident_cost - self.eastchester_budget.per_resident_cost
    
    @property
    def per_resident_difference_pct(self) -> float:
        """Percentage difference."""
        if self.eastchester_budget.per_resident_cost == 0:
            return 0
        return ((self.scarsdale_budget.per_resident_cost / self.eastchester_budget.per_resident_cost) - 1) * 100
    
    @property
    def total_budget_difference(self) -> float:
        """Difference in total budgets."""
        return self.scarsdale_budget.total_budget - self.eastchester_budget.total_budget
    
    def to_dict(self) -> dict:
        return {
            'eastchester': self.eastchester_budget.to_dict(),
            'scarsdale': self.scarsdale_budget.to_dict(),
            'per_resident_difference': self.per_resident_difference,
            'per_resident_difference_pct': self.per_resident_difference_pct,
            'total_budget_difference': self.total_budget_difference,
        }
    
    def summary(self) -> str:
        """Generate text summary."""
        lines = [
            "=" * 70,
            "FIRE DEPARTMENT BUDGET COMPARISON",
            "=" * 70,
            "",
            "EASTCHESTER FIRE DEPARTMENT:",
            f"  Total Budget: ${self.eastchester_budget.total_budget:,.0f}",
            f"  Population Covered: {self.eastchester_budget.population:,}",
            f"  Per Resident Cost: ${self.eastchester_budget.per_resident_cost:,.2f}",
            f"  Coverage Area: {self.eastchester_budget.coverage_area}",
            "",
            "SCARSDALE FIRE DEPARTMENT:",
            f"  Total Budget: ${self.scarsdale_budget.total_budget:,.0f}",
            f"  Population Covered: {self.scarsdale_budget.population:,}",
            f"  Per Resident Cost: ${self.scarsdale_budget.per_resident_cost:,.2f}",
            f"  Coverage Area: {self.scarsdale_budget.coverage_area}",
            "",
            "COMPARISON:",
            f"  Per Resident Difference: ${self.per_resident_difference:,.2f}",
            f"  Percentage Difference: {self.per_resident_difference_pct:+.1f}%",
            f"  Total Budget Difference: ${self.total_budget_difference:,.0f}",
            "",
        ]
        
        if self.per_resident_difference > 0:
            lines.append(f"  💡 Scarsdale spends ${self.per_resident_difference:.2f} more per resident")
        else:
            lines.append(f"  💡 Eastchester spends ${abs(self.per_resident_difference):.2f} more per resident")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


def load_fire_budgets() -> dict[str, FireDepartmentBudget]:
    """Load fire budgets from file or collect new."""
    from config import DATA_DIR
    
    budget_file = DATA_DIR / 'raw' / 'fire_budgets' / 'fire_budgets.json'
    
    if budget_file.exists():
        with open(budget_file, 'r') as f:
            data = json.load(f)
        
        budgets = {}
        for key, budget_data in data.items():
            budgets[key] = FireDepartmentBudget(**budget_data)
        
        return budgets
    else:
        # Collect new data
        return collect_fire_budgets()


def compare_fire_departments() -> FireComparison:
    """Compare Eastchester and Scarsdale fire departments."""
    budgets = load_fire_budgets()
    
    if 'eastchester' not in budgets or 'scarsdale' not in budgets:
        raise ValueError("Missing fire budget data. Run collect_fire_budgets() first.")
    
    return FireComparison(
        eastchester_budget=budgets['eastchester'],
        scarsdale_budget=budgets['scarsdale']
    )


if __name__ == "__main__":
    comparison = compare_fire_departments()
    print(comparison.summary())
