import pandas as pd
import numpy as np
import pickle
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report, roc_auc_score, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns

def train():
    # Load data
    import os
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    df = pd.read_csv(os.path.join(BASE_DIR, 'churn_training_data.csv'))
    
    X = df.drop('churned', axis=1)
    y = df['churned']
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Train
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train_scaled, y_train)
    
    # Evaluate
    y_pred = model.predict(X_test_scaled)
    y_prob = model.predict_proba(X_test_scaled)[:, 1]
    
    print("Classification Report:")
    print(classification_report(y_test, y_pred))
    print(f"ROC-AUC Score: {roc_auc_score(y_test, y_prob):.4f}")
    
    # 6. GENERATE CONFUSION MATRIX IMAGE
    cm = confusion_matrix(y_test, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
    plt.title('Confusion Matrix: Churn Prediction')
    plt.ylabel('Actual')
    plt.xlabel('Predicted')
    plt.savefig('confusion_matrix.png')
    
    # 7. GENERATE MARKDOWN REPORT
    with open(os.path.join(BASE_DIR, 'model_performance_report.md'), 'w') as f:
        f.write("# ML Model Performance Report\n\n")
        f.write(f"**ROC-AUC Score:** {roc_auc_score(y_test, y_prob):.4f}\n\n")
        f.write("### Classification Metrics\n")
        f.write("```\n")
        f.write(classification_report(y_test, y_pred))
        f.write("```\n\n")
        f.write("![Confusion Matrix](confusion_matrix.png)\n")

    # Save artifacts
    with open(os.path.join(BASE_DIR, 'churn_model.pkl'), 'wb') as f:
        pickle.dump(model, f)
    with open(os.path.join(BASE_DIR, 'scaler.pkl'), 'wb') as f:
        pickle.dump(scaler, f)
    
    # Save feature names for consistency
    with open(os.path.join(BASE_DIR, 'feature_names.pkl'), 'wb') as f:
        pickle.dump(list(X.columns), f)
        
    print(f"Model and scaler saved to {BASE_DIR}")

if __name__ == "__main__":
    train()
