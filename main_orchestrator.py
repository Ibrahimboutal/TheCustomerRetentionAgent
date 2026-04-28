import sys
import os
import json
from datetime import datetime

# Ensure project root is in path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from api import server
from agent.decision_engine import DecisionEngine

def run_retention_loop(customer_id):
    print("="*60)
    print(f"🚀 STARTING AUTONOMOUS RETENTION LOOP FOR CUSTOMER #{customer_id}")
    print("="*60)

    # 1. ANALYZE (Data Ingestion)
    print("[1/5] ANALYZING: Fetching customer data and running ML Inference...")
    customer = [c for c in server.get_customers() if c['customer_id'] == customer_id][0]
    risk_score = customer['churn_probability']
    print(f"      - Customer: {customer['name']}")
    print(f"      - ML Churn Probability: {risk_score}%")

    # 2. DECIDE (Deterministic Decision Engine)
    print("[2/5] DECIDING: Enforcing financial guardrails via Decision Engine...")
    # Assume the agent proposes a 20% discount
    decision = DecisionEngine.validate_action(
        customer['name'], 0.20, risk_score/100, customer['TotalCharges']
    )
    print(f"      - Strategy Approved: {decision['approved_rate']} Discount")
    print(f"      - Justification: {decision['justification']}")

    # 3. PERSONALIZE (Agentic RAG)
    print("[3/5] PERSONALIZING: Searching support history for empathy...")
    history = server.search_support_history(customer_id)
    history_note = "None found" if history['status'] == 'empty' else f"Found {len(history['data'])} logs"
    print(f"      - Context: {history_note}")
    
    # 4. ACT (Execution)
    print("[4/5] ACTING: Generating code and drafting outreach...")
    discount = server.generate_discount_code(customer_id, float(decision['approved_rate'].replace('%', ''))/100)
    print(f"      - Action: Generated {discount['code']}")
    
    # 5. SIMULATE (ROI Impact)
    print("[5/5] SIMULATING: Predicting the business outcome...")
    outcome = server.simulate_outcome(customer_id)
    print(f"      - Predicted Result: {outcome['result']}")
    print(f"      - Revenue Gained: {outcome['revenue_gain']}")
    
    print("\n" + "="*60)
    print("✅ RETENTION LOOP COMPLETE: Impact Recorded in CRM")
    print("="*60)

if __name__ == "__main__":
    # Run for Customer #1 (Linda Garcia)
    run_retention_loop(1)
