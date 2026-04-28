import pandas as pd
import numpy as np

class DecisionEngine:
    """
    ⚖️ CONSTRAINED OPTIMIZATION ENGINE
    Allocates limited retention budget to maximize Net Revenue Retained (NRR).
    """
    
    @staticmethod
    def get_uplift_estimate(discount_rate):
        """
        Estimated probability shift (Uplift) based on discount.
        In a real system, this would be a separate Causal Model (e.g. Uplift RF).
        Assumption: 20% discount reduces churn probability by 15% absolute.
        """
        return discount_rate * 0.75 # Linear approximation for demo

    @staticmethod
    def optimize_cohort_discounts(cohort_df, budget=5000):
        """
        Uses a Greedy Knapsack approach to allocate discounts.
        Maximizes: sum(ChurnProb * LTV * Uplift)
        Subject to: sum(Discount * LTV) <= Budget
        """
        if cohort_df.empty:
            return cohort_df

        # 1. Calculate ROI for different discount levels (5%, 10%, 20%)
        # ROI = (Expected Revenue Saved) / (Cost of Discount)
        # We'll calculate 'Expected Revenue Saved per Dollar Spent'
        
        results = []
        for _, customer in cohort_df.iterrows():
            prob = customer['churn_probability'] / 100
            ltv = customer['total_spend']
            
            for rate in [0.05, 0.10, 0.20]:
                saved_rev = prob * ltv * DecisionEngine.get_uplift_estimate(rate)
                cost = ltv * rate
                efficiency = saved_rev / cost if cost > 0 else 0
                
                results.append({
                    'customer_id': customer['customer_id'],
                    'name': customer['name'],
                    'rate': rate,
                    'cost': cost,
                    'expected_save': saved_rev,
                    'efficiency': efficiency
                })
        
        opt_df = pd.DataFrame(results)
        
        # 2. Greedy Selection: Sort by Efficiency (ROI)
        opt_df = opt_df.sort_values(by='efficiency', ascending=False)
        
        allocated = {}
        current_spend = 0
        
        for _, row in opt_df.iterrows():
            cid = row['customer_id']
            # If we haven't given this customer a discount yet and have budget
            if cid not in allocated and (current_spend + row['cost']) <= budget:
                allocated[cid] = {
                    'rate': row['rate'],
                    'justification': f"High ROI ({row['efficiency']:.2f}) - Optimizing for Budget."
                }
                current_spend += row['cost']
        
        return allocated, current_spend

    @staticmethod
    def validate_action(customer_name, proposed_rate, churn_risk, ltv, global_budget_rem=5000):
        """
        Fallback for single-customer validation if not running batch optimization.
        """
        # Calculate cost
        cost = ltv * proposed_rate
        
        # Heuristic Efficiency check
        uplift = DecisionEngine.get_uplift_estimate(proposed_rate)
        efficiency = (churn_risk * ltv * uplift) / cost if cost > 0 else 0
        
        # If ROI is too low (< 0.5), we cap it
        if efficiency < 0.5:
            approved_rate = 0.05
            reason = f"Low predicted ROI ({efficiency:.2f}). Capping discount to 5%."
        elif cost > global_budget_rem:
             approved_rate = 0.0
             reason = "Insufficient Global Budget."
        else:
            approved_rate = proposed_rate
            reason = f"Approved based on ROI efficiency ({efficiency:.2f})."
            
        return {
            "customer": customer_name,
            "proposed_rate": f"{int(proposed_rate*100)}%",
            "approved_rate": f"{int(approved_rate*100)}%",
            "was_capped": approved_rate < proposed_rate,
            "justification": reason,
            "churn_risk_score": f"{int(churn_risk*100)}%"
        }
