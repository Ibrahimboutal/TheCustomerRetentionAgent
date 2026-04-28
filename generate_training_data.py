import pandas as pd
import numpy as np
import os

def generate_data(n=10000):
    np.random.seed(42)
    
    # Features
    tenure_days = np.random.randint(30, 730, n)
    support_tickets_30d = np.random.poisson(0.5, n)
    login_frequency = np.random.randint(1, 30, n)
    payment_failures = np.random.choice([0, 1, 2], n, p=[0.8, 0.15, 0.05])
    total_spend = np.random.uniform(10, 5000, n)
    
    # Recency (simulated)
    recency = np.random.randint(1, 180, n)
    
    # Calculate churn probability based on features (The "Real" logic)
    # Higher recency, higher support tickets, higher payment failures -> higher churn
    logit = (
        0.05 * recency + 
        0.8 * support_tickets_30d + 
        2.0 * payment_failures - 
        0.1 * login_frequency - 
        0.001 * total_spend - 4.0
    )
    prob = 1 / (1 + np.exp(-logit))
    churned = (np.random.rand(n) < prob).astype(int)
    
    df = pd.DataFrame({
        'tenure_days': tenure_days,
        'support_tickets_30d': support_tickets_30d,
        'login_frequency': login_frequency,
        'payment_failures': payment_failures,
        'total_spend': total_spend,
        'recency': recency,
        'churned': churned
    })
    
    df.to_csv('churn_training_data.csv', index=False)
    print(f"Generated {n} rows of training data in churn_training_data.csv")

if __name__ == "__main__":
    generate_data()
