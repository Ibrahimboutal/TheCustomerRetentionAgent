import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os

def generate_eda():
    # 1. Load Data
    if not os.path.exists('churn_training_data.csv'):
        print("No training data found. Run generate_training_data.py first.")
        return
        
    df = pd.read_csv('churn_training_data.csv')
    
    # 2. Churn Distribution
    plt.figure(figsize=(10, 6))
    sns.countplot(x='churned', data=df, palette='viridis')
    plt.title('Churn Distribution (Target Variable)')
    plt.savefig('churn_distribution.png')
    
    # 3. Correlation Matrix
    plt.figure(figsize=(12, 8))
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt='.2f')
    plt.title('Feature Correlation Matrix')
    plt.savefig('correlation_matrix.png')
    
    # 4. Feature Importance (from the saved model)
    if os.path.exists('churn_model.pkl') and os.path.exists('feature_names.pkl'):
        with open('churn_model.pkl', 'rb') as f:
            model = pickle.load(f)
        with open('feature_names.pkl', 'rb') as f:
            features = pickle.load(f)
            
        importances = pd.DataFrame({
            'Feature': features,
            'Importance': model.feature_importances_
        }).sort_values(by='Importance', ascending=False)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Importance', y='Feature', data=importances, palette='magma')
        plt.title('ML Model: Feature Importance for Churn Prediction')
        plt.savefig('feature_importance.png')
        
    print("EDA Report Generated: churn_distribution.png, correlation_matrix.png, feature_importance.png")

if __name__ == "__main__":
    generate_eda()
