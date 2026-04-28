import pandas as pd
import numpy as np
import pickle
import os
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def train():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(BASE_DIR, 'telco_churn.csv')
    
    if not os.path.exists(data_path):
        print(f"Error: {data_path} not found.")
        return

    # 1. LOAD & CLEAN
    df = pd.read_csv(data_path)
    # TotalCharges is string, convert to float, handle errors
    df['TotalCharges'] = pd.to_numeric(df['TotalCharges'], errors='coerce')
    df = df.dropna()
    
    # 2. FEATURE ENGINEERING (Label Encoding for categories)
    le = LabelEncoder()
    # Categorical columns
    cat_cols = df.select_dtypes(include=['object']).columns.tolist()
    # Remove customerID and Churn (target)
    cat_cols.remove('customerID')
    cat_cols.remove('Churn')
    
    # Store encoders for later use
    encoders = {}
    for col in cat_cols:
        encoders[col] = LabelEncoder()
        df[col] = encoders[col].fit_transform(df[col])
        
    df['Churn'] = df['Churn'].apply(lambda x: 1 if x == 'Yes' else 0)
    
    # Define features
    features = ['tenure', 'MonthlyCharges', 'TotalCharges', 'SeniorCitizen'] + cat_cols
    X = df[features]
    y = df['Churn']
    
    # 3. SPLIT & SCALE
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # 4. TRAIN (Random Forest)
    model = RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # 5. EVALUATE
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    print("Classification Report (Real Data):")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_prob):.4f}")
    
    # 6. SAVE REPORT
    with open(os.path.join(BASE_DIR, 'model_performance_report.md'), 'w') as f:
        f.write("# ML Model Performance Report (Real Telco Data)\n\n")
        f.write(f"**ROC-AUC Score:** {roc_auc_score(y_test, y_prob):.4f}\n\n")
        f.write("### Classification Metrics\n")
        f.write("```\n")
        f.write(classification_report(y_test, y_pred))
        f.write("```\n")
        
    # 7. SAVE ARTIFACTS
    with open(os.path.join(BASE_DIR, 'churn_model.pkl'), 'wb') as f:
        pickle.dump(model, f)
    with open(os.path.join(BASE_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    with open(os.path.join(BASE_DIR, 'feature_names.pkl'), 'wb') as f:
        pickle.dump(features, f)
    with open(os.path.join(BASE_DIR, 'encoders.pkl'), 'wb') as f:
        pickle.dump(encoders, f)
        
    print(f"Production model and encoders saved to {BASE_DIR}")

if __name__ == "__main__":
    train()
