import pandas as pd
from datetime import datetime

class DecisionEngine:
    """
    🛡️ The Deterministic Decision Engine.
    Ensures every agent action follows strict financial and business rules.
    """
    
    @staticmethod
    def get_discount_strategy(churn_risk, ltv):
        """
        Determines the maximum allowed discount and provides a business justification.
        """
        # Rules:
        # - High risk (>70%) + High LTV (>1000) -> 20% max
        # - High risk (>70%) + Low LTV (<200) -> 10% max
        # - Low risk (<30%) -> 5% max (Keep margins high)
        # - Default -> 10%
        
        if churn_risk > 0.7:
            if ltv > 1000:
                max_rate = 0.20
                reason = "High Churn Risk for a VIP customer justifies the maximum retention budget."
            else:
                max_rate = 0.10
                reason = "High Churn Risk identified, but budget capped to preserve LTV/CAC ratio."
        elif churn_risk < 0.3:
            max_rate = 0.05
            reason = "Low Churn Risk detected. Suggesting a minimal discount to maintain profitability."
        else:
            max_rate = 0.10
            reason = "Standard retention strategy applied for moderate churn risk."
            
        return max_rate, reason

    @staticmethod
    def validate_action(customer_name, proposed_rate, churn_risk, ltv):
        """
        Validates the agent's proposal and applies the cap.
        """
        max_rate, reason = DecisionEngine.get_discount_strategy(churn_risk, ltv)
        final_rate = min(proposed_rate, max_rate)
        
        was_capped = final_rate < proposed_rate
        
        return {
            "customer": customer_name,
            "proposed_rate": f"{int(proposed_rate*100)}%",
            "approved_rate": f"{int(final_rate*100)}%",
            "was_capped": was_capped,
            "justification": reason,
            "churn_risk_score": f"{int(churn_risk*100)}%"
        }
