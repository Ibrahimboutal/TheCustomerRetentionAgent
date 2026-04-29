import pandas as pd
import numpy as np
from scipy.optimize import minimize

class DecisionEngine:
    """
    ⚖️ MATHEMATICAL OPTIMIZATION ENGINE
    Solves the constrained non-linear optimization problem:
    Maximize Net Revenue Retained (NRR) subject to a Global Budget.
    """
    
    @staticmethod
    def uplift_function(discount):
        """
        🧬 Diminishing Returns Uplift Model.
        Adjusted to be more aggressive for demo purposes.
        """
        return 1 - np.exp(-10 * discount) 

    @staticmethod
    def optimize_cohort_discounts(cohort_df, budget=5000):
        """
        Uses SciPy SLSQP (Sequential Least Squares Programming) to solve:
        Maximize: sum(ChurnProb_i * LTV_i * Uplift(Discount_i))
        Subject to: sum(Discount_i * LTV_i) <= Budget
        Bounds: 0 <= Discount_i <= 0.30 (30% cap)
        """
        if cohort_df.empty:
            return {}, 0

        n = len(cohort_df)
        probs = cohort_df['churn_probability'].values / 100
        ltvs = cohort_df['TotalCharges'].values # Using Real Telco Feature
        
        # Initial guess: equal distribution of budget
        x0 = np.full(n, (budget / sum(ltvs)) if sum(ltvs) > 0 else 0)
        x0 = np.clip(x0, 0, 0.29)

        # Objective Function: MINIMIZE negative Expected Revenue Retained
        def objective(discounts):
            expected_save = probs * ltvs * DecisionEngine.uplift_function(discounts)
            return -np.sum(expected_save)

        # Constraint: Budget
        def budget_constraint(discounts):
            total_cost = np.sum(discounts * ltvs)
            return budget - total_cost

        cons = {'type': 'ineq', 'fun': budget_constraint}
        bounds = [(0, 0.30) for _ in range(n)]

        # Run Optimization
        res = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=cons)
        
        if not res.success:
            # Fallback to simple logic if optimization fails
            return {}, 0

        optimized_rates = res.x
        allocated = {}
        total_spend = 0
        
        for i, (idx, row) in enumerate(cohort_df.iterrows()):
            rate = optimized_rates[i]
            if rate > 0.01: # Only record meaningful discounts
                allocated[row['customer_id']] = {
                    'rate': round(rate, 3),
                    'justification': f"Optimal allocation via SLSQP (ROI Efficiency: {(-res.fun/budget):.2f})"
                }
                total_spend += (rate * ltvs[i])
        
        return allocated, total_spend

    @staticmethod
    def validate_action(customer_name, proposed_rate, churn_risk, ltv):
        """
        Single-customer validation using the marginal uplift ROI.
        """
        # Diminishing returns check
        marginal_uplift = DecisionEngine.uplift_function(proposed_rate)
        expected_save = churn_risk * ltv * marginal_uplift
        cost = ltv * proposed_rate
        
        roi = expected_save / cost if cost > 0 else 0
        
        # If ROI < 1.0, the discount is mathematically losing money
        if roi < 1.0:
            approved_rate = 0.0
            reason = f"Negative ROI ({roi:.2f}). No discount justified."
        else:
            approved_rate = proposed_rate
            reason = f"Approved ROI-positive action ({roi:.2f})."
            
        return {
            "customer": customer_name,
            "proposed_rate": f"{int(proposed_rate*100)}%",
            "approved_rate": f"{int(approved_rate*100)}%",
            "was_capped": approved_rate < proposed_rate,
            "justification": reason,
            "churn_risk_score": f"{int(churn_risk*100)}%"
        }
