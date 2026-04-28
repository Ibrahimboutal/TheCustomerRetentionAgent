import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from api import server
from agent.decision_engine import DecisionEngine

class CausalRetentionSimulator:
    """
    🧬 CAUSAL INFERENCE SIMULATOR
    Quantifies the 'Average Treatment Effect' (ATE) across a cohort.
    """
    
    @staticmethod
    def run_simulation(n_customers=50):
        np.random.seed(42)
        
        # 1. Fetch real customer data (IBM Telco features)
        customers = server.get_customers()
        if not customers:
            print("Error: No customer data in DB.")
            return

        df = pd.DataFrame(customers)
        cohort = df.head(n_customers)
        
        # 2. RUN CONTROL SCENARIO (Status Quo)
        control_churn_count = 0
        for _, row in cohort.iterrows():
            prob = row['churn_probability'] / 100
            if np.random.rand() < prob:
                control_churn_count += 1
        
        # 3. RUN AGENT SCENARIO (Optimization)
        # We use the SciPy Decision Engine to allocate a budget of $500
        budget = 500
        allocations, total_cost = DecisionEngine.optimize_cohort_discounts(cohort, budget=budget)
        
        agent_churn_count = 0
        revenue_saved = 0
        
        for i, row in cohort.iterrows():
            base_prob = row['churn_probability'] / 100
            ltv = row['TotalCharges']
            
            # If agent applied a treatment
            treatment_rate = allocations.get(row['customer_id'], {}).get('rate', 0)
            
            # Calculate Uplift (Treatment Effect)
            uplift = DecisionEngine.uplift_function(treatment_rate)
            # New Probability = P(Churn | No Treatment) * (1 - Uplift)
            treatment_prob = base_prob * (1 - uplift)
            
            if np.random.rand() < treatment_prob:
                agent_churn_count += 1
            else:
                revenue_saved += ltv

        # 4. REPORT METRICS
        control_rate = (control_churn_count / n_customers) * 100
        agent_rate = (agent_churn_count / n_customers) * 100
        net_saved = revenue_saved - total_cost
        
        print("="*60)
        print("CAUSAL UPLIFT REPORT (SCIPY OPTIMIZED)")
        print("="*60)
        print(f"Cohort Size: {n_customers}")
        print(f"Budget Cap:  ${budget}")
        print(f"Total Spent: ${total_cost:,.2f}")
        print("-" * 60)
        print(f"CONTROL CHURN (Baseline): {control_rate:.1f}%")
        print(f"AGENT CHURN (Treated):   {agent_rate:.1f}%")
        print(f"UPLIFT (Absolute):        {control_rate - agent_rate:.1f} Ppt")
        print("-" * 60)
        if total_cost > 0:
            roi = (net_saved - (n_customers*ltv*(1-control_rate/100))) / total_cost
            print(f"ESTIMATED ROI: {roi:.2f}x")
        else:
            print("ESTIMATED ROI: N/A (No budget allocated due to low risk)")
        print("="*60)

        # Write to final report
        with open(os.path.join(os.path.dirname(__file__), 'retention_roi_report.md'), 'w') as f:
            f.write("# Causal Uplift Report\n\n")
            f.write(f"**Baseline Churn:** {control_rate:.1f}%\n")
            f.write(f"**Optimized Churn:** {agent_rate:.1f}%\n\n")
            f.write("### Mathematical Proof\n")
            f.write("- **Optimization:** Sequential Least Squares Programming (SLSQP).\n")
            f.write("- **Causal Model:** Treatment effect follows an exponential diminishing returns curve.\n")

if __name__ == "__main__":
    CausalRetentionSimulator.run_simulation()
