# 🤖 The Causal Retention War Room
*A premium submission for the **Google Cloud Rapid Agent Hackathon** on Devpost.*

**The Problem:** Traditional "AI" chatbots are toys. They lack mathematical constraints, data grounding, and enterprise-grade deployment.
**The Solution:** An autonomous Agentic system powered by **Gemini 1.5 Pro**, **Vertex AI Reasoning Engine**, **BigQuery**, and **True Causal AI**.

---

## 🌟 Winning Integrations & Features

### 1. 🧠 Vertex AI Reasoning Engine & Gemini 1.5 Pro
- **Multi-Agent Boardroom:** We built a managed multi-agent debate system where Gemini personas (CFO vs. Customer Success) argue over retention budgets in real-time.
- **Reasoning Engine Ready:** The entire agent logic is wrapped in a Vertex AI Reasoning Engine compatible structure, allowing for managed runtime execution.
- **Multimodal Voice RAG:** Ingests `.mp3` recordings to detect frustration and sarcasm natively via Gemini 1.5 Pro.

### 2. ⚡ Enterprise Infrastructure (Google Cloud Native)
- **BigQuery Analytical Core:** Replaced local storage with BigQuery for massive scalability and "Enterprise Readiness."
- **Cloud Run Deployment:** Containerized and optimized for high-performance deployment via Google Cloud Run with automated CI/CD via `cloudbuild.yaml`.
- **Cloud Logging & Observability:** Integrated with Google Cloud Logging for real-time monitoring of agent tool calls.

### 3. 🎯 True Causal AI & Optimization
- **X-Learner Uplift Modeling:** Uses EconML to calculate the Individual Treatment Effect (ITE) of a discount, ensuring we never waste budget on "Sure Things."
- **SciPy SLSQP Optimization:** A hard mathematical layer that solves for the most ROI-efficient budget allocation across thousands of customers under a strict global constraint.

### 4. 🛡️ Enterprise Safety & Guardrails
- **Vertex AI Safety Filters:** Programmatic enforcement of safety settings (Harassment, Hate Speech, etc.) on all agent-generated outreach.
- **Financial Guardrails:** Non-negotiable ROI thresholds prevent the agent from making irrational business decisions.

### 5. 🕹️ The Time Machine Simulator (Premium UI)
- A neon-styled, Glassmorphism Streamlit "War Room" dashboard.
- Live "Agent Thought Stream" showing the real-time reasoning and debate of the AI agents.

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
