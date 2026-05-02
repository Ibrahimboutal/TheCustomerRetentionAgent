# 🤖 The Causal Retention War Room
### *Google Cloud Rapid Agent Hackathon — Devpost Submission*

> **An autonomous multi-agent system that doesn't just chat — it reasons, debates, optimises, and acts to save customers before they churn.**

[![MIT License](https://img.shields.io/badge/License-MIT-cyan.svg)](LICENSE)
[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://python.org)
[![Gemini 2.0 Flash](https://img.shields.io/badge/Gemini-2.0%20Flash-purple.svg)](https://ai.google.dev)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.57-red.svg)](https://streamlit.io)
[![FastAPI](https://img.shields.io/badge/FastAPI-MCP%20Server-green.svg)](https://fastapi.tiangolo.com)

---

## 🎯 The Problem

Every business loses customers. But most retention tools only **describe** the problem — "17% of customers are at risk." They never **act** on it. Teams are left manually reviewing spreadsheets, guessing at discounts, and writing emails one by one.

**The cost?** Customer churn costs US businesses over **$1.6 trillion per year.** The solution isn't a better dashboard. It's an agent that can reason, decide, and intervene — autonomously.

---

## 💡 The Solution

**The Causal Retention War Room** is a fully autonomous multi-agent system that:

1. **Scores** every customer with a calibrated ML churn model (Random Forest)
2. **Debates** each high-risk case in a real boardroom simulation: Customer Success vs CFO, arbitrated by an Executive Orchestrator — all powered by **Gemini 2.0 Flash**
3. **Optimises** the retention budget using **SciPy SLSQP** constrained non-linear optimisation — proven mathematically superior to naive equal-allocation
4. **Acts** — generates personalised discount codes, flags VIP customers, drafts empathy emails — all via tool calls through the **MCP server**
5. **Explains** which features drive each individual's churn risk, making AI decisions transparent and auditable

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STREAMLIT WAR ROOM UI                        │
│         (Segmentation · Customers · Cohort · Optimizer          │
│          KPI Simulator · Agent Debate · Priority Queue)         │
└──────────────────────┬──────────────────────────────────────────┘
                       │ HTTP / JSON-RPC 2.0
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│               FASTAPI  MCP  SERVER  (port 8000)                 │
│                                                                 │
│  Tools exposed via MCP protocol:                                │
│  • get_customers          • segment_customers                   │
│  • generate_discount      • flag_vip                           │
│  • initiate_boardroom_debate                                    │
│  • draft_empathy_email    • trigger_macro_optimization          │
└───────┬────────────────────┬────────────────────────────────────┘
        │                    │
        ▼                    ▼
┌───────────────┐   ┌────────────────────────────────────────────┐
│  SQLITE / CRM │   │         AGENT ORCHESTRATION LAYER          │
│  DATABASE     │   │                                            │
│               │   │  ┌─────────────┐   ┌──────────────────┐   │
│  50 customers │   │  │ Boardroom   │   │ Decision Engine  │   │
│  + agent logs │   │  │ Debate      │   │ (SciPy SLSQP)    │   │
│               │   │  │             │   │                  │   │
│  (Supabase    │   │  │ CS Agent ↔  │   │ Maximize:        │   │
│   if creds    │   │  │ CFO Agent   │   │ Σ P·LTV·Uplift   │   │
│   provided)   │   │  │     ↓       │   │ s.t. Σd·LTV≤B    │   │
│               │   │  │ Orchestrator│   │                  │   │
└───────────────┘   │  └──────┬──────┘   └──────────────────┘   │
                    │         │                                   │
                    │         ▼                                   │
                    │  ┌─────────────────────────────────────┐   │
                    │  │     GEMINI 2.0 FLASH  (google.genai) │   │
                    │  │  • Multi-persona debate generation  │   │
                    │  │  • Empathy email drafting           │   │
                    │  │  • Falls back to deterministic sim  │   │
                    │  └─────────────────────────────────────┘   │
                    └────────────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   ML SCORING ENGINE  │
                    │   Random Forest      │
                    │   + EconML X-Learner │
                    │   Feature Importances│
                    │   Uplift: 1−e^{-10d} │
                    └──────────────────────┘
```

---

## ✨ Key Features

### 🤖 Multi-Agent Boardroom Debate (Gemini 2.0 Flash)
Three AI personas argue over every at-risk customer:
- **Customer Success Agent** — advocates for maximum retention spend
- **CFO Agent** — challenges ROI, argues against margin erosion
- **Executive Orchestrator** — synthesises both views into a final discount decision

Each debate is grounded in real ML risk scores, LTV, contract data, and the causal uplift function.

### ⚡ MCP Server — Agent "Superpowers"
A FastAPI server exposing 7 tools via the MCP JSON-RPC protocol:

| Tool | What it does |
|------|--------------|
| `get_customers` | Fetches and filters CRM records |
| `segment_customers` | Runs ML scoring, updates segments |
| `generate_discount` | Creates personalised discount codes in DB |
| `flag_vip` | Elevates customer to VIP status |
| `initiate_boardroom_debate` | Runs the Gemini multi-agent debate |
| `draft_empathy_email` | Writes personalised retention emails |
| `trigger_macro_optimization` | Runs SLSQP budget optimisation |

### 📐 Mathematical Optimisation (SciPy SLSQP)
Real constrained non-linear programming — not "smart rules":
```
Maximise:  Σᵢ ( Pᵢ · LTVᵢ · (1 − e^{−10·dᵢ}) )
Subject to: Σᵢ ( dᵢ · LTVᵢ ) ≤ Budget
Bounds:     0 ≤ dᵢ ≤ 0.30
```
The Strategy Comparison panel proves SLSQP outperforms naive equal allocation by quantifying the exact revenue gain.

### 🔬 Causal AI — Per-Customer Churn Drivers
The dashboard shows which features (contract type, tenure, internet service, payment method) contribute most to each individual customer's churn risk — making the AI's decisions **explainable and auditable**.

### 📊 6-Tab War Room Dashboard
| Tab | Contents |
|-----|----------|
| Segmentation | Donut, bubble chart, histogram, revenue bar, risk-vs-revenue summary |
| Customers | Searchable table, churn driver chart, inline action buttons |
| Cohort Analysis | Tenure buckets, Contract×Internet heatmap, LTV vs At-Risk dual axis, payment method breakdown, feature correlations |
| Budget Optimizer | SLSQP allocation, naive vs SLSQP waterfall comparison, ROI scatter |
| KPI Simulator | Sensitivity analysis, A/B strategy test simulation |
| Agent Debate | Live boardroom debate, email drafting, action log |

### 🚨 Priority Queue (Sidebar)
Top 5 customers ranked by **expected revenue loss** (churn probability × LTV) with one-click Discount and VIP action buttons — so the highest-impact interventions are always one click away.

---

## 🛠️ Tech Stack

| Component | Technology | Role |
|-----------|-----------|------|
| **Agent Brain** | Gemini 2.0 Flash via `google-genai` | Multi-agent debate, email generation |
| **MCP Server** | FastAPI + Uvicorn | Exposes 7 agent tools over JSON-RPC |
| **ML Scoring** | scikit-learn Random Forest | Churn probability prediction |
| **Causal AI** | EconML X-Learner | Individual Treatment Effect estimation |
| **Optimisation** | SciPy SLSQP | Constrained budget allocation |
| **Dashboard** | Streamlit 1.57 + Plotly | War Room UI |
| **Database** | SQLite (local) / Supabase (cloud) | CRM + agent action log |
| **Deployment** | Docker + Cloud Run | `cloudbuild.yaml` included |

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- (Optional) A Gemini API key for live AI debates

### 1. Clone & Install

```bash
git clone https://github.com/Ibrahimboutal/TheCustomerRetentionAgent.git
cd TheCustomerRetentionAgent
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and add:
# GOOGLE_API_KEY=your_gemini_api_key   (optional — falls back to simulation)
# SUPABASE_URL=...                      (optional — falls back to SQLite)
# SUPABASE_KEY=...
```

### 3. Initialise the Database & Train Models

```bash
python data/crm_init.py
python ml/train_model.py
```

### 4. Launch (One Command)

```bash
bash start.sh
```

This starts:
- **FastAPI MCP Server** on `http://localhost:8000`
- **Streamlit War Room** on `http://localhost:5000`

The app auto-scores all customers on first load. No Gemini API key required — the system runs a deterministic simulation fallback so every feature works out of the box.

---

## 🏆 Judging Criteria — How This Project Delivers

### Technological Implementation
- Real MCP server with 7 distinct tools called via JSON-RPC by the UI
- Gemini 2.0 Flash orchestrating a 3-persona multi-agent debate with real data grounding
- Constrained non-linear mathematical optimisation (SLSQP) with provable improvement over baselines
- EconML causal uplift model for individual treatment effect estimation
- Random Forest ML pipeline with automated scoring and DB persistence

### Design
- Neon glassmorphism "War Room" aesthetic built in Streamlit with custom CSS
- 7-card metric bar, 6-tab navigation, Priority Queue sidebar
- Every chart is interactive (Plotly), every decision is one click from action
- Graceful degradation — all features work without any API keys set

### Potential Impact
- Customer churn costs US businesses $1.6 trillion/year
- The system targets the exact bottleneck: closing the gap between **insight** (someone might churn) and **action** (do something about it, now)
- The Priority Queue + action buttons mean a retention team of one can act on the 5 highest-risk accounts in under 60 seconds

### Quality of the Idea
- Moves beyond "AI chat assistant" into a real decision-making agent with mathematical constraints
- The multi-agent debate surface makes AI reasoning **visible** and **contestable** — CFO and CS personas representing real business tensions
- Strategy Comparison quantifies the financial value of optimisation vs gut instinct

---

## 📁 Project Structure

```
TheCustomerRetentionAgent/
├── api/
│   └── server.py          # FastAPI MCP server (7 tools)
├── agent/
│   ├── boardroom.py       # Multi-agent Gemini debate + simulation fallback
│   └── decision_engine.py # SciPy SLSQP optimisation engine
├── ui/
│   └── app.py             # Streamlit War Room dashboard
├── ml/
│   ├── train_model.py     # Random Forest churn model training
│   ├── train_uplift.py    # EconML X-Learner training
│   ├── churn_model.pkl    # Trained model artifact
│   └── encoders.pkl       # Label encoders
├── data/
│   ├── crm_init.py        # SQLite DB + 50 mock customers
│   └── mock_crm.db        # Local database
├── eval/                  # Evaluation scripts
├── Dockerfile             # Container definition
├── cloudbuild.yaml        # Google Cloud Run CI/CD
├── start.sh               # One-command launcher
├── requirements.txt       # Python dependencies
└── .env.example           # Environment variable template
```

---

## 📝 License

MIT License — see [LICENSE](LICENSE) for details.

---

*Built for the Google Cloud Rapid Agent Hackathon · May–June 2026*
