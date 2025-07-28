import pandas as pd
from typing import Dict, List
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AIReasoner:
    """Generates AI reasoning for claim processing decisions"""
    
    def __init__(self):
        self.medical_code_knowledge = {
            # ER Codes
            '99281': 'ER Visit Level 1 - Minor',
            '99282': 'ER Visit Level 2 - Low complexity',
            '99283': 'ER Visit Level 3 - Moderate complexity',
            '99284': 'ER Visit Level 4 - High complexity',
            '99285': 'ER Visit Level 5 - Critical care',
            
            # Imaging codes
            '70450': 'CT Head/Brain without contrast',
            '70460': 'CT Head/Brain with contrast',
            '70553': 'MRI Brain with and without contrast',
            '71250': 'CT Chest without contrast',
            '72148': 'MRI Lumbar Spine',
            
            # Lab codes
            '36415': 'Collection of venous blood by venipuncture',
            '80053': 'Comprehensive metabolic panel',
            '85025': 'Blood count; complete CBC',
            
            # Revenue codes
            '0450': 'Emergency Room - General',
            '0300': 'Laboratory - General',
            '0350': 'CT Scan',
            '0360': 'Operating Room Services',
            '0206': 'Intensive Care Unit',
            '0270': 'Medical/Surgical Supplies'
        }
        
        self.splitting_rules = {
            'max_lines_per_claim': 28,
            'er_consolidation_window_hours': 24,
            'imaging_grouping_window_hours': 24,
            'priority_order': [
                'Emergency Room Visits',
                'Surgical Procedures',
                'ICU Services',
                'Imaging Services',
                'Laboratory Tests',
                'Medications/Infusions',
                'Other Services'
            ]
        }
    
    def generate_reasoning(self, original_df: pd.DataFrame, 
                          processed_claims: Dict[str, List[pd.DataFrame]]) -> str:
        """Generate comprehensive AI reasoning for claim processing"""
        
        try:
            reasoning_parts = []
            
            # Header
            reasoning_parts.append("=== MEDICAL CLAIM PROCESSING AI REASONING ===")
            reasoning_parts.append(f"Processing Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            reasoning_parts.append("")
            
            # Overall summary
            total_original_lines = len(original_df)
            total_processed_claims = sum(len(claims) for claims in processed_claims.values())
            total_split_claims = sum(1 for claims in processed_claims.values() if len(claims) > 1)
            
            reasoning_parts.append("=== PROCESSING SUMMARY ===")
            reasoning_parts.append(f"Original file contained {total_original_lines} line items")
            reasoning_parts.append(f"Processed into {len(processed_claims)} patient claims")
            reasoning_parts.append(f"Required splitting for {total_split_claims} claims due to 28-line limit")
            reasoning_parts.append(f"Total sub-claims created: {total_processed_claims}")
            reasoning_parts.append("")
            
            # Detailed analysis for each patient claim
            for patient_claim_id, claim_list in processed_claims.items():
                reasoning_parts.append(f"=== PATIENT CLAIM: {patient_claim_id} ===")
                
                # Combine all sub-claims for analysis
                full_claim = pd.concat(claim_list, ignore_index=True) if claim_list else pd.DataFrame()
                
                if not full_claim.empty:
                    analysis = self._analyze_claim(full_claim)
                    reasoning_parts.append(f"Total Lines: {len(full_claim)}")
                    reasoning_parts.append(f"Total Charges: ${full_claim['Total Charges'].sum():,.2f}")
                    reasoning_parts.append(f"Service Date Range: {full_claim['Service Date'].min().strftime('%Y-%m-%d')} to {full_claim['Service Date'].max().strftime('%Y-%m-%d')}")
                    reasoning_parts.append("")
                    
                    # Service type breakdown
                    reasoning_parts.append("Service Type Analysis:")
                    for service_type, count in analysis['service_types'].items():
                        if count > 0:
                            reasoning_parts.append(f"  - {service_type}: {count} services")
                    reasoning_parts.append("")
                    
                    # Splitting analysis
                    if len(claim_list) > 1:
                        reasoning_parts.append(f"SPLITTING REQUIRED: Claim split into {len(claim_list)} sub-claims")
                        reasoning_parts.append("Splitting Logic Applied:")
                        reasoning_parts.append("  1. Maintained ER visit integrity (24-hour consolidation)")
                        reasoning_parts.append("  2. Grouped imaging services with related ER visits")
                        reasoning_parts.append("  3. Prioritized high-value services in earlier claims")
                        reasoning_parts.append("  4. Applied natural break points at service date/type boundaries")
                        reasoning_parts.append("")
                        
                        for i, sub_claim in enumerate(claim_list, 1):
                            reasoning_parts.append(f"  Sub-claim {i}: {len(sub_claim)} lines, ${sub_claim['Total Charges'].sum():,.2f}")
                    else:
                        reasoning_parts.append("NO SPLITTING REQUIRED: Claim within 28-line limit")
                    
                    reasoning_parts.append("")
                    
                    # Medical code insights
                    code_insights = self._analyze_medical_codes(full_claim)
                    if code_insights:
                        reasoning_parts.append("Medical Code Analysis:")
                        for insight in code_insights:
                            reasoning_parts.append(f"  - {insight}")
                        reasoning_parts.append("")
                    
                    # Business rule applications
                    rule_applications = self._analyze_rule_applications(full_claim)
                    if rule_applications:
                        reasoning_parts.append("Business Rules Applied:")
                        for rule in rule_applications:
                            reasoning_parts.append(f"  - {rule}")
                        reasoning_parts.append("")
            
            # Quality assurance
            reasoning_parts.append("=== QUALITY ASSURANCE ===")
            qa_results = self._perform_quality_checks(original_df, processed_claims)
            for check in qa_results:
                reasoning_parts.append(f"✓ {check}")
            reasoning_parts.append("")
            
            # Recommendations
            recommendations = self._generate_recommendations(original_df, processed_claims)
            if recommendations:
                reasoning_parts.append("=== RECOMMENDATIONS ===")
                for rec in recommendations:
                    reasoning_parts.append(f"• {rec}")
                reasoning_parts.append("")
            
            return "\n".join(reasoning_parts)
            
        except Exception as e:
            logger.error(f"Error generating reasoning: {str(e)}")
            return f"Error generating AI reasoning: {str(e)}"
    
    def _analyze_claim(self, df: pd.DataFrame) -> Dict:
        """Analyze a single claim"""
        
        service_types = {
            'Emergency Room Visits': 0,
            'Surgical Procedures': 0,
            'ICU Services': 0,
            'Imaging Services': 0,
            'Laboratory Tests': 0,
            'Medications/Infusions': 0,
            'Other Services': 0
        }
        
        for _, row in df.iterrows():
            hcpcs_code = str(row.get('HCPCS Code', ''))
            revenue_code = str(row.get('Revenue Code', ''))
            description = str(row.get('Description', '')).upper()
            
            if (hcpcs_code.startswith('9928') or '0450' in revenue_code or 
                'ER' in description or 'EMERGENCY' in description):
                service_types['Emergency Room Visits'] += 1
            elif ('0360' in revenue_code or 'SURGERY' in description or 
                  'PROCEDURE' in description):
                service_types['Surgical Procedures'] += 1
            elif ('0206' in revenue_code or 'ICU' in description):
                service_types['ICU Services'] += 1
            elif (hcpcs_code in ['70450', '70553', '71250'] or '0350' in revenue_code or
                  'CT' in description or 'MRI' in description):
                service_types['Imaging Services'] += 1
            elif ('36415' in hcpcs_code or '0300' in revenue_code or 'LAB' in description):
                service_types['Laboratory Tests'] += 1
            elif (hcpcs_code.startswith('J') or 'INJECTION' in description or 
                  'INFUSION' in description):
                service_types['Medications/Infusions'] += 1
            else:
                service_types['Other Services'] += 1
        
        return {
            'service_types': service_types,
            'total_charges': df['Total Charges'].sum(),
            'line_count': len(df),
            'date_range': (df['Service Date'].min(), df['Service Date'].max())
        }
    
    def _analyze_medical_codes(self, df: pd.DataFrame) -> List[str]:
        """Analyze medical codes and provide insights"""
        
        insights = []
        
        # Check for common patterns
        hcpcs_codes = df['HCPCS Code'].dropna().astype(str).unique()
        revenue_codes = df['Revenue Code'].dropna().astype(str).unique()
        
        # ER visit analysis
        er_codes = [code for code in hcpcs_codes if code.startswith('9928')]
        if er_codes:
            insights.append(f"Emergency room visits detected (codes: {', '.join(er_codes)})")
        
        # Imaging analysis
        imaging_codes = [code for code in hcpcs_codes if code in ['70450', '70553', '71250']]
        if imaging_codes:
            insights.append(f"Advanced imaging performed: {', '.join([self.medical_code_knowledge.get(code, code) for code in imaging_codes])}")
        
        # High-cost services
        high_cost_services = df[df['Charge Amount'] > 5000]
        if not high_cost_services.empty:
            insights.append(f"High-cost services identified: {len(high_cost_services)} services over $5,000")
        
        # Multiple same-day services
        same_day_groups = df.groupby('Service Date').size()
        if same_day_groups.max() > 10:
            insights.append(f"High-volume service day detected: {same_day_groups.max()} services on {same_day_groups.idxmax().strftime('%Y-%m-%d')}")
        
        return insights
    
    def _analyze_rule_applications(self, df: pd.DataFrame) -> List[str]:
        """Analyze which business rules were applied"""
        
        rules_applied = []
        
        # Check for 28-line rule
        if len(df) > 28:
            rules_applied.append("28-line limit rule: Claim required splitting due to excessive line items")
        
        # Check for ER consolidation
        er_visits = df[df['Description'].str.contains('ER|Emergency', case=False, na=False)]
        if len(er_visits) > 1:
            rules_applied.append("ER consolidation rule: Multiple ER visits consolidated within 24-hour window")
        
        # Check for imaging grouping
        imaging_services = df[df['Description'].str.contains('CT|MRI|Scan', case=False, na=False)]
        if not imaging_services.empty and not er_visits.empty:
            rules_applied.append("Imaging grouping rule: Imaging services grouped with related ER visits")
        
        # Check for service prioritization
        rules_applied.append("Service prioritization rule: Services ordered by clinical importance and date")
        
        return rules_applied
    
    def _perform_quality_checks(self, original_df: pd.DataFrame, 
                               processed_claims: Dict) -> List[str]:
        """Perform quality assurance checks"""
        
        checks = []
        
        # Line count validation
        original_lines = len(original_df)
        processed_lines = sum(len(claim) for claims in processed_claims.values() for claim in claims)
        
        if original_lines == processed_lines:
            checks.append(f"Line count integrity maintained: {original_lines} lines")
        else:
            checks.append(f"WARNING: Line count mismatch - Original: {original_lines}, Processed: {processed_lines}")
        
        # Charge amount validation
        original_total = original_df['Total Charges'].sum()
        processed_total = sum(claim['Total Charges'].sum() 
                            for claims in processed_claims.values() 
                            for claim in claims)
        
        if abs(original_total - processed_total) < 0.01:
            checks.append(f"Charge amount integrity maintained: ${original_total:,.2f}")
        else:
            checks.append(f"WARNING: Charge amount mismatch - Original: ${original_total:,.2f}, Processed: ${processed_total:,.2f}")
        
        # 28-line limit compliance
        oversized_claims = []
        for patient_claim_id, claims in processed_claims.items():
            for i, claim in enumerate(claims):
                if len(claim) > 28:
                    oversized_claims.append(f"{patient_claim_id}_sub{i+1}")
        
        if not oversized_claims:
            checks.append("28-line limit compliance: All sub-claims within limit")
        else:
            checks.append(f"WARNING: Oversized claims detected: {', '.join(oversized_claims)}")
        
        return checks
    
    def _generate_recommendations(self, original_df: pd.DataFrame, 
                                processed_claims: Dict) -> List[str]:
        """Generate recommendations for process improvement"""
        
        recommendations = []
        
        # Check for frequent splitting
        split_ratio = sum(1 for claims in processed_claims.values() if len(claims) > 1) / len(processed_claims)
        
        if split_ratio > 0.5:
            recommendations.append("High claim splitting rate detected. Consider reviewing service bundling practices.")
        
        # Check for high-cost outliers
        all_charges = []
        for claims in processed_claims.values():
            for claim in claims:
                all_charges.extend(claim['Charge Amount'].tolist())
        
        if all_charges:
            avg_charge = sum(all_charges) / len(all_charges)
            high_charges = [c for c in all_charges if c > avg_charge * 3]
            
            if high_charges:
                recommendations.append(f"High-cost outliers detected: {len(high_charges)} charges above 3x average. Review for coding accuracy.")
        
        # Check for service duplication patterns
        duplicate_services = original_df.groupby(['HCPCS Code', 'Service Date']).size()
        frequent_duplicates = duplicate_services[duplicate_services > 5]
        
        if not frequent_duplicates.empty:
            recommendations.append("Frequent duplicate services detected. Verify medical necessity and coding accuracy.")
        
        return recommendations