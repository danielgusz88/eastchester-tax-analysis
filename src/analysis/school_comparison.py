"""
School District Budget Comparison Analysis.

Compares combined Eastchester-area school districts (Eastchester, Bronxville, Tuckahoe)
vs Scarsdale school district on a per-student basis.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import sys

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_collection.school_budget_scraper import SchoolDistrictBudget, collect_school_budgets


@dataclass
class CombinedSchoolDistrict:
    """Combined school district data."""
    name: str
    districts: list[SchoolDistrictBudget]
    
    @property
    def total_budget(self) -> float:
        return sum(d.total_budget for d in self.districts)
    
    @property
    def total_enrollment(self) -> int:
        return sum(d.enrollment for d in self.districts)
    
    @property
    def per_student_cost(self) -> float:
        if self.total_enrollment == 0:
            return 0
        return self.total_budget / self.total_enrollment
    
    @property
    def average_per_student(self) -> float:
        """Average per-student cost across districts (weighted by enrollment)."""
        if self.total_enrollment == 0:
            return 0
        total_cost = sum(d.per_student_cost * d.enrollment for d in self.districts)
        return total_cost / self.total_enrollment
    
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'total_budget': self.total_budget,
            'total_enrollment': self.total_enrollment,
            'per_student_cost': self.per_student_cost,
            'average_per_student': self.average_per_student,
            'num_districts': len(self.districts),
            'districts': [d.to_dict() for d in self.districts],
        }


@dataclass
class SchoolComparison:
    """Comparison of school district budgets."""
    eastchester_area: CombinedSchoolDistrict
    scarsdale: SchoolDistrictBudget
    
    @property
    def per_student_difference(self) -> float:
        """Difference in per-student cost."""
        return self.scarsdale.per_student_cost - self.eastchester_area.per_student_cost
    
    @property
    def per_student_difference_pct(self) -> float:
        """Percentage difference."""
        if self.eastchester_area.per_student_cost == 0:
            return 0
        return ((self.scarsdale.per_student_cost / self.eastchester_area.per_student_cost) - 1) * 100
    
    @property
    def total_budget_difference(self) -> float:
        """Difference in total budgets."""
        return self.scarsdale.total_budget - self.eastchester_area.total_budget
    
    @property
    def enrollment_difference(self) -> int:
        """Difference in enrollment."""
        return self.scarsdale.enrollment - self.eastchester_area.total_enrollment
    
    def to_dict(self) -> dict:
        return {
            'eastchester_area': self.eastchester_area.to_dict(),
            'scarsdale': self.scarsdale.to_dict(),
            'per_student_difference': self.per_student_difference,
            'per_student_difference_pct': self.per_student_difference_pct,
            'total_budget_difference': self.total_budget_difference,
            'enrollment_difference': self.enrollment_difference,
        }
    
    def summary(self) -> str:
        """Generate text summary."""
        lines = [
            "=" * 70,
            "SCHOOL DISTRICT BUDGET COMPARISON",
            "=" * 70,
            "",
            "EASTCHESTER AREA (COMBINED):",
            f"  Districts: {', '.join(d.district_name for d in self.eastchester_area.districts)}",
            f"  Total Budget: ${self.eastchester_area.total_budget:,.0f}",
            f"  Total Enrollment: {self.eastchester_area.total_enrollment:,}",
            f"  Per Student Cost: ${self.eastchester_area.per_student_cost:,.2f}",
            "",
            "  Individual Districts:",
        ]
        
        for district in self.eastchester_area.districts:
            lines.append(f"    {district.district_name}:")
            lines.append(f"      Budget: ${district.total_budget:,.0f}")
            lines.append(f"      Enrollment: {district.enrollment:,}")
            lines.append(f"      Per Student: ${district.per_student_cost:,.2f}")
        
        lines.extend([
            "",
            "SCARSDALE UFSD:",
            f"  Total Budget: ${self.scarsdale.total_budget:,.0f}",
            f"  Enrollment: {self.scarsdale.enrollment:,}",
            f"  Per Student Cost: ${self.scarsdale.per_student_cost:,.2f}",
            "",
            "COMPARISON:",
            f"  Per Student Difference: ${self.per_student_difference:,.2f}",
            f"  Percentage Difference: {self.per_student_difference_pct:+.1f}%",
            f"  Total Budget Difference: ${self.total_budget_difference:,.0f}",
            f"  Enrollment Difference: {self.enrollment_difference:,} students",
            "",
        ])
        
        if self.per_student_difference > 0:
            lines.append(f"  💡 Scarsdale spends ${self.per_student_difference:.2f} more per student")
        else:
            lines.append(f"  💡 Eastchester area spends ${abs(self.per_student_difference):.2f} more per student")
        
        lines.append("")
        lines.append("=" * 70)
        
        return "\n".join(lines)


def load_school_budgets() -> dict[str, SchoolDistrictBudget]:
    """Load school budgets from file or collect new."""
    from config import DATA_DIR
    
    budget_file = DATA_DIR / 'raw' / 'school_budgets' / 'school_budgets.json'
    
    if budget_file.exists():
        with open(budget_file, 'r') as f:
            data = json.load(f)
        
        budgets = {}
        for key, budget_data in data.items():
            budgets[key] = SchoolDistrictBudget(**budget_data)
        
        return budgets
    else:
        # Collect new data
        return collect_school_budgets()


def compare_school_districts() -> SchoolComparison:
    """Compare combined Eastchester-area districts vs Scarsdale."""
    budgets = load_school_budgets()
    
    required = ['eastchester', 'bronxville', 'tuckahoe', 'scarsdale']
    missing = [r for r in required if r not in budgets]
    
    if missing:
        raise ValueError(f"Missing school budget data: {missing}. Run collect_school_budgets() first.")
    
    # Create combined Eastchester area
    eastchester_area = CombinedSchoolDistrict(
        name='Eastchester Area (Combined)',
        districts=[
            budgets['eastchester'],
            budgets['bronxville'],
            budgets['tuckahoe'],
        ]
    )
    
    return SchoolComparison(
        eastchester_area=eastchester_area,
        scarsdale=budgets['scarsdale']
    )


if __name__ == "__main__":
    comparison = compare_school_districts()
    print(comparison.summary())
