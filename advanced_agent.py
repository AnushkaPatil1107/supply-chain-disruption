import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import random
import math
import re
from simulation import EQUIPMENT_CATEGORIES

class SupplyChainAgent:
    """
    An advanced agent for supply chain optimization and disruption management
    that operates entirely within the application (no external API calls).
    """
    
    def __init__(self):
        # Predetermined knowledge base for disruption types and solutions
        self.disruption_types = [
            "Supply chain delay", 
            "Quality issues", 
            "Production shortage", 
            "Logistics failure",
            "Supplier bankruptcy",
            "Regional blackout",
            "Labor shortage",
            "Equipment failure", 
            "Natural disaster",
            "Political unrest"
        ]
        
        self.solution_templates = {
            "inventory": "Increase safety stock by {0}% for {1}",
            "supplier": "Find alternative supplier for {0}",
            "logistics": "Establish backup logistics routes for {0}",
            "manufacturing": "Implement flexible manufacturing process for {0}",
            "monitoring": "Enhance monitoring systems for {0} supply",
            "diversification": "Diversify {0} suppliers across different regions",
            "collaboration": "Develop collaborative planning with {0} suppliers"
        }
        
        # Historical disruption data (synthetic for analysis)
        # These are illustrative priors, not measured incident history. Keep
        # the category set aligned with the equipment dataset used by the app.
        self.historical_disruptions = {
            category: {
                "count": 6 + len(details["suppliers"]),
                "avg_impact": round(min(0.42, 0.18 + len(details["suppliers"]) * 0.015), 2),
                "trend": "increasing" if len(details["suppliers"]) >= 7 else "stable"
            }
            for category, details in EQUIPMENT_CATEGORIES.items()
        }
    
    def analyze_disruptions(self, simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze supply chain disruptions and generate insights
        
        Args:
            simulation_data: Dictionary containing simulation results
            
        Returns:
            Dictionary with analysis results and recommendations
        """
        # Extract data from simulation results
        disruptions = simulation_data.get("disruptions", {})
        normal_results = simulation_data.get("normal_results", {})
        disrupted_results = simulation_data.get("disrupted_results", {})
        solution_results = simulation_data.get("solution_results", {})
        suppliers = simulation_data.get("suppliers", [])
        
        # Calculate disruption rate
        total_suppliers = len(suppliers) if suppliers else 0
        disrupted_suppliers = len(disruptions)
        disruption_rate = disrupted_suppliers / total_suppliers if total_suppliers > 0 else 0
        
        # Get severity level
        severity_level = self._calculate_severity_level(disruption_rate)
        
        # Identify most common disruption
        most_common_disruption = self._get_most_common_disruption()
        
        # Identify highest risk categories
        highest_risk_categories = self._get_highest_risk_categories()
        
        # Analyze impact by category
        category_impacts = self._analyze_category_impacts(normal_results, disrupted_results)
        
        # Identify bottlenecks
        bottlenecks = self._identify_bottlenecks(simulation_data)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(
            disruptions=disruptions,
            category_impacts=category_impacts,
            bottlenecks=bottlenecks
        )
        
        # Generate recovery forecast
        recovery_forecast = self._generate_recovery_forecast(disruptions)
        
        # Format disruption summary
        disruption_summary = {
            "total_suppliers": total_suppliers,
            "disrupted_suppliers": disrupted_suppliers,
            "disruption_rate": f"{disruption_rate:.0%}",
            "severity_level": severity_level,
            "most_common_disruption": most_common_disruption,
            "highest_risk_categories": highest_risk_categories
        }
        
        # Return the complete analysis
        return {
            "disruption_summary": disruption_summary,
            "category_impacts": category_impacts,
            "bottlenecks": bottlenecks,
            "recommendations": recommendations,
            "recovery_forecast": recovery_forecast
        }
    
    def _calculate_severity_level(self, disruption_rate: float) -> str:
        """Calculate the severity level based on disruption rate"""
        if disruption_rate < 0.1:
            return "Low"
        elif disruption_rate < 0.3:
            return "Medium"
        elif disruption_rate < 0.5:
            return "High"
        else:
            return "Critical"
    
    def _get_most_common_disruption(self) -> str:
        """Identify the most common disruption type from history"""
        # For demonstration, select from predefined list
        # In a real system, this would analyze historical data
        disruption_weights = {
            "Supply chain delay": 35,
            "Quality issues": 20, 
            "Production shortage": 15,
            "Logistics failure": 10,
            "Natural disaster": 5,
            "Equipment failure": 5,
            "Labor shortage": 5,
            "Regional blackout": 2,
            "Political unrest": 2,
            "Supplier bankruptcy": 1
        }
        
        # Weighted random selection
        items = list(disruption_weights.keys())
        weights = list(disruption_weights.values())
        return random.choices(items, weights=weights, k=1)[0]
    
    def _get_highest_risk_categories(self, limit: int = 3) -> List[str]:
        """Identify the highest risk categories"""
        # Sort categories by historical disruption impact and count
        sorted_categories = sorted(
            self.historical_disruptions.items(),
            key=lambda x: (x[1]["avg_impact"] * x[1]["count"]),
            reverse=True
        )
        
        # Return top n categories
        return [category for category, _ in sorted_categories[:limit]]
    
    def _analyze_category_impacts(self, normal_results: Dict, disrupted_results: Dict) -> List[Dict]:
        """Analyze impact by equipment category"""
        categories = list(self.historical_disruptions.keys())
        impacts = []
        
        # Get production values from normal and disrupted scenarios
        normal_production = normal_results.get("manufacturer_production", {})
        disrupted_production = disrupted_results.get("manufacturer_production", {})
        
        # Analyze each category's impact
        for category in categories:
            # Sum up production for manufacturers in this category
            normal_total = sum(value for key, value in normal_production.items() if f"({category})" in key)
            disrupted_total = sum(value for key, value in disrupted_production.items() if f"({category})" in key)
            
            # Calculate percentage reduction
            impact_percentage = 0
            if normal_total > 0:
                impact_percentage = ((normal_total - disrupted_total) / normal_total) * 100
            
            # Categorize impact severity
            severity = self._categorize_impact_severity(impact_percentage)
            
            impacts.append({
                "category": category,
                "normal_production": normal_total,
                "disrupted_production": disrupted_total,
                "impact_percentage": impact_percentage,
                "severity": severity
            })
        
        # Sort by impact percentage
        return sorted(impacts, key=lambda x: x["impact_percentage"], reverse=True)
    
    def _categorize_impact_severity(self, impact_percentage: float) -> str:
        """Categorize the severity of impact based on percentage"""
        if impact_percentage < 10:
            return "Minimal"
        elif impact_percentage < 30:
            return "Moderate"
        elif impact_percentage < 50:
            return "Significant"
        else:
            return "Severe"
    
    def _identify_bottlenecks(self, simulation_data: Dict) -> List[Dict]:
        """Identify bottlenecks in the supply chain"""
        bottlenecks = []
        
        # Extract data
        disruptions = simulation_data.get("disruptions", {})
        disrupted_results = simulation_data.get("disrupted_results", {})
        suppliers = simulation_data.get("suppliers", [])
        
        # Get disrupted suppliers by name
        disrupted_supplier_names = set(disruptions.keys())
        
        # Group suppliers by category
        suppliers_by_category = {}
        for supplier in suppliers:
            category = supplier.category
            if category not in suppliers_by_category:
                suppliers_by_category[category] = []
            suppliers_by_category[category].append(supplier.name)
        
        # Identify categories with high disruption rate
        for category, supplier_names in suppliers_by_category.items():
            if not supplier_names:
                continue
                
            # Calculate disruption rate for this category
            category_disruption_count = sum(1 for name in supplier_names if name in disrupted_supplier_names)
            category_disruption_rate = category_disruption_count / len(supplier_names)
            
            # If more than 40% of suppliers in a category are disrupted, consider it a bottleneck
            if category_disruption_rate >= 0.4:
                bottlenecks.append({
                    "category": category,
                    "disruption_rate": f"{category_disruption_rate:.0%}",
                    "disrupted_suppliers": category_disruption_count,
                    "total_suppliers": len(supplier_names),
                    "criticality": "High" if category_disruption_rate > 0.6 else "Medium"
                })
        
        return bottlenecks
    
    def _generate_recommendations(self, 
                                 disruptions: Dict, 
                                 category_impacts: List[Dict], 
                                 bottlenecks: List[Dict]) -> List[Dict]:
        """Generate strategic recommendations based on disruption analysis"""
        recommendations = []
        
        # 1. Recommendations for high-impact categories
        for impact in category_impacts:
            if impact["severity"] in ["Significant", "Severe"]:
                # Recommend inventory increase proportional to impact
                inventory_increase = min(round(impact["impact_percentage"]), 100)
                recommendations.append({
                    "type": "Inventory",
                    "action": self.solution_templates["inventory"].format(
                        inventory_increase, impact["category"]
                    ),
                    "target": impact["category"],
                    "priority": "High" if impact["severity"] == "Severe" else "Medium"
                })
                
                # Recommend supplier diversification for severe impacts
                if impact["severity"] == "Severe":
                    recommendations.append({
                        "type": "Diversification",
                        "action": self.solution_templates["diversification"].format(
                            impact["category"]
                        ),
                        "target": impact["category"],
                        "priority": "High"
                    })
        
        # 2. Recommendations for bottlenecks
        for bottleneck in bottlenecks:
            # Recommend monitoring systems for all bottlenecks
            recommendations.append({
                "type": "Monitoring",
                "action": self.solution_templates["monitoring"].format(
                    bottleneck["category"]
                ),
                "target": bottleneck["category"],
                "priority": "High" if bottleneck["criticality"] == "High" else "Medium"
            })
            
            # For high criticality bottlenecks, add manufacturing flexibility
            if bottleneck["criticality"] == "High":
                recommendations.append({
                    "type": "Manufacturing",
                    "action": self.solution_templates["manufacturing"].format(
                        bottleneck["category"]
                    ),
                    "target": bottleneck["category"],
                    "priority": "High"
                })
        
        # 3. Logistics recommendations based on disruption presence
        if disruptions:
            # If there are many disruptions, recommend logistics improvements
            if len(disruptions) >= 3:
                affected_categories = set()
                for supplier, _ in disruptions.items():
                    # Extract category from supplier name (assuming format like "SupplierName (Category)")
                    match = re.search(r'\(([^)]+)\)', supplier)
                    if match:
                        affected_categories.add(match.group(1))
                    
                # If multiple categories affected, recommend logistics improvements
                if len(affected_categories) >= 2:
                    recommendations.append({
                        "type": "Logistics",
                        "action": self.solution_templates["logistics"].format(
                            ", ".join(list(affected_categories)[:2])
                        ),
                        "target": "Multiple Categories",
                        "priority": "Medium"
                    })
        
        # 4. Collaboration recommendations for sustainability
        if category_impacts:
            # Recommend collaboration for the category with highest impact
            highest_impact = max(category_impacts, key=lambda x: x["impact_percentage"])
            recommendations.append({
                "type": "Collaboration",
                "action": self.solution_templates["collaboration"].format(
                    highest_impact["category"]
                ),
                "target": highest_impact["category"],
                "priority": "Medium"
            })
        
        # Sort recommendations by priority
        priority_order = {"High": 0, "Medium": 1, "Low": 2}
        return sorted(recommendations, key=lambda x: priority_order[x["priority"]])
    
    def _generate_recovery_forecast(self, disruptions: Dict) -> Dict:
        """Generate recovery forecast based on current disruptions"""
        if not disruptions:
            return {
                "estimated_recovery_time": "No disruptions present",
                "confidence": "High",
                "recovery_phases": []
            }
        
        # Calculate estimated recovery time based on number and type of disruptions
        disruption_count = len(disruptions)
        
        # Define recovery time ranges (in days/weeks)
        if disruption_count < 3:
            recovery_time = "1-2 weeks"
            confidence = "High"
        elif disruption_count < 6:
            recovery_time = "3-4 weeks"
            confidence = "Medium"
        else:
            recovery_time = "1-2 months"
            confidence = "Low"
        
        # Generate recovery phases
        recovery_phases = []
        
        # Phase 1: Initial response
        recovery_phases.append({
            "phase": "Initial Response",
            "timeline": "Days 1-3",
            "activities": [
                "Assess impact of disruptions",
                "Activate alternative suppliers",
                "Prioritize critical production lines",
                "Communicate with stakeholders"
            ]
        })
        
        # Phase 2: Stabilization
        recovery_phases.append({
            "phase": "Stabilization",
            "timeline": "Week 1",
            "activities": [
                "Implement temporary logistics solutions",
                "Allocate inventory to high-priority customers",
                "Begin coordination with alternative suppliers",
                "Adjust production schedules"
            ]
        })
        
        # Phase 3: Recovery
        if disruption_count < 3:
            # Simple recovery for few disruptions
            recovery_phases.append({
                "phase": "Full Recovery",
                "timeline": "Week 2",
                "activities": [
                    "Resume normal production levels",
                    "Replenish safety stock",
                    "Evaluate response effectiveness",
                    "Update contingency plans"
                ]
            })
        else:
            # Gradual recovery for many disruptions
            recovery_phases.append({
                "phase": "Partial Recovery",
                "timeline": "Weeks 2-3",
                "activities": [
                    "Scale up alternative supplier production",
                    "Restore 70-80% of normal operations",
                    "Begin inventory rebuilding",
                    "Implement monitoring improvements"
                ]
            })
            
            recovery_phases.append({
                "phase": "Full Recovery",
                "timeline": "Week 4+",
                "activities": [
                    "Return to pre-disruption production levels",
                    "Complete safety stock replenishment",
                    "Implement resilience improvements",
                    "Document lessons learned"
                ]
            })
        
        return {
            "estimated_recovery_time": recovery_time,
            "confidence": confidence,
            "recovery_phases": recovery_phases
        }
        
    def generate_insights(self, simulation_data: Dict) -> Dict:
        """
        Generate high-level insights about the supply chain simulation
        
        Args:
            simulation_data: Dictionary containing simulation results
            
        Returns:
            Dictionary with insights
        """
        # Extract disruption analysis
        disruption_analysis = self.analyze_disruptions(simulation_data)
        
        # Extract key metrics
        disruption_summary = disruption_analysis.get("disruption_summary", {})
        disruption_rate_str = disruption_summary.get("disruption_rate", "0%")
        disruption_rate = float(disruption_rate_str.strip("%"))/100 if disruption_rate_str else 0
        severity_level = disruption_summary.get("severity_level", "Low")
        
        # Generate insight summary
        insight_summary = self._generate_insight_summary(disruption_rate, severity_level)
        
        # Generate key findings
        key_findings = self._generate_key_findings(disruption_analysis)
        
        # Generate strategic insights
        strategic_insights = self._generate_strategic_insights(disruption_analysis)
        
        # Generate risk assessment
        highest_risk_categories = disruption_summary.get("highest_risk_categories", [])
        risk_assessment = self._generate_risk_assessment(highest_risk_categories)
        
        # Generate performance indicators
        performance_indicators = self._generate_performance_indicators(simulation_data)
        
        # Calculate resilience score
        resilience_score = self._calculate_resilience_score(
            performance_indicators.get("production_efficiency", 0),
            performance_indicators.get("supply_continuity", 0)
        )
        
        # Generate trend analysis
        trend_analysis = self._generate_trend_analysis()
        
        # Return compiled insights
        return {
            "headline": insight_summary,
            "key_metrics": {
                "disruption_rate": disruption_rate_str,
                "severity": severity_level,
                "critical_bottlenecks": str(len(disruption_analysis.get("bottlenecks", []))),
                "affected_categories": len(highest_risk_categories)
            },
            "top_insights": key_findings,
            "strategic_recommendations": strategic_insights,
            "risk_assessment": risk_assessment,
            "performance_indicators": performance_indicators,
            "resilience_score": resilience_score.get("score_label", "N/A"),
            "resilience_details": resilience_score,
            "trend_analysis": trend_analysis
        }
    
    def _generate_insight_summary(self, disruption_rate: float, severity_level: str) -> str:
        """Generate a summary of insights based on disruption metrics"""
        if disruption_rate == 0:
            return "Supply chain operating normally with no detected disruptions"
        elif disruption_rate < 0.1:
            return "Minor supply chain disruptions with limited impact on operations"
        elif disruption_rate < 0.3:
            return f"{severity_level} supply chain disruptions affecting {disruption_rate:.0%} of suppliers"
        elif disruption_rate < 0.5:
            return f"Significant supply chain disruptions requiring immediate attention"
        else:
            return f"Critical supply chain failure affecting over {disruption_rate:.0%} of suppliers"
    
    def _generate_key_findings(self, analysis: Dict) -> List[str]:
        """Generate key findings from the analysis"""
        findings = []
        
        # Get key data
        disruption_summary = analysis.get("disruption_summary", {})
        category_impacts = analysis.get("category_impacts", [])
        bottlenecks = analysis.get("bottlenecks", [])
        recommendations = analysis.get("recommendations", [])
        
        # Finding 1: Disruption overview
        if disruption_summary:
            findings.append(
                f"Supply chain experiencing {disruption_summary.get('severity_level', 'Unknown')} disruption "
                f"with {disruption_summary.get('disruption_rate', '0%')} of suppliers affected"
            )
        
        # Finding 2: Most impacted category
        if category_impacts:
            most_impacted = category_impacts[0]
            findings.append(
                f"{most_impacted.get('category', 'Unknown')} experiencing {most_impacted.get('severity', 'significant')} "
                f"impact with {most_impacted.get('impact_percentage', 0):.1f}% reduction in production"
            )
        
        # Finding 3: Bottlenecks
        if bottlenecks:
            critical_bottlenecks = [b for b in bottlenecks if b.get('criticality') == 'High']
            if critical_bottlenecks:
                bottleneck_categories = [b.get('category', 'Unknown') for b in critical_bottlenecks]
                findings.append(
                    f"Critical bottlenecks identified in {', '.join(bottleneck_categories)} "
                    f"supply with over 60% disruption rate"
                )
            elif bottlenecks:
                bottleneck_count = len(bottlenecks)
                findings.append(
                    f"Detected {bottleneck_count} bottleneck{'s' if bottleneck_count > 1 else ''} "
                    f"in the supply chain with moderate severity"
                )
        
        # Finding 4: Most common disruption
        if disruption_summary.get('most_common_disruption'):
            findings.append(
                f"Most frequent disruption type: {disruption_summary.get('most_common_disruption', 'Unknown')}"
            )
        
        # Finding 5: Top recommendation
        if recommendations:
            top_rec = recommendations[0]
            findings.append(
                f"Priority recommendation: {top_rec.get('action', 'Unknown')} ({top_rec.get('priority', 'Medium')} priority)"
            )
        
        return findings
    
    def _generate_strategic_insights(self, analysis: Dict) -> List[str]:
        """Generate strategic insights from the analysis"""
        insights = []
        
        # Get key data
        recommendations = analysis.get("recommendations", [])
        bottlenecks = analysis.get("bottlenecks", [])
        recovery_forecast = analysis.get("recovery_forecast", {})
        
        # Insight 1: Recovery timeline
        if recovery_forecast:
            insights.append(
                f"Estimated recovery time: {recovery_forecast.get('estimated_recovery_time', 'Unknown')} "
                f"with {recovery_forecast.get('confidence', 'medium')} confidence"
            )
        
        # Insight 2: Resource allocation
        if bottlenecks:
            bottleneck_categories = [b.get('category', 'Unknown') for b in bottlenecks]
            insights.append(
                f"Focus resources on {', '.join(bottleneck_categories)} categories to address "
                f"critical supply constraints"
            )
        
        # Insight 3: Long-term strategy
        high_priority_recs = [r for r in recommendations if r.get('priority') == 'High']
        if high_priority_recs:
            rec_types = {r.get('type', 'Unknown') for r in high_priority_recs}
            insights.append(
                f"Implement {', '.join(rec_types)} strategies to improve long-term "
                f"supply chain resilience"
            )
        
        # Insight 4: Monitoring focus
        insights.append(
            "Enhanced monitoring recommended for early detection of disruption patterns"
        )
        
        return insights
    
    def _generate_risk_assessment(self, highest_risk_categories: List[str]) -> Dict:
        """Generate risk assessment insights"""
        if not highest_risk_categories:
            return {
                "overall_risk_level": "Low",
                "high_risk_areas": ["None identified"],
                "risk_factors": ["No significant risk factors detected"]
            }
        
        # Determine overall risk level based on number of high-risk categories
        overall_risk_level = "Low"
        if len(highest_risk_categories) >= 3:
            overall_risk_level = "High"
        elif len(highest_risk_categories) >= 1:
            overall_risk_level = "Medium"
        
        # Determine risk factors based on categories
        risk_factors = [
            f"Supplier concentration and long lead times may affect {category.lower()} availability"
            for category in highest_risk_categories[:3]
        ]
        
        # Add general risk factors if needed
        if not risk_factors:
            risk_factors.append("Potential supplier reliability issues")
            risk_factors.append("Weather-related transportation disruptions")
        
        return {
            "overall_risk_level": overall_risk_level,
            "high_risk_areas": highest_risk_categories,
            "risk_factors": risk_factors
        }
    
    def _generate_performance_indicators(self, simulation_data: Dict) -> Dict:
        """Generate performance indicators for the supply chain"""
        # Extract data
        normal_results = simulation_data.get("normal_results", {})
        disrupted_results = simulation_data.get("disrupted_results", {})
        solution_results = simulation_data.get("solution_results", {})
        
        # Calculate production efficiency
        normal_production = sum(normal_results.get("manufacturer_production", {}).values())
        disrupted_production = sum(disrupted_results.get("manufacturer_production", {}).values())
        solution_production = sum(solution_results.get("manufacturer_production", {}).values())
        
        production_efficiency = 0
        if normal_production > 0:
            production_efficiency = disrupted_production / normal_production
        
        solution_efficiency = 0
        if normal_production > 0:
            solution_efficiency = solution_production / normal_production
        
        # Calculate supply continuity
        normal_supply = sum(normal_results.get("supplier_amounts", {}).values())
        disrupted_supply = sum(disrupted_results.get("supplier_amounts", {}).values())
        
        supply_continuity = 0
        if normal_supply > 0:
            supply_continuity = disrupted_supply / normal_supply
        
        # Calculate customer impact
        normal_customer = normal_results.get("customer_received", 0)
        disrupted_customer = disrupted_results.get("customer_received", 0)
        solution_customer = solution_results.get("customer_received", 0)
        
        customer_impact = 0
        if normal_customer > 0:
            customer_impact = (normal_customer - disrupted_customer) / normal_customer
        
        solution_effectiveness = 0
        if normal_customer > 0 and disrupted_customer < normal_customer:
            solution_improvement = solution_customer - disrupted_customer
            max_possible_improvement = normal_customer - disrupted_customer
            if max_possible_improvement > 0:
                solution_effectiveness = solution_improvement / max_possible_improvement
        
        # Calculate business impact
        impact_factor = (1 - production_efficiency) * 0.5 + customer_impact * 0.5
        business_impact = self._categorize_business_impact(impact_factor)
        
        return {
            "production_efficiency": production_efficiency,
            "production_efficiency_pct": f"{production_efficiency:.0%}",
            "supply_continuity": supply_continuity,
            "supply_continuity_pct": f"{supply_continuity:.0%}",
            "customer_impact": customer_impact,
            "customer_impact_pct": f"{customer_impact:.0%}",
            "solution_effectiveness": solution_effectiveness,
            "solution_effectiveness_pct": f"{solution_effectiveness:.0%}",
            "business_impact": business_impact,
            "impact_factor": impact_factor,
            "impact_factor_pct": f"{impact_factor:.0%}"
        }
    
    def _categorize_business_impact(self, impact_factor: float) -> str:
        """Categorize business impact based on impact factor"""
        if impact_factor < 0.1:
            return "Minimal"
        elif impact_factor < 0.25:
            return "Moderate"
        elif impact_factor < 0.5:
            return "Significant"
        else:
            return "Severe"
    
    def _calculate_resilience_score(self, production_efficiency: float, supply_continuity: float) -> Dict:
        """Calculate a resilience score for the supply chain"""
        # Calculate base score (0-100)
        base_score = (production_efficiency * 0.6 + supply_continuity * 0.4) * 100
        
        # Determine resilience level
        if base_score >= 80:
            level = "High"
        elif base_score >= 60:
            level = "Moderate"
        elif base_score >= 40:
            level = "Low"
        else:
            level = "Very Low"
        
        # Get interpretation
        interpretation = self._get_resilience_interpretation(level)
        
        return {
            "score": round(base_score),
            "score_label": f"{round(base_score)}/100",
            "level": level,
            "interpretation": interpretation,
            "components": {
                "production_continuity": f"{production_efficiency:.0%}",
                "supply_stability": f"{supply_continuity:.0%}"
            }
        }
    
    def _get_resilience_interpretation(self, level: str) -> str:
        """Get interpretation text for resilience level"""
        interpretations = {
            "High": "Supply chain demonstrates strong resilience with minimal disruption impact",
            "Moderate": "Supply chain shows adequate resilience but with room for improvement",
            "Low": "Supply chain exhibits vulnerability to disruptions and requires attention",
            "Very Low": "Supply chain demonstrates critical vulnerability requiring immediate action"
        }
        return interpretations.get(level, "Unable to determine resilience level")
    
    def _generate_trend_analysis(self) -> Dict:
        """Generate trend analysis based on historical data"""
        # Extract trend data from historical disruptions
        category_trends = {}
        for category, data in self.historical_disruptions.items():
            category_trends[category] = data["trend"]
        
        # Identify categories with increasing trends
        increasing_risk = [
            category for category, trend in category_trends.items() 
            if trend == "increasing"
        ]
        
        # Identify categories with decreasing trends
        decreasing_risk = [
            category for category, trend in category_trends.items() 
            if trend == "decreasing"
        ]
        
        # Generate interpretation
        if increasing_risk:
            trend_summary = f"Increasing disruption risk in {', '.join(increasing_risk)}"
        elif decreasing_risk:
            trend_summary = f"Overall improving trend with decreasing disruptions in {', '.join(decreasing_risk)}"
        else:
            trend_summary = "Stable disruption patterns across all categories"
        
        return {
            "trend_summary": trend_summary,
            "increasing_risk_categories": increasing_risk,
            "decreasing_risk_categories": decreasing_risk,
            "stable_categories": [
                category for category, trend in category_trends.items() 
                if trend == "stable"
            ],
            "category_trends": category_trends
        }
        
    def cluster_analysis(self, suppliers: List[Any]) -> Dict:
        """
        Perform cluster analysis on suppliers to identify patterns and groups
        
        Args:
            suppliers: List of supplier objects
            
        Returns:
            Dictionary with clustering results
        """
        if not suppliers or len(suppliers) < 3:
            return {
                "status": "insufficient_data",
                "message": "Not enough suppliers for meaningful cluster analysis",
                "clusters": []
            }
        
        # Extract features for clustering
        features = []
        supplier_names = []
        categories = []
        supply_amounts = []
        
        for supplier in suppliers:
            # Extract numeric features (supply amount, inventory)
            supply_amount = getattr(supplier, 'supply_amount', 50)  # Default to 50 if not available
            inventory = getattr(supplier, 'inventory', 100)  # Default to 100 if not available
            
            features.append([supply_amount, inventory])
            supplier_names.append(getattr(supplier, 'name', 'Unknown'))
            categories.append(getattr(supplier, 'category', 'Unknown'))
            supply_amounts.append(supply_amount)
        
        if not features:
            return {
                "status": "no_features",
                "message": "Could not extract features from suppliers",
                "clusters": []
            }
        
        # Normalize the data
        scaler = StandardScaler()
        features_scaled = scaler.fit_transform(features)
        
        # Determine optimal number of clusters (between 2 and 5)
        max_clusters = min(5, len(features) - 1)
        min_clusters = min(2, max_clusters)
        
        # Default to 3 clusters if we have enough data
        n_clusters = min(3, max_clusters)
        
        # Perform K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42)
        clusters = kmeans.fit_predict(features_scaled)
        
        # Analyze cluster characteristics
        cluster_data = []
        for i in range(n_clusters):
            # Get indices of suppliers in this cluster
            cluster_indices = [idx for idx, label in enumerate(clusters) if label == i]
            
            # Get categories in this cluster
            cluster_categories = [categories[idx] for idx in cluster_indices]
            
            # Find most common category
            category_counts = {}
            for category in cluster_categories:
                if category not in category_counts:
                    category_counts[category] = 0
                category_counts[category] += 1
            
            # Sort categories by count
            sorted_categories = sorted(
                category_counts.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            
            # Determine dominant category if any
            dominant_category = "Mixed"
            if sorted_categories:
                top_category, top_count = sorted_categories[0]
                if top_count / len(cluster_indices) > 0.5:  # If more than 50% are same category
                    dominant_category = top_category
            
            # Calculate average supply ratio (as percentage of maximum)
            cluster_supply = [supply_amounts[idx] for idx in cluster_indices]
            avg_supply = sum(cluster_supply) / len(cluster_supply) if cluster_supply else 0
            max_supply = max(supply_amounts) if supply_amounts else 100
            avg_supply_ratio = avg_supply / max_supply if max_supply > 0 else 0
            
            # Determine risk level based on supply ratio
            if avg_supply_ratio < 0.3:
                risk_level = "High"
                characteristics = "Low supply capacity"
            elif avg_supply_ratio < 0.7:
                risk_level = "Medium"
                characteristics = "Moderate supply capacity"
            else:
                risk_level = "Low"
                characteristics = "High supply capacity"
            
            cluster_data.append({
                "cluster_id": i,
                "size": len(cluster_indices),
                "suppliers": [supplier_names[idx] for idx in cluster_indices],
                "dominant_category": dominant_category,
                "categories": dict(sorted_categories),
                "avg_supply_ratio": avg_supply_ratio,
                "risk_level": risk_level,
                "characteristics": characteristics
            })
        
        return {
            "status": "success",
            "num_clusters": n_clusters,
            "clusters": cluster_data
        }
        
    def what_if_analysis(self, simulation_data: Dict, scenario: str) -> Dict:
        """
        Perform what-if analysis for different scenarios
        
        Args:
            simulation_data: Dictionary containing simulation results
            scenario: Type of scenario to analyze
            
        Returns:
            Dictionary with scenario analysis results
        """
        if scenario == "increased_disruption":
            return self._analyze_increased_disruption(simulation_data)
        elif scenario == "improved_resilience":
            return self._analyze_improved_resilience(simulation_data)
        elif scenario == "category_failure":
            return self._analyze_category_failure(simulation_data)
        elif scenario == "optimized_inventory":
            return self._analyze_optimized_inventory(simulation_data)
        else:
            return {
                "status": "error",
                "message": f"Unknown scenario: {scenario}"
            }
    
    def _analyze_increased_disruption(self, simulation_data: Dict) -> Dict:
        """Analyze the impact of increased disruption probability"""
        # Extract performance metrics
        perf = self._generate_performance_indicators(simulation_data)
        current_impact = perf.get("impact_factor", 0)
        
        # Extract current disruption rate
        disruption_analysis = self.analyze_disruptions(simulation_data)
        disruption_summary = disruption_analysis.get("disruption_summary", {})
        disruption_rate_str = disruption_summary.get("disruption_rate", "0%")
        current_rate = float(disruption_rate_str.strip("%"))/100 if disruption_rate_str else 0
        
        # Define increased disruption probability scenarios
        scenarios = [
            {"disruption_probability": current_rate + 0.1},
            {"disruption_probability": current_rate + 0.2},
            {"disruption_probability": current_rate + 0.3}
        ]
        
        # Model projected impact for each scenario
        for scenario in scenarios:
            # Simple model: Impact increases proportionally but with diminishing returns
            # This is a simplified projection that would be more sophisticated in a real system
            prob_increase = scenario["disruption_probability"] - current_rate
            impact_multiplier = 1 + (prob_increase * (2 - prob_increase))  # Non-linear impact curve
            
            # Calculate estimated impact
            scenario["estimated_impact_factor"] = min(current_impact * impact_multiplier, 1.0)
            
            # Calculate production decrease
            current_production = sum(simulation_data.get("normal_results", {}).get("manufacturer_production", {}).values())
            projected_production_ratio = 1 - scenario["estimated_impact_factor"]
            projected_production = current_production * projected_production_ratio
            current_disrupted_production = sum(simulation_data.get("disrupted_results", {}).get("manufacturer_production", {}).values())
            
            scenario["production_decrease"] = current_disrupted_production - projected_production
        
        return {
            "current_disruption_rate": disruption_rate_str,
            "current_impact_factor": f"{current_impact:.1%}",
            "projected_scenarios": scenarios
        }
    
    def _analyze_improved_resilience(self, simulation_data: Dict) -> Dict:
        """Analyze the impact of improved supply chain resilience"""
        # Extract performance metrics
        perf = self._generate_performance_indicators(simulation_data)
        current_impact = perf.get("impact_factor", 0)
        
        # Calculate current resilience score
        current_prod_efficiency = perf.get("production_efficiency", 0)
        current_supply_continuity = perf.get("supply_continuity", 0)
        current_resilience = self._calculate_resilience_score(current_prod_efficiency, current_supply_continuity)
        current_score = current_resilience.get("score", 50)
        
        # Define resilience improvement scenarios
        improvements = [
            {"resilience_improvement": "10%", "score_increase": 10},
            {"resilience_improvement": "25%", "score_increase": 25},
            {"resilience_improvement": "50%", "score_increase": 50}
        ]
        
        # Current production values
        normal_production = sum(simulation_data.get("normal_results", {}).get("manufacturer_production", {}).values())
        disrupted_production = sum(simulation_data.get("disrupted_results", {}).get("manufacturer_production", {}).values())
        production_loss = normal_production - disrupted_production
        
        # Model projected impact for each improvement
        for improvement in improvements:
            # Calculate new resilience score (cap at 100)
            new_score = min(current_score + improvement["score_increase"], 100)
            improvement["new_resilience_score"] = new_score
            
            # Calculate impact reduction based on resilience improvement
            # Higher resilience means lower impact
            impact_reduction_ratio = improvement["score_increase"] / 100
            new_impact = max(current_impact * (1 - impact_reduction_ratio), 0)
            improvement["new_impact_factor"] = new_impact
            
            # Calculate production increase
            production_recovery = production_loss * impact_reduction_ratio
            improvement["production_increase"] = production_recovery
            
            # Calculate new production level
            new_production = disrupted_production + production_recovery
            improvement["new_production_level"] = new_production
            improvement["production_recovery_pct"] = f"{(new_production/normal_production if normal_production > 0 else 0):.0%}"
        
        return {
            "current_resilience_score": current_score,
            "current_impact_factor": f"{current_impact:.1%}",
            "projected_improvements": improvements
        }
    
    def _analyze_category_failure(self, simulation_data: Dict) -> Dict:
        """Analyze the impact of a complete category failure"""
        # Get performance data
        perf = self._generate_performance_indicators(simulation_data)
        
        # Get categories from historical data
        categories = list(self.historical_disruptions.keys())
        
        # Extract category contributions from normal results
        normal_results = simulation_data.get("normal_results", {})
        normal_production = normal_results.get("manufacturer_production", {})
        
        # Calculate category contributions
        category_contributions = {}
        total_production = sum(normal_production.values())
        
        for category in categories:
            # Sum up production for manufacturers in this category
            category_production = sum(value for key, value in normal_production.items() if f"({category})" in key)
            contribution = category_production / total_production if total_production > 0 else 0
            category_contributions[category] = contribution
        
        # Model failure scenarios
        failure_scenarios = []
        for category, contribution in category_contributions.items():
            # Skip categories with minimal contribution
            if contribution < 0.05:
                continue
                
            # Calculate business impact
            impact_factor = contribution * 1.5  # Category failure has cascading effects
            business_impact = self._categorize_business_impact(impact_factor)
            
            # Estimate recovery time
            recovery_time = self._estimate_category_recovery_time(contribution)
            
            # Generate recovery strategy
            recovery_strategy = self._generate_category_recovery_strategy(category, business_impact)
            
            failure_scenarios.append({
                "category": category,
                "contribution": f"{contribution:.0%}",
                "impact_factor": impact_factor,
                "business_impact": business_impact,
                "estimated_recovery_time": recovery_time,
                "recovery_strategy": recovery_strategy
            })
        
        # Identify critical dependencies
        critical_dependencies = self._identify_critical_dependencies([])
        
        return {
            "current_business_impact": perf.get("business_impact", "Unknown"),
            "failure_scenarios": failure_scenarios,
            "critical_dependencies": critical_dependencies
        }
    
    def _estimate_category_recovery_time(self, contribution: float) -> str:
        """Estimate recovery time based on category contribution"""
        if contribution < 0.1:
            return "1-2 weeks"
        elif contribution < 0.25:
            return "3-4 weeks"
        elif contribution < 0.4:
            return "1-2 months"
        else:
            return "2-3 months"
    
    def _generate_category_recovery_strategy(self, category: str, impact: str) -> List[str]:
        """Generate recovery strategy for a category failure"""
        strategies = []
        
        # Common strategies
        strategies.append(f"Identify alternative suppliers for {category} equipment")
        strategies.append(f"Implement emergency logistics routes for {category} components")
        
        # Impact-specific strategies
        if impact in ["Significant", "Severe"]:
            strategies.append(f"Establish crisis response team for {category} recovery")
            strategies.append("Develop customer allocation prioritization framework")
            strategies.append("Implement daily executive briefings during recovery")
        else:
            strategies.append(f"Increase monitoring frequency for {category} supply chain")
            strategies.append("Maintain weekly stakeholder communication plan")
        
        return strategies
    
    def _identify_critical_dependencies(self, category_impacts: List[Dict]) -> List[Dict]:
        """Identify critical dependencies between categories"""
        dependencies = []
        
        # This is a simplified approach - in a real system we would use a graph or network model
        # to identify actual dependencies between categories
        
        # Sort categories by impact
        sorted_impacts = sorted(category_impacts, key=lambda x: x.get("impact_percentage", 0), reverse=True)
        
        # Define some standard dependencies based on impact relationships
        if len(sorted_impacts) >= 2:
            # Assume the highest impact category might affect the second highest
            dependencies.append({
                "source": sorted_impacts[0].get("category", "Unknown"),
                "target": sorted_impacts[1].get("category", "Unknown"),
                "dependency_type": "Supply chain",
                "criticality": "High"
            })
            
        if len(sorted_impacts) >= 3:
            # Assume some component dependencies
            dependencies.append({
                "source": sorted_impacts[0].get("category", "Unknown"),
                "target": sorted_impacts[2].get("category", "Unknown"),
                "dependency_type": "Component",
                "criticality": "Medium"
            })
        
        # Illustrative construction-equipment component dependencies. Only
        # surface links whose equipment categories are in the current analysis.
        available_categories = {item.get("category") for item in category_impacts}
        for component, equipment, dependency_type in [
            ("Hydraulic systems", "Excavators", "Component"),
            ("High-strength steel", "Cranes", "Raw Material"),
            ("Engine systems", "Dump Trucks", "Component"),
            ("Hydraulic systems", "Wheel Loaders", "Component"),
        ]:
            if equipment in available_categories:
                dependencies.append({
                    "source": component,
                    "target": equipment,
                    "dependency_type": dependency_type,
                    "criticality": "High"
                })
        
        return dependencies
    
    def _analyze_optimized_inventory(self, simulation_data: Dict) -> Dict:
        """Analyze the impact of optimized inventory levels"""
        # Get performance data
        perf = self._generate_performance_indicators(simulation_data)
        
        # Extract disruption analysis
        disruption_analysis = self.analyze_disruptions(simulation_data)
        category_impacts = disruption_analysis.get("category_impacts", [])
        
        # Generate inventory recommendations
        inventory_recommendations = []
        for impact in category_impacts:
            category = impact.get("category", "Unknown")
            impact_pct = impact.get("impact_percentage", 0)
            
            # Skip categories with minimal impact
            if impact_pct < 5:
                continue
            
            # Calculate recommended inventory increase
            if impact_pct >= 40:
                inventory_increase = "50%"
                priority = "High"
            elif impact_pct >= 20:
                inventory_increase = "30%"
                priority = "Medium"
            else:
                inventory_increase = "15%"
                priority = "Low"
            
            # Calculate benefit
            benefit = self._get_inventory_benefit(inventory_increase)
            
            inventory_recommendations.append({
                "category": category,
                "current_impact": f"{impact_pct:.1f}%",
                "recommended_increase": inventory_increase,
                "priority": priority,
                "expected_benefit": benefit
            })
        
        # Estimate overall service level improvement
        service_level_change = self._estimate_service_level_change(inventory_recommendations)
        
        # Calculate inventory cost implications (simplified)
        total_increase_pct = sum(
            float(rec.get("recommended_increase", "0%").strip("%")) / 100
            for rec in inventory_recommendations
        ) / len(inventory_recommendations) if inventory_recommendations else 0
        
        inventory_cost_increase = total_increase_pct * 0.8  # Assuming some economies of scale
        
        return {
            "current_service_level": f"{(1 - perf.get('customer_impact', 0)):.0%}",
            "projected_service_level": f"{(1 - perf.get('customer_impact', 0) + service_level_change):.0%}",
            "inventory_recommendations": inventory_recommendations,
            "inventory_cost_implication": f"+{inventory_cost_increase:.0%} inventory holding cost",
            "roi_period": "3-6 months" if service_level_change > 0.1 else "6-12 months"
        }
    
    def _get_inventory_benefit(self, recommendation: str) -> str:
        """Get the expected benefit text based on inventory recommendation"""
        increase = float(recommendation.strip("%")) / 100
        
        if increase >= 0.4:
            return "Significant reduction in stockouts and disruption impact"
        elif increase >= 0.2:
            return "Moderate reduction in supply chain vulnerability"
        else:
            return "Incremental improvement in supply continuity"
    
    def _estimate_service_level_change(self, recommendations: List[Dict]) -> float:
        """Estimate the change in service level based on inventory recommendations"""
        if not recommendations:
            return 0.0
        
        # Calculate weighted average of impact reduction
        total_weight = 0
        weighted_improvement = 0
        
        for rec in recommendations:
            # Extract priority and convert to weight
            priority = rec.get("priority", "Medium")
            weight = 3 if priority == "High" else (2 if priority == "Medium" else 1)
            
            # Extract inventory increase percentage
            increase_str = rec.get("recommended_increase", "0%")
            increase = float(increase_str.strip("%")) / 100
            
            # Assume diminishing returns on inventory increases
            service_improvement = math.sqrt(increase) * 0.1  # Non-linear scaling
            
            weighted_improvement += service_improvement * weight
            total_weight += weight
        
        # Return average improvement
        return weighted_improvement / total_weight if total_weight > 0 else 0


class AdvancedAnalyticsEngine:
    """
    Advanced analytics engine for supply chain simulation that provides
    decision support and visualization capabilities.
    """
    
    def __init__(self):
        self.agent = SupplyChainAgent()
    
    def analyze_simulation(self, simulation_data: Dict) -> Dict:
        """
        Analyze simulation data and provide comprehensive insights
        
        Args:
            simulation_data: Dictionary containing simulation results
            
        Returns:
            Dictionary with analysis results
        """
        # Get disruption analysis
        disruption_analysis = self.agent.analyze_disruptions(simulation_data)
        
        # Generate high-level insights
        insights = self.agent.generate_insights(simulation_data)
        
        # Run cluster analysis if suppliers are available
        suppliers = simulation_data.get("suppliers", [])
        cluster_analysis = self.agent.cluster_analysis(suppliers)
        
        # Run what-if analyses
        what_if_scenarios = {
            "increased_disruption": self.agent.what_if_analysis(simulation_data, "increased_disruption"),
            "improved_resilience": self.agent.what_if_analysis(simulation_data, "improved_resilience"),
            "category_failure": self.agent.what_if_analysis(simulation_data, "category_failure")
        }
        
        # Prepare visualization data
        visualization_data = self._prepare_visualization_data(simulation_data, disruption_analysis)
        
        # Generate executive summary
        executive_summary = self._generate_executive_summary(insights, disruption_analysis)
        
        return {
            "disruption_analysis": disruption_analysis,
            "summary": insights,
            "cluster_analysis": cluster_analysis,
            "what_if_scenarios": what_if_scenarios,
            "visualization_data": visualization_data,
            "executive_summary": executive_summary
        }
    
    def _prepare_visualization_data(self, 
                                   simulation_data: Dict, 
                                   disruption_analysis: Dict) -> Dict:
        """Prepare data for visualization"""
        # Extract metrics for line charts
        normal_results = simulation_data.get("normal_results", {})
        disrupted_results = simulation_data.get("disrupted_results", {})
        solution_results = simulation_data.get("solution_results", {})
        
        # Prepare production comparison
        production_comparison = {
            "labels": ["Normal", "Disrupted", "With Solutions"],
            "values": [
                sum(normal_results.get("manufacturer_production", {}).values()),
                sum(disrupted_results.get("manufacturer_production", {}).values()),
                sum(solution_results.get("manufacturer_production", {}).values())
            ]
        }
        
        # Prepare customer impact comparison
        customer_comparison = {
            "labels": ["Normal", "Disrupted", "With Solutions"],
            "values": [
                normal_results.get("customer_received", 0),
                disrupted_results.get("customer_received", 0),
                solution_results.get("customer_received", 0)
            ]
        }
        
        # Prepare category impact data
        category_impacts = disruption_analysis.get("category_impacts", [])
        category_comparison = {
            "categories": [impact.get("category", "Unknown") for impact in category_impacts],
            "impact_percentages": [impact.get("impact_percentage", 0) for impact in category_impacts]
        }
        
        return {
            "production_comparison": production_comparison,
            "customer_comparison": customer_comparison,
            "category_comparison": category_comparison
        }
    
    def _generate_executive_summary(self, 
                                   insights: Dict, 
                                   disruption_analysis: Dict) -> Dict:
        """Generate an executive summary of the analysis"""
        # Extract key metrics
        headline = insights.get("headline", "Supply Chain Analysis")
        key_metrics = insights.get("key_metrics", {})
        top_insights = insights.get("top_insights", [])
        
        # Get top recommendations
        recommendations = disruption_analysis.get("recommendations", [])
        top_recommendations = recommendations[:3] if recommendations else []
        
        # Format action items
        action_items = []
        for rec in top_recommendations:
            action_items.append({
                "action": rec.get("action", "Unknown action"),
                "priority": rec.get("priority", "Medium"),
                "target": rec.get("target", "General")
            })
        
        return {
            "headline": headline,
            "overview": " ".join(top_insights[:2]) if top_insights else "No insights available",
            "key_metrics": key_metrics,
            "action_items": action_items
        }
        
    def get_historical_trends(self) -> Dict:
        """Analyze historical simulation data to identify trends"""
        # This would normally analyze a database of past simulations
        # For demonstration, return synthetic trend data
        
        return {
            "disruption_frequency_trend": "increasing",
            "avg_disruption_duration": "12 days",
            "most_affected_category": max(
                self.agent.historical_disruptions,
                key=lambda category: self.agent.historical_disruptions[category]["count"]
            ),
            "category_trends": self.agent._generate_trend_analysis().get("category_trends", {})
        }


def get_agent_recommendations(simulation_data: Dict) -> Dict:
    """
    Get advanced recommendations from the supply chain agent
    
    Args:
        simulation_data: Dictionary containing simulation results
        
    Returns:
        Dictionary with analysis and recommendations
    """
    # Initialize the analytics engine
    engine = AdvancedAnalyticsEngine()
    
    # Get comprehensive analysis
    analysis = engine.analyze_simulation(simulation_data)
    
    return analysis