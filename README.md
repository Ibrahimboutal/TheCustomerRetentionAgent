# 🤖 Professional Customer Retention Agent (Enterprise Suite)

This is a production-grade AI system that bridges the gap between **Generative AI** and **Deterministic Machine Learning**. It automates customer retention by identifying churn risk, enforcing financial policies, and executing personalized recovery strategies.

## 🏗️ Professional Architecture
The project is structured into modular domains to reflect real-world engineering standards:

- **`/ml`**: The Data Science Pipeline (Synthetic Data → Training → EDA → Performance Reports).
- **`/agent`**: The Deterministic Decision Engine (Rules-based guardrails).
- **`/api`**: FastAPI-powered MCP server for tool orchestration.
- **`/data`**: Persistence layer (SQLite) and CRM initialization.
- **`/eval`**: ROI Simulations and Agent Evaluation suites.
- **`/ui`**: Premium Streamlit monitoring dashboard.

---

## 📊 ML Pipeline & Performance
The "Brain" of the system is a **Random Forest Classifier** trained on 10,000 behavioral records.
- **ROC-AUC Score:** 0.9171
- **Features:** Tenure, Support Tickets, Login Frequency, Payment Failures, Spend, Recency.
- **Deep Evaluation:** See `ml/model_performance_report.md` for full classification metrics and confusion matrices.

---

## 🛡️ Deterministic Decision Engine
Unlike simple "LLM-decides" agents, this system uses a **Sandwiched Logic** layer:
1. **The Model** predicts the risk (Probability).
2. **The Decision Engine** (`agent/decision_engine.py`) maps the risk to a financial strategy (Max Discount).
3. **The Agent** executes the strategy with personalized empathy (RAG).

---

## 📈 Proven Business Impact
We use **Monte Carlo Simulations** to prove the ROI of the agent before deployment.
- **Net Revenue Lift:** ~210% increase compared to baseline "Email Blasts".
- **Churn Reduction:** 12.0 percentage point absolute improvement.
- **Efficiency:** Prevents discount waste on "Sure Things" and avoids "Sleeping Dog" churn.

---

## 🚀 Setup & Execution

### 1. Installation
```bash
pip install fastapi uvicorn pandas plotly streamlit scikit-learn requests seaborn matplotlib
```

### 2. The Analytical Core
```bash
# Initialize data, train model, and run EDA
python data/crm_init.py
python ml/train_model.py
python ml/generate_eda_report.py
```

### 3. Running the System
**Terminal 1 (Server):**
```bash
uvicorn api.server:app --port 8000
```

**Terminal 2 (Dashboard):**
```bash
streamlit run ui/app.py
```

### 4. Evaluation
```bash
python eval/simulate_kpis.py
python eval/agent_eval.py
```

---
*Created for the Advanced Agentic Coding Hackathon - Engineering Trust in AI.*
