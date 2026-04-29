# 🤖 The Causal Customer Retention Agent
*A submission for the **Google Cloud Rapid Agent Hackathon** on Devpost.*

**The Problem:** Traditional "AI" chatbots just answer questions. They don't take action, and they certainly don't understand the strict mathematical constraints of an enterprise budget. 
**The Solution:** An autonomous Agentic system powered by Gemini 1.5 Pro, Model Context Protocol (MCP), and True Causal AI (EconML) that actively saves high-value customers while proving its ROI mathematically.

---

## 🌟 Key Hackathon Integrations & Features

### 1. 🧠 Google Cloud Agent Builder & Gemini 1.5 Pro
- **Multimodal Voice RAG:** Instead of relying solely on text transcripts, the Agent natively ingests `.mp3` recordings of angry customer support calls using the **Google Generative AI File API**. Gemini 1.5 Pro natively listens to the audio to detect frustration, tone, and sarcasm to draft highly empathetic recovery emails.
- **The Agentic Boardroom:** Replacing simple Human-in-the-Loop constraints, we built a real-time multi-agent debate system. Three distinct Gemini personas (Customer Success, CFO, and Orchestrator) argue over budget allocations in real-time.

### 2. 🔌 Model Context Protocol (MCP) Server
- The entire system is architected around a robust **FastAPI MCP Server** (`api/server.py`).
- It exposes 15 specialized tools (e.g., `initiate_boardroom_debate`, `get_uplift`, `simulate_revenue`, `draft_email`) allowing the frontend UI or external orchestrators to trigger advanced operations dynamically.

### 3. 🎯 True Causal AI (Microsoft EconML)
- **Beyond Prediction:** We don't just predict *who* will churn. We use an **X-Learner** (trained with EconML and Random Forests) to calculate the precise Individual Treatment Effect (ITE) of a discount.
- **ROI Optimization:** This guarantees the Agent never wastes margin on "Sure Things" or triggers churn in "Sleeping Dogs."

### 4. ⚡ The Time Machine Simulator
- A live gamified Streamlit dashboard where judges can inject a "Macro-Economic Shock" (e.g., Competitor drops prices by 30%).
- The system instantly re-calculates the entire cohort's churn risk, triggers a **SciPy Sequential Least Squares Programming (SLSQP)** optimization to re-allocate a strict $5,000 budget, and autonomously drafts targeted recovery campaigns for the highest-LTV users.

---

## 🚀 Setup & Execution

### 1. Prerequisites
Ensure you have Python 3.10+ installed.

```bash
git clone https://github.com/Ibrahimboutal/TheCustomerRetentionAgent.git
cd TheCustomerRetentionAgent
pip install -r requirements.txt
```

### 2. Set API Key
Export your Gemini API Key:
```bash
export GOOGLE_API_KEY="your_api_key_here"
```

### 3. Initialize the Analytical Core & Audio RAG
Generate the SQLite database, train the ML models, and generate the synthetic `.mp3` support calls for the Voice RAG module:
```bash
python data/crm_init.py
python ml/train_model.py
python ml/train_uplift.py
python data/generate_audio_logs.py
```

### 4. Launch the System
You need two terminal windows to run the MCP Server and the UI Dashboard simultaneously.

**Terminal 1 (The MCP API Server):**
```bash
uvicorn api.server:app --port 8000
```

**Terminal 2 (The Streamlit Control Center):**
```bash
streamlit run ui/app.py
```

---

## 🏆 Hackathon Judging Criteria Met

- **Technological Implementation:** Complex orchestration of FastAPI, Streamlit, SciPy SLSQP optimization, EconML X-Learners, and Gemini 1.5 Pro multimodal audio RAG.
- **Design:** A premium, dark-mode, neon-styled Streamlit UI that acts as an enterprise control center, making complex math highly visual and actionable.
- **Quality of the Idea:** Moving agents from simple "chat wrappers" to constrained, mathematically rigorous, business-driving engines.

## License
This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
