import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import pickle
import os

def generate_eda():
    # 1. Load Data
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    data_path = os.path.join(BASE_DIR, 'churn_training_data.csv')
    
    if not os.path.exists(data_path):
        print(f"No training data found at {data_path}. Run generate_training_data.py first.")
        return
        
    df = pd.read_csv(data_path)
    
    plt.figure(figsize=(10, 6))
    sns.countplot(x='churned', data=df, palette='viridis')
    plt.title('Churn Distribution (Target Variable)')
    plt.savefig(os.path.join(BASE_DIR, 'churn_distribution.png'))
    
    # 3. Correlation Matrix
    plt.figure(figsize=(12, 8))
    sns.heatmap(df.corr(), annot=True, cmap='coolwarm', fmt='.2f')
    plt.title('Feature Correlation Matrix')
    plt.savefig(os.path.join(BASE_DIR, 'correlation_matrix.png'))
    
    # 4. Feature Importance (from the saved model)
    model_path = os.path.join(BASE_DIR, 'churn_model.pkl')
    features_path = os.path.join(BASE_DIR, 'feature_names.pkl')
    
    if os.path.exists(model_path) and os.path.exists(features_path):
        with open(model_path, 'rb') as f:
            model = pickle.load(f)
        with open(features_path, 'rb') as f:
            features = pickle.load(f)
            
        importances = pd.DataFrame({
            'Feature': features,
            'Importance': model.feature_importances_
        }).sort_values(by='Importance', ascending=False)
        
        plt.figure(figsize=(10, 6))
        sns.barplot(x='Importance', y='Feature', data=importances, palette='magma')
        plt.title('ML Model: Feature Importance for Churn Prediction')
        plt.savefig(os.path.join(BASE_DIR, 'feature_importance.png'))
        
    print(f"EDA Report Generated at {BASE_DIR}")

if __name__ == "__main__":
    generate_eda()
