# ML Model Performance Report (Real Telco Data)

**ROC-AUC Score:** 0.8278

### Classification Metrics
```
              precision    recall  f1-score   support

           0       0.83      0.91      0.87      1033
           1       0.66      0.49      0.56       374

    accuracy                           0.80      1407
   macro avg       0.75      0.70      0.72      1407
weighted avg       0.79      0.80      0.79      1407
```

### Technical Notes
- **Features:** tenure, MonthlyCharges, TotalCharges, Contract Type, Internet Service, etc.
- **Preprocessing:** Label Encoding for categoricals, StandardScaler for continuous variables.
- **Algorithm:** RandomForestClassifier (n_estimators=100, max_depth=10).
- **Inference:** Production-ready pkl files saved in `/ml`.
