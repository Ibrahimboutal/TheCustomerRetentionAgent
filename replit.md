# The Causal Retention War Room

## Project Overview
An autonomous multi-agent customer retention system built for the Google Cloud Rapid Agent Hackathon. It uses causal AI (Uplift modeling via EconML), Gemini 1.5 Pro, and a multi-agent debate system to calculate ROI-efficient discount budget allocation for customer retention.

## Architecture

### Frontend
- **Streamlit** dashboard at port 5000 (`ui/app.py`)
- "War Room" neon glassmorphism aesthetic
- Real-time auto-refresh (5s interval via `streamlit-autorefresh`)
- Shows: KPI metrics, customer segmentation, scatter plots, agent activity logs

### Backend (MCP Server)
- **FastAPI** JSON-RPC server at port 8000 (`api/server.py`)
- Model Context Protocol (MCP) tool server
- Tools: `get_customers`, `segment_customers`, `generate_discount`, `flag_vip`, `initiate_boardroom_debate`, `draft_empathy_email`, `trigger_macro_optimization`

### Agent System
- `agent/boardroom.py` — Multi-agent debate (Customer Success vs CFO vs Orchestrator) using Gemini 1.5 Pro
- `agent/decision_engine.py` — SciPy SLSQP optimization for cohort-level discount allocation
- `agent/reasoning_engine_wrapper.py` — Vertex AI Reasoning Engine integration

### ML
- `ml/churn_model.pkl` — Random Forest churn prediction model (scikit-learn)
- `ml/encoders.pkl` — Label encoders for categorical features
- `ml/train_model.py` — Training script (requires `telco_churn.csv` dataset)

### Data Layer (Priority order)
1. Supabase (cloud PostgreSQL) — if `SUPABASE_URL` and `SUPABASE_KEY` are set
2. BigQuery — if `GOOGLE_CLOUD_PROJECT` is set
3. Local SQLite (`data/mock_crm.db`) — fallback, auto-initialized with 50 mock customers

## Key Dependencies
- `streamlit` 1.57.0 — UI framework
- `fastapi` + `uvicorn` — API server
- `google-generativeai` — Gemini API
- `google-cloud-bigquery`, `google-cloud-aiplatform` — GCP services
- `supabase` — Cloud database client
- `econml` — Causal ML / Uplift modeling
- `scikit-learn` 1.6.x — ML (pinned for econml compatibility)
- `scipy` — Optimization (SLSQP)
- `pandas`, `plotly`, `seaborn`, `matplotlib` — Data & visualization

## Startup
`bash start.sh` — Launches FastAPI on localhost:8000 and Streamlit on 0.0.0.0:5000

## Environment Variables
See `.env.example`:
- `SUPABASE_URL` — Supabase project URL
- `SUPABASE_KEY` — Supabase service role key
- `GOOGLE_API_KEY` — Gemini API key
- `HACKATHON_API_KEY` — API authentication key

## Notes
- Without Supabase/GCP credentials, the app runs fully on local SQLite fallback
- The ML model (`churn_model.pkl`) was trained synthetically on the mock CRM data — replace with real Telco data training for production use
- scikit-learn is pinned to <1.7 for econml compatibility
