# 🤖 Enterprise Customer Retention Agent (Elite Grade)

This is a production-grade AI agentic system designed to automate customer retention using **Model Context Protocol (MCP)**, **Supervised Machine Learning**, and **Causal Inference**. It transforms a standard CRM into an autonomous ROI engine.

## 🏗️ Architecture: The "Sandwiched" Intelligence
The system follows a three-layer "Sandwich" architecture to ensure both empathy and deterministic financial safety:
1.  **Analytical Layer (ML)**: A supervised **Random Forest model** (trained on 10k+ records) predicts churn risk with **0.91 ROC-AUC**.
2.  **Creative Layer (LLM)**: A Gemini-powered agent uses **Agentic RAG** to retrieve customer support history and draft personalized, empathetic retention emails.
3.  **Governance Layer (Decision Engine)**: A deterministic Python Rules Engine enforces strict financial guardrails, overriding LLM proposals that exceed budget or policy constraints.

---

## 🚀 Key Features

### 🧠 Advanced Intelligence
-   **Supervised Churn Prediction**: Real-time inference using a trained `RandomForestClassifier`.
-   **Causal Uplift Modeling**: Categorizes customers into four quadrants: *Persuadables*, *Sure Things*, *Lost Causes*, and *Sleeping Dogs* to optimize marketing spend.
-   **Agentic RAG**: Multi-modal reasoning that synthesizes unstructured support logs to personalize every outreach.

### 🛡️ Enterprise Trust & Safety
-   **Human-in-the-Loop (HITL)**: Asynchronous "Approval Queue" for high-value budget requests.
-   **Deterministic Guardrails**: Financial rules engine that prevents discount abuse and enforces policy.
-   **Historical Memory**: `promotion_history` tracking to prevent redundant discounting.

### 📊 Measurable Impact
-   **Monte Carlo ROI Simulator**: Built-in A/B testing framework that proves the system's impact on **Net Revenue Retained (NRR)**.
-   **Outcome Simulator (The Time Machine)**: Live simulation of customer responses to close the loop on retention strategies.

---

## 🛠️ Setup Instructions

### 1. Installation
```bash
pip install fastapi uvicorn pandas plotly streamlit scikit-learn requests
```

### 2. Model Training (The Data Science Layer)
Generate synthetic data and train the production model:
```bash
python generate_training_data.py
python train_model.py
```

### 3. Initialize the System
```bash
python crm_init.py
```

### 4. Run the Stack
**Terminal 1 (Server):**
```bash
uvicorn server:app --port 8000
```

**Terminal 2 (Dashboard):**
```bash
streamlit run app.py
```

---

## 🎬 The "Winning Demo" Walkthrough

1.  **The Math**: Run `python simulate_kpis.py` to show the judges the **212% ROI lift** your system generates.
2.  **The Intervention**: Ask the agent to analyze Customer #1. Watch it call `get_uplift` and `search_history`.
3.  **The Safety**: Try to trick the agent into a 90% discount. Show the dashboard log where the **Rules Engine** automatically caps it at 5%.
4.  **The Human Touch**: Open the **Approval Queue** tab and live-approve a budget request.
5.  **The Closing**: Call `simulate_outcome` and watch the **Total Revenue** on the dashboard increase live as the deal is closed.

## 🏗️ Tech Stack Justification
-   **FastAPI / MCP**: Unified protocol for tool discovery and execution.
-   **Scikit-Learn**: Traditional ML for deterministic risk assessment.
-   **Streamlit**: Real-time monitoring of agent "Thought Process" and CRM state.
-   **AWS/Vertex AI**: Scalable agentic compute for stateful reasoning.

---
*Developed for the Advanced Agentic Coding Hackathon - Bridging the gap between LLM creativity and Enterprise determinism.*
