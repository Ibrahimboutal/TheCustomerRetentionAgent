import os
from typing import Dict, Any
from api import server
from agent.decision_engine import DecisionEngine

class RetentionReasoningEngine:
    """
    A Vertex AI Reasoning Engine compatible wrapper for the 
    Customer Retention Agent logic.
    """
    def __init__(self, project_id: str = None, location: str = "us-central1"):
        self.project_id = project_id or os.environ.get("GOOGLE_CLOUD_PROJECT")
        self.location = location

    def __call__(self, customer_id: int) -> Dict[str, Any]:
        """
        Executes the autonomous retention loop for a specific customer.
        This is the main entrypoint when deployed as a Reasoning Engine.
        """
        print(f"🚀 Reasoning Engine: Processing Customer #{customer_id}")
        
        # 1. Fetch Data (Supports BigQuery Fallback)
        customers = server.get_customers()
        customer_list = customers.get('customers', [])
        customer = next((c for c in customer_list if c['customer_id'] == customer_id), None)
        
        if not customer:
            return {"status": "error", "message": f"Customer {customer_id} not found."}

        risk_score = customer.get('churn_probability', 50.0) # Default if not segmentated

        # 2. Financial Decision Engine
        decision = DecisionEngine.validate_action(
            customer['name'], 
            0.20, 
            risk_score / 100, 
            customer.get('TotalCharges', 0)
        )

        # 3. Execution
        discount = server.generate_discount_code(
            customer_id, 
            float(decision['approved_rate'].replace('%', '')) / 100
        )

        # 4. Impact Simulation
        outcome = server.simulate_outcome(customer_id)

        return {
            "customer_name": customer['name'],
            "risk_score": f"{risk_score}%",
            "approved_strategy": decision['approved_rate'],
            "justification": decision['justification'],
            "promo_code": discount['code'],
            "predicted_roi": outcome['revenue_gain'],
            "status": "Success"
        }

# Example registration logic (for documentation/judges)
# remote_app = reasoning_engines.ReasoningEngine.create(
#     RetentionReasoningEngine(project_id=PROJECT_ID),
#     requirements=["google-cloud-aiplatform", "fastapi", ...]
# )
