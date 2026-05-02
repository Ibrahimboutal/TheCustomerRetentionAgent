import pandas as pd
import numpy as np
from scipy.optimize import minimize

class DecisionEngine:
    """
    MATHEMATICAL OPTIMIZATION ENGINE
    Solves the constrained non-linear optimization problem:
    Maximize Net Revenue Retained (NRR) subject to a Global Budget.
    """

    @staticmethod
    def uplift_function(discount):
        """Diminishing returns uplift model."""
        return 1 - np.exp(-10 * discount)

    @staticmethod
    def optimize_cohort_discounts(cohort_df: pd.DataFrame, budget: float = 5000):
        """
        Uses SciPy SLSQP to solve:
        Maximize: sum(ChurnProb_i * LTV_i * Uplift(Discount_i))
        Subject to: sum(Discount_i * LTV_i) <= Budget
        Bounds: 0 <= Discount_i <= 0.30
        """
        if cohort_df.empty:
            return {}, 0

        df = cohort_df.copy()

        # Support both 'churn_probability' (0-100) and fractional forms
        if 'churn_probability' in df.columns:
            probs = df['churn_probability'].values
            if probs.max() > 1.0:
                probs = probs / 100.0
        elif 'churn_risk' in df.columns:
            probs = df['churn_risk'].values
        else:
            probs = np.full(len(df), 0.3)

        ltvs = df['TotalCharges'].values.astype(float)
        ltvs = np.where(ltvs <= 0, 1.0, ltvs)

        n = len(df)
        total_ltv = ltvs.sum()
        x0 = np.clip(np.full(n, budget / total_ltv if total_ltv > 0 else 0), 0, 0.29)

        def objective(discounts):
            return -np.sum(probs * ltvs * DecisionEngine.uplift_function(discounts))

        def budget_constraint(discounts):
            return budget - np.sum(discounts * ltvs)

        cons = {'type': 'ineq', 'fun': budget_constraint}
        bounds = [(0, 0.30)] * n

        res = minimize(objective, x0, method='SLSQP', bounds=bounds, constraints=cons,
                       options={'maxiter': 1000, 'ftol': 1e-9})

        optimized_rates = res.x if res.success else x0
        efficiency = (-res.fun / budget) if budget > 0 else 0

        allocated = {}
        total_spend = 0

        for i, (_, row) in enumerate(df.iterrows()):
            rate = optimized_rates[i]
            if rate > 0.005:
                c_id = row.get('customer_id', i)
                allocated[c_id] = {
                    'rate': round(float(rate), 4),
                    'discount_pct': round(float(rate) * 100, 1),
                    'expected_save': round(float(probs[i] * ltvs[i] * DecisionEngine.uplift_function(rate)), 2),
                    'cost': round(float(rate * ltvs[i]), 2),
                    'justification': f"SLSQP optimal (efficiency: {efficiency:.2f}x)"
                }
                total_spend += rate * ltvs[i]

        return allocated, round(total_spend, 2)

    @staticmethod
    def validate_action(customer_name, proposed_rate, churn_risk, ltv):
        """Single-customer ROI validation."""
        marginal_uplift = DecisionEngine.uplift_function(proposed_rate)
        expected_save = churn_risk * ltv * marginal_uplift
        cost = ltv * proposed_rate
        roi = expected_save / cost if cost > 0 else 0

        if roi < 1.0:
            approved_rate = 0.0
            reason = f"Negative ROI ({roi:.2f}). No discount justified."
        else:
            approved_rate = proposed_rate
            reason = f"Approved. ROI-positive action ({roi:.2f}x return)."

        return {
            "customer": customer_name,
            "proposed_rate": f"{int(proposed_rate * 100)}%",
            "approved_rate": f"{int(approved_rate * 100)}%",
            "was_capped": approved_rate < proposed_rate,
            "justification": reason,
            "churn_risk_score": f"{int(churn_risk * 100)}%",
            "roi": round(roi, 2)
        }
