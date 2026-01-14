"""
Town Budget Comparison Analysis.

Compares Eastchester town budget against Scarsdale, Pelham, and Larchmont
to identify areas where Eastchester may underperform or overspend.
"""

from dataclasses import dataclass
from pathlib import Path
import json
import sys
from typing import List, Dict

import pandas as pd

sys.path.insert(0, str(Path(__file__).parent.parent))

from data_collection.town_budget_scraper import TownBudget, collect_town_budgets
from models.tax_calculator import TaxCalculator


@dataclass
class TaxBurdenAnalysis:
    """Tax burden analysis for a municipality."""
    municipality: str
    typical_home_value: float
    typical_sqft: float
    annual_tax: float
    tax_per_sqft: float
    tax_per_taxpayer: float
    effective_rate: float
    municipal_tax_only: float  # Town + Village (excluding school)
    municipal_tax_per_sqft: float
    municipal_tax_per_taxpayer: float
    
    def to_dict(self) -> dict:
        return {
            'municipality': self.municipality,
            'typical_home_value': self.typical_home_value,
            'typical_sqft': self.typical_sqft,
            'annual_tax': self.annual_tax,
            'tax_per_sqft': self.tax_per_sqft,
            'tax_per_taxpayer': self.tax_per_taxpayer,
            'effective_rate': self.effective_rate,
            'municipal_tax_only': self.municipal_tax_only,
            'municipal_tax_per_sqft': self.municipal_tax_per_sqft,
            'municipal_tax_per_taxpayer': self.municipal_tax_per_taxpayer,
        }


@dataclass
class CombinedEastchesterArea:
    """Combined tax and service analysis for Eastchester area."""
    municipalities: List[str]  # ['eastchester_unincorp', 'bronxville', 'tuckahoe']
    tax_burdens: Dict[str, TaxBurdenAnalysis]
    total_population: int
    estimated_taxpayers: int  # Estimated number of property taxpayers
    
    @property
    def weighted_avg_tax_per_sqft(self) -> float:
        """Weighted average tax per sqft across the 3 municipalities."""
        # Use population as weight
        total = 0
        weight = 0
        for muni_key, burden in self.tax_burdens.items():
            # Estimate population for each (rough)
            pop_weights = {
                'eastchester_unincorp': 20000,
                'bronxville': 6500,
                'tuckahoe': 6500,
            }
            w = pop_weights.get(muni_key, 10000)
            total += burden.tax_per_sqft * w
            weight += w
        return total / weight if weight > 0 else 0
    
    @property
    def weighted_avg_tax_per_taxpayer(self) -> float:
        """Weighted average tax per taxpayer."""
        total = 0
        weight = 0
        for muni_key, burden in self.tax_burdens.items():
            pop_weights = {
                'eastchester_unincorp': 20000,
                'bronxville': 6500,
                'tuckahoe': 6500,
            }
            w = pop_weights.get(muni_key, 10000)
            total += burden.tax_per_taxpayer * w
            weight += w
        return total / weight if weight > 0 else 0
    
    @property
    def weighted_avg_municipal_tax_per_sqft(self) -> float:
        """Weighted average municipal tax (town+village, no school) per sqft."""
        total = 0
        weight = 0
        for muni_key, burden in self.tax_burdens.items():
            pop_weights = {
                'eastchester_unincorp': 20000,
                'bronxville': 6500,
                'tuckahoe': 6500,
            }
            w = pop_weights.get(muni_key, 10000)
            total += burden.municipal_tax_per_sqft * w
            weight += w
        return total / weight if weight > 0 else 0
    
    @property
    def weighted_avg_municipal_tax_per_taxpayer(self) -> float:
        """Weighted average municipal tax (town+village, no school) per taxpayer."""
        total = 0
        weight = 0
        for muni_key, burden in self.tax_burdens.items():
            pop_weights = {
                'eastchester_unincorp': 20000,
                'bronxville': 6500,
                'tuckahoe': 6500,
            }
            w = pop_weights.get(muni_key, 10000)
            total += burden.municipal_tax_per_taxpayer * w
            weight += w
        return total / weight if weight > 0 else 0


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
    
    def calculate_tax_burdens(self, typical_home_value: float = 1_000_000, typical_sqft: float = 2000) -> Dict[str, TaxBurdenAnalysis]:
        """
        Calculate tax burdens for all municipalities.
        
        Args:
            typical_home_value: Typical home value for comparison
            typical_sqft: Typical square footage
            
        Returns:
            Dict of municipality -> TaxBurdenAnalysis
        """
        calc = TaxCalculator()
        burdens = {}
        
        # Calculate for Eastchester area municipalities
        eastchester_area_munis = ['eastchester_unincorp', 'bronxville', 'tuckahoe']
        
        for muni_key in eastchester_area_munis:
            try:
                breakdown = calc.calculate_from_market_value(typical_home_value, muni_key)
                
                # Estimate taxpayers (roughly 2.5 people per household, 70% own homes)
                muni = calc.get_municipality(muni_key)
                population = {
                    'eastchester_unincorp': 20000,
                    'bronxville': 6500,
                    'tuckahoe': 6500,
                }.get(muni_key, 10000)
                
                estimated_taxpayers = int(population * 0.7 / 2.5)  # Rough estimate
                
                # Municipal tax = town + village (exclude school, county, fire)
                municipal_tax = breakdown.town_tax + breakdown.village_tax
                
                burdens[muni_key] = TaxBurdenAnalysis(
                    municipality=muni.name,
                    typical_home_value=typical_home_value,
                    typical_sqft=typical_sqft,
                    annual_tax=breakdown.total,
                    tax_per_sqft=breakdown.total / typical_sqft,
                    tax_per_taxpayer=breakdown.total,  # Per property owner
                    effective_rate=breakdown.effective_rate,
                    municipal_tax_only=municipal_tax,
                    municipal_tax_per_sqft=municipal_tax / typical_sqft,
                    municipal_tax_per_taxpayer=municipal_tax,
                )
            except Exception:
                continue
        
        # Calculate for comparison towns
        comparison_keys = {
            'scarsdale': 'scarsdale',
            'pelham': 'pelham',
            'larchmont': 'larchmont',
        }
        
        for town_name, muni_key in comparison_keys.items():
            try:
                breakdown = calc.calculate_from_market_value(typical_home_value, muni_key)
                
                town = self.comparison_towns.get(town_name)
                if not town:
                    continue
                
                population = town.population
                estimated_taxpayers = int(population * 0.7 / 2.5)
                
                municipal_tax = breakdown.town_tax + breakdown.village_tax
                
                burdens[muni_key] = TaxBurdenAnalysis(
                    municipality=town.municipality,
                    typical_home_value=typical_home_value,
                    typical_sqft=typical_sqft,
                    annual_tax=breakdown.total,
                    tax_per_sqft=breakdown.total / typical_sqft,
                    tax_per_taxpayer=breakdown.total,
                    effective_rate=breakdown.effective_rate,
                    municipal_tax_only=municipal_tax,
                    municipal_tax_per_sqft=municipal_tax / typical_sqft,
                    municipal_tax_per_taxpayer=municipal_tax,
                )
            except Exception:
                continue
        
        return burdens
    
    def get_combined_eastchester_tax_analysis(self, typical_home_value: float = 1_000_000, typical_sqft: float = 2000) -> CombinedEastchesterArea:
        """Get combined tax analysis for Eastchester area."""
        burdens = self.calculate_tax_burdens(typical_home_value, typical_sqft)
        
        # Filter to Eastchester area
        eastchester_burdens = {
            k: v for k, v in burdens.items()
            if k in ['eastchester_unincorp', 'bronxville', 'tuckahoe']
        }
        
        total_pop = 33000  # Combined population
        
        return CombinedEastchesterArea(
            municipalities=['eastchester_unincorp', 'bronxville', 'tuckahoe'],
            tax_burdens=eastchester_burdens,
            total_population=total_pop,
            estimated_taxpayers=int(total_pop * 0.7 / 2.5),
        )
    
    def analyze_municipal_tax_efficiency(self, typical_home_value: float = 1_000_000, typical_sqft: float = 2000) -> Dict:
        """
        Analyze municipal tax efficiency: services received per dollar of municipal tax.
        
        Returns comprehensive analysis comparing municipal tax rates vs service levels.
        """
        burdens = self.calculate_tax_burdens(typical_home_value, typical_sqft)
        combined_eastchester = self.get_combined_eastchester_tax_analysis(typical_home_value, typical_sqft)
        
        # Calculate municipal tax per resident for Eastchester area
        # We need to estimate municipal tax per resident (not per taxpayer)
        # Rough estimate: municipal_tax_per_taxpayer * (taxpayers / population)
        eastchester_taxpayers = combined_eastchester.estimated_taxpayers
        eastchester_pop = combined_eastchester.total_population
        
        # Get weighted average municipal tax per taxpayer
        weighted_municipal_tax_per_taxpayer = combined_eastchester.weighted_avg_municipal_tax_per_taxpayer
        
        # Convert to per resident: multiply by (taxpayers / population)
        municipal_tax_per_resident = (weighted_municipal_tax_per_taxpayer * 
                                      (eastchester_taxpayers / eastchester_pop) 
                                      if eastchester_pop > 0 and eastchester_taxpayers > 0 else 0)
        
        # Calculate municipal tax as % of total tax for Eastchester area
        # Get average total tax per taxpayer first
        weighted_total_tax_per_taxpayer = combined_eastchester.weighted_avg_tax_per_taxpayer
        municipal_tax_rate = 0.0
        if weighted_total_tax_per_taxpayer > 0:
            municipal_tax_rate = (weighted_municipal_tax_per_taxpayer / weighted_total_tax_per_taxpayer) * 100
        
        analysis = {
            'eastchester_area': {
                'municipal_tax_per_sqft': combined_eastchester.weighted_avg_municipal_tax_per_sqft,
                'municipal_tax_per_taxpayer': weighted_municipal_tax_per_taxpayer,
                'municipal_tax_per_resident': municipal_tax_per_resident,
                'services_per_resident': self.eastchester.per_resident_cost,
                'municipal_tax_efficiency': 0.0,  # Services per dollar of municipal tax
                'municipal_tax_rate': municipal_tax_rate,  # Municipal tax as % of total tax
            },
            'comparison_towns': {},
        }
        
        # Calculate efficiency for Eastchester area
        # Efficiency = services per resident / municipal tax per resident
        
        if municipal_tax_per_resident > 0:
            analysis['eastchester_area']['municipal_tax_efficiency'] = (
                self.eastchester.per_resident_cost / municipal_tax_per_resident
            )
        
        # Calculate for comparison towns
        for town_name, town_budget in self.comparison_towns.items():
            burden = burdens.get(town_name)
            if not burden:
                continue
            
            # Estimate taxpayers and municipal tax per resident
            town_taxpayers = int(town_budget.population * 0.7 / 2.5)
            municipal_tax_per_resident_town = (burden.municipal_tax_per_taxpayer * 
                                                (town_taxpayers / town_budget.population) 
                                                if town_budget.population > 0 else 0)
            
            efficiency = 0.0
            if municipal_tax_per_resident_town > 0:
                efficiency = town_budget.per_resident_cost / municipal_tax_per_resident_town
            
            # Calculate municipal tax as % of total tax
            municipal_tax_pct = 0.0
            if burden.annual_tax > 0:
                municipal_tax_pct = (burden.municipal_tax_only / burden.annual_tax) * 100
            
            analysis['comparison_towns'][town_name] = {
                'municipality': town_budget.municipality,
                'municipal_tax_per_sqft': burden.municipal_tax_per_sqft,
                'municipal_tax_per_taxpayer': burden.municipal_tax_per_taxpayer,
                'municipal_tax_per_resident': municipal_tax_per_resident_town,
                'services_per_resident': town_budget.per_resident_cost,
                'municipal_tax_efficiency': efficiency,
                'municipal_tax_rate': municipal_tax_pct,
                'total_tax_per_sqft': burden.tax_per_sqft,
                'total_tax_per_taxpayer': burden.tax_per_taxpayer,
            }
        
        # Calculate averages for comparison
        if analysis['comparison_towns']:
            comp_towns = list(analysis['comparison_towns'].values())
            analysis['comparison_averages'] = {
                'municipal_tax_per_sqft': sum(t['municipal_tax_per_sqft'] for t in comp_towns) / len(comp_towns),
                'municipal_tax_per_resident': sum(t['municipal_tax_per_resident'] for t in comp_towns) / len(comp_towns),
                'services_per_resident': sum(t['services_per_resident'] for t in comp_towns) / len(comp_towns),
                'municipal_tax_efficiency': sum(t['municipal_tax_efficiency'] for t in comp_towns) / len(comp_towns),
            }
        
        return analysis
    
    def find_municipal_tax_concerns(self, typical_home_value: float = 1_000_000, typical_sqft: float = 2000) -> List[dict]:
        """
        Find concerns about municipal tax rates vs services provided.
        
        Identifies if Eastchester charges similar municipal taxes but provides fewer services.
        """
        analysis = self.analyze_municipal_tax_efficiency(typical_home_value, typical_sqft)
        concerns = []
        
        eastchester = analysis['eastchester_area']
        comp_avg = analysis.get('comparison_averages', {})
        
        if not comp_avg:
            return concerns
        
        # Concern 1: Municipal tax per sqft vs services
        if eastchester['municipal_tax_per_sqft'] > comp_avg['municipal_tax_per_sqft'] * 0.9:  # Within 10%
            if eastchester['services_per_resident'] < comp_avg['services_per_resident'] * 0.8:  # 20% less services
                concerns.append({
                    'category': 'Municipal Tax Value',
                    'issue': 'Paying similar municipal tax but receiving fewer services',
                    'eastchester_municipal_tax_per_sqft': f"${eastchester['municipal_tax_per_sqft']:.2f}",
                    'comparison_avg_municipal_tax_per_sqft': f"${comp_avg['municipal_tax_per_sqft']:.2f}",
                    'eastchester_services': f"${eastchester['services_per_resident']:.2f}/resident",
                    'comparison_avg_services': f"${comp_avg['services_per_resident']:.2f}/resident",
                    'efficiency_difference': f"{((comp_avg['municipal_tax_efficiency'] / eastchester['municipal_tax_efficiency']) - 1) * 100:.1f}%",
                    'impact': 'Residents pay comparable municipal taxes but receive significantly fewer services per tax dollar',
                    'severity': 'high'
                })
        
        # Concern 2: Low efficiency ratio
        if eastchester['municipal_tax_efficiency'] < comp_avg['municipal_tax_efficiency'] * 0.85:
            concerns.append({
                'category': 'Tax Efficiency',
                'issue': 'Lower municipal tax efficiency (services per tax dollar)',
                'eastchester_efficiency': f"{eastchester['municipal_tax_efficiency']:.2f}x",
                'comparison_avg_efficiency': f"{comp_avg['municipal_tax_efficiency']:.2f}x",
                'difference': f"{comp_avg['municipal_tax_efficiency'] - eastchester['municipal_tax_efficiency']:.2f}x less efficient",
                'percentage': f"{((comp_avg['municipal_tax_efficiency'] / eastchester['municipal_tax_efficiency']) - 1) * 100:.1f}% below average",
                'impact': 'Each dollar of municipal tax provides fewer services compared to other towns',
                'severity': 'high'
            })
        
        # Concern 3: High municipal tax rate but low services
        if eastchester['municipal_tax_per_sqft'] > comp_avg['municipal_tax_per_sqft'] * 1.1:
            if eastchester['services_per_resident'] < comp_avg['services_per_resident']:
                concerns.append({
                    'category': 'Tax Rate vs Services',
                    'issue': 'Higher municipal tax rate but lower service levels',
                    'eastchester_municipal_tax': f"${eastchester['municipal_tax_per_sqft']:.2f}/sqft",
                    'comparison_avg_municipal_tax': f"${comp_avg['municipal_tax_per_sqft']:.2f}/sqft",
                    'tax_difference': f"${eastchester['municipal_tax_per_sqft'] - comp_avg['municipal_tax_per_sqft']:.2f} more per sqft",
                    'services_difference': f"${comp_avg['services_per_resident'] - eastchester['services_per_resident']:.2f} less services per resident",
                    'impact': 'Residents pay more in municipal taxes but receive less in services',
                    'severity': 'high'
                })
        
        return concerns
    
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
