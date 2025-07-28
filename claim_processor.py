import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import logging

logger = logging.getLogger(__name__)

class ClaimProcessor:
    """Processes medical claims according to business rules"""
    
    def __init__(self):
        # Medical code knowledge base
        self.er_codes = {
            '99281', '99282', '99283', '99284', '99285',  # ER visit codes
            '0450', '0451', '0452', '0459'  # ER revenue codes
        }
        
        self.imaging_codes = {
            '70450', '70460', '70470',  # CT Head
            '70551', '70552', '70553',  # MRI Brain
            '71250', '71260', '71270',  # CT Chest
            '72148', '72149', '72158',  # MRI Spine
            '73700', '73701', '73702',  # CT extremities
            '76700', '76705',  # Ultrasound
            '78015', '78016',  # Thyroid scan
        }
        
        self.imaging_revenue_codes = {'0350', '0351', '0352', '0359'}
        
        self.lab_codes = {
            '36415',  # Lab draw
            '80053', '80048', '80061',  # Basic metabolic panels
            '85025', '85027',  # CBC codes
            '84484', '82947',  # Common lab tests
        }
        
        self.lab_revenue_codes = {'0300', '0301', '0302', '0309'}
        
        # ICU and high-cost procedure codes
        self.icu_codes = {'0200', '0201', '0202', '0206', '0209'}
        self.surgery_codes = {'0360', '0361', '0369', '0370', '0371', '0379'}
        
    def process_claims(self, df: pd.DataFrame, custom_rules: Dict = None) -> Dict[str, List[pd.DataFrame]]:
        """
        Process claims according to business rules
        Returns: Dictionary with patient_claim_id as key and list of split DataFrames as value
        """
        try:
            # Set default rules
            rules = {
                'max_lines': 28,
                'er_consolidation': True,
                'imaging_grouping': True,
                'custom_prompt': ''
            }
            
            if custom_rules:
                rules.update(custom_rules)
            
            # Convert Service Date to datetime
            df['Service Date'] = pd.to_datetime(df['Service Date'])
            
            # Group by Patient ID and Claim ID
            grouped_claims = df.groupby(['Patient ID', 'Claim ID'])
            
            processed_claims = {}
            
            for (patient_id, claim_id), claim_group in grouped_claims:
                patient_claim_id = f"{patient_id}_{claim_id}"
                logger.info(f"Processing claim: {patient_claim_id} with {len(claim_group)} lines")
                
                # Apply business rules and split if necessary
                split_claims = self._apply_business_rules(claim_group, rules)
                processed_claims[patient_claim_id] = split_claims
            
            return processed_claims
            
        except Exception as e:
            logger.error(f"Error processing claims: {str(e)}")
            raise
    
    def _apply_business_rules(self, claim_df: pd.DataFrame, rules: Dict) -> List[pd.DataFrame]:
        """Apply business rules to split claims"""
        
        # Sort by service date and priority
        claim_df = self._prioritize_services(claim_df)
        
        # If claim has <= max_lines, no splitting needed
        if len(claim_df) <= rules['max_lines']:
            return [claim_df]
        
        # Apply ER consolidation rule
        if rules['er_consolidation']:
            claim_df = self._consolidate_er_visits(claim_df)
        
        # Apply imaging grouping rule
        if rules['imaging_grouping']:
            claim_df = self._group_imaging_with_er(claim_df)
        
        # Split into multiple claims if still over limit
        return self._split_by_line_limit(claim_df, rules['max_lines'])
    
    def _prioritize_services(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prioritize services by importance and date"""
        
        def get_priority(row):
            hcpcs_code = str(row.get('HCPCS Code', ''))
            revenue_code = str(row.get('Revenue Code', ''))
            description = str(row.get('Description', '')).upper()
            
            # Priority 1: ER visits (highest priority)
            if (hcpcs_code in self.er_codes or 
                revenue_code in self.er_codes or 
                'ER' in description or 'EMERGENCY' in description):
                return 1
            
            # Priority 2: Surgery and high-cost procedures
            if (revenue_code in self.surgery_codes or
                'SURGERY' in description or 'PROCEDURE' in description):
                return 2
            
            # Priority 3: ICU charges
            if (revenue_code in self.icu_codes or
                'ICU' in description or 'INTENSIVE' in description):
                return 3
            
            # Priority 4: Imaging (should be grouped with ER)
            if (hcpcs_code in self.imaging_codes or
                revenue_code in self.imaging_revenue_codes or
                'CT' in description or 'MRI' in description or 'SCAN' in description):
                return 4
            
            # Priority 5: Labs
            if (hcpcs_code in self.lab_codes or
                revenue_code in self.lab_revenue_codes or
                'LAB' in description):
                return 5
            
            # Priority 6: Medications and infusions
            if ('INJECTION' in description or 'INFUSION' in description or
                hcpcs_code.startswith('J')):
                return 6
            
            # Priority 7: Everything else
            return 7
        
        df['Priority'] = df.apply(get_priority, axis=1)
        return df.sort_values(['Service Date', 'Priority', 'Charge Amount'], 
                            ascending=[True, True, False])
    
    def _consolidate_er_visits(self, df: pd.DataFrame) -> pd.DataFrame:
        """Consolidate ER visits within 24 hours"""
        
        er_visits = df[df['Priority'] == 1].copy()
        
        if len(er_visits) <= 1:
            return df
        
        # Group ER visits within 24 hours
        consolidated_groups = []
        remaining_visits = er_visits.copy()
        
        while not remaining_visits.empty:
            # Take the earliest visit
            anchor_visit = remaining_visits.iloc[0]
            anchor_date = anchor_visit['Service Date']
            
            # Find all visits within 24 hours
            within_24h = remaining_visits[
                (remaining_visits['Service Date'] >= anchor_date) &
                (remaining_visits['Service Date'] <= anchor_date + timedelta(hours=24))
            ]
            
            consolidated_groups.append(within_24h)
            remaining_visits = remaining_visits.drop(within_24h.index)
        
        # Keep the highest charge ER visit from each group
        consolidated_er = []
        for group in consolidated_groups:
            # Keep the highest charge ER visit
            highest_charge = group.loc[group['Charge Amount'].idxmax()]
            consolidated_er.append(highest_charge)
        
        # Combine with non-ER services
        non_er_services = df[df['Priority'] != 1]
        consolidated_df = pd.concat([pd.DataFrame(consolidated_er), non_er_services], 
                                  ignore_index=True)
        
        return consolidated_df.sort_values(['Service Date', 'Priority'])
    
    def _group_imaging_with_er(self, df: pd.DataFrame) -> pd.DataFrame:
        """Group imaging services with related ER visits"""
        
        er_visits = df[df['Priority'] == 1].copy()
        imaging_services = df[df['Priority'] == 4].copy()
        
        if er_visits.empty or imaging_services.empty:
            return df
        
        # For each imaging service, find the closest ER visit within 24 hours
        grouped_imaging = []
        remaining_imaging = imaging_services.copy()
        
        for _, er_visit in er_visits.iterrows():
            er_date = er_visit['Service Date']
            
            # Find imaging within 24 hours of ER visit
            related_imaging = remaining_imaging[
                (remaining_imaging['Service Date'] >= er_date - timedelta(hours=2)) &
                (remaining_imaging['Service Date'] <= er_date + timedelta(hours=24))
            ]
            
            if not related_imaging.empty:
                # Group these imaging services with the ER visit
                for idx, imaging in related_imaging.iterrows():
                    grouped_imaging.append(imaging)
                
                remaining_imaging = remaining_imaging.drop(related_imaging.index)
        
        # Combine grouped imaging with other services
        other_services = df[(df['Priority'] != 4) | 
                           (df.index.isin(remaining_imaging.index))]
        
        if grouped_imaging:
            grouped_df = pd.concat([other_services, pd.DataFrame(grouped_imaging)], 
                                 ignore_index=True)
        else:
            grouped_df = other_services
        
        return grouped_df.sort_values(['Service Date', 'Priority'])
    
    def _split_by_line_limit(self, df: pd.DataFrame, max_lines: int) -> List[pd.DataFrame]:
        """Split DataFrame into multiple claims based on line limit"""
        
        if len(df) <= max_lines:
            return [df]
        
        claims = []
        current_start = 0
        
        while current_start < len(df):
            current_end = min(current_start + max_lines, len(df))
            
            # Try to keep related services together
            if current_end < len(df):
                # Look for a natural break point (different service date or priority)
                for i in range(current_end - 5, current_end):
                    if i > current_start:
                        current_row = df.iloc[i]
                        next_row = df.iloc[i + 1] if i + 1 < len(df) else None
                        
                        if (next_row is not None and 
                            (current_row['Service Date'] != next_row['Service Date'] or
                             current_row['Priority'] != next_row['Priority'])):
                            current_end = i + 1
                            break
            
            claim_slice = df.iloc[current_start:current_end].copy()
            claims.append(claim_slice)
            current_start = current_end
        
        return claims
    
    def _calculate_claim_totals(self, df: pd.DataFrame) -> Dict:
        """Calculate claim totals and statistics"""
        
        return {
            'total_lines': len(df),
            'total_charges': df['Total Charges'].sum(),
            'service_date_range': {
                'start': df['Service Date'].min(),
                'end': df['Service Date'].max()
            },
            'service_types': {
                'er_visits': len(df[df['Priority'] == 1]),
                'surgeries': len(df[df['Priority'] == 2]),
                'icu_days': len(df[df['Priority'] == 3]),
                'imaging': len(df[df['Priority'] == 4]),
                'labs': len(df[df['Priority'] == 5]),
                'medications': len(df[df['Priority'] == 6]),
                'other': len(df[df['Priority'] == 7])
            }
        }
    
    def validate_claim_integrity(self, original_df: pd.DataFrame, 
                                processed_claims: List[pd.DataFrame]) -> Dict:
        """Validate that claim splitting maintains data integrity"""
        
        # Combine all processed claims
        combined_df = pd.concat(processed_claims, ignore_index=True)
        
        validation_results = {
            'line_count_match': len(original_df) == len(combined_df),
            'charge_total_match': abs(original_df['Total Charges'].sum() - 
                                    combined_df['Total Charges'].sum()) < 0.01,
            'original_lines': len(original_df),
            'processed_lines': len(combined_df),
            'original_total': original_df['Total Charges'].sum(),
            'processed_total': combined_df['Total Charges'].sum(),
            'claims_created': len(processed_claims)
        }
        
        return validation_results
