import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from econml.metalearners import XLearner
from sklearn.preprocessing import LabelEncoder, StandardScaler

def synthesize_uplift_data(df):
    """
    Since standard Telco dataset lacks a randomized Treatment (T) and 
    causal Outcome (Y), we synthesize them mathematically for demonstration.
    """
    df = df.copy()
    
    # Randomly assign Treatment (e.g., 50% got the retention discount)
    np.random.seed(42)
    df['T'] = np.random.binomial(1, 0.5, size=len(df))
    
    # Calculate synthetic Individual Treatment Effect (ITE) based on business logic
    # High positive ITE for short-tenure, month-to-month (Persuadables)
    # Zero ITE for long-tenure, contracted (Sure Things)
    # Negative ITE for high-spend new users (Sleeping Dogs)
    
    def calculate_true_ite(row):
        ite = 0.05 # Baseline small uplift
        if row['tenure'] < 12 and row['Contract'] == 'Month-to-month':
            ite = 0.25 # High causal uplift
        elif row['tenure'] > 24 and row['Contract'] != 'Month-to-month':
            ite = 0.00 # Sure Things
        elif row['MonthlyCharges'] > 80 and row['tenure'] < 6:
            ite = -0.15 # Sleeping dogs
        return ite

    df['True_ITE'] = df.apply(calculate_true_ite, axis=1)
    
    # Base probability of retention (inverse of Churn)
    # We use a simple heuristic to get base prob or use the actual Churn flag as baseline
    # If Churn is Yes (1), base retention is 0. If No (0), base retention is 1.
    base_retention = df['Churn'].apply(lambda x: 0 if x == 'Yes' else 1)
    
    # We add noise to make it realistic
    noise = np.random.normal(0, 0.05, size=len(df))
    
    # Final observed outcome probability
    prob_y = base_retention + (df['T'] * df['True_ITE']) + noise
    prob_y = np.clip(prob_y, 0, 1)
    
    # Sample actual binary outcome
    df['Y'] = np.random.binomial(1, prob_y)
    
    return df

def train_uplift():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(BASE_DIR, 'telco_churn.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    # 1. LOAD & SYNTHESIZE
    df = pd.read_csv(data_path)
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df = df.dropna()
    
    df = synthesize_uplift_data(df)
    
    # 2. FEATURE ENGINEERING
    # We use the same features as the original churn model
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    if 'customerID' in cat_cols: cat_cols.remove('customerID')
    if 'Churn' in cat_cols: cat_cols.remove('Churn')
    
    encoders = {}
    for col in cat_cols:
        encoders[col] = LabelEncoder()
        df[col] = encoders[col].fit_transform(df[col])
        
    features = ['tenure', 'MonthlyCharges', 'TotalCharges', 'SeniorCitizen'] + cat_cols
    X = df[features]
    T = df['T']
    Y = df['Y'] # Outcome: Retained (1) or Churned (0)
    
    # 3. SCALE
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    print("Training Causal X-Learner...")
    # 4. TRAIN X-LEARNER (from EconML)
    # X-Learner uses models for outcome and models for effect
    models = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    effect_models = RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42)
    propensity_model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    
    est = XLearner(
        models=models,
        propensity_model=propensity_model,
        cate_models=effect_models
    )
    
    est.fit(Y, T, X=X_scaled)
    print("X-Learner training complete.")
    
    # Evaluate synthetic accuracy just to verify it learned the ITE
    predicted_ite = est.effect(X_scaled)
    df['Predicted_ITE'] = predicted_ite
    print(f"Mean True ITE: {df['True_ITE'].mean():.4f}")
    print(f"Mean Predicted ITE: {df['Predicted_ITE'].mean():.4f}")
    
    # 5. SAVE ARTIFACTS
    with open(os.path.join(BASE_DIR, 'uplift_model.pkl'), 'wb') as f:
        pickle.dump(est, f)
    with open(os.path.join(BASE_DIR, 'uplift_scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    with open(os.path.join(BASE_DIR, 'uplift_features.pkl'), 'wb') as f:
        pickle.dump(features, f)
    with open(os.path.join(BASE_DIR, 'uplift_encoders.pkl'), 'wb') as f:
        pickle.dump(encoders, f)
        
    print(f"Causal uplift model saved to {BASE_DIR}/uplift_model.pkl")

if __name__ == "__main__":
    train_uplift()
