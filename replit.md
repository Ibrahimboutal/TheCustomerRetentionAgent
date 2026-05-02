# Retention War Room v2.0

## Project Overview
An autonomous multi-agent customer retention system built for the Google Cloud Rapid Agent Hackathon. Uses causal AI (Uplift modeling), Gemini, and multi-agent debate to calculate ROI-efficient discount budget allocation for customer retention.

## Architecture

### Frontend
- **Streamlit** dashboard at port 5000 (`ui/app.py`)
- "War Room" neon glassmorphism aesthetic
- Auto-refresh every 30s
- **5 tabs**: Segmentation, Customers, Budget Optimizer, KPI Simulator, Agent Debate

### Backend (MCP Server)
- **FastAPI** JSON-RPC server at port 8000 (`api/server.py`)
- Tools: `get_customers`, `segment_customers`, `generate_discount`, `flag_vip`, `initiate_boardroom_debate`, `draft_empathy_email`, `trigger_macro_optimization`

### Agent System
- `agent/boardroom.py` — Multi-agent debate (Customer Success vs CFO vs Orchestrator)
  - Uses `google.genai` (Gemini 2.0 Flash) when `GOOGLE_API_KEY` is set
  - Falls back to deterministic simulation when no key configured
- `agent/decision_engine.py` — SciPy SLSQP optimization for cohort budget allocation

### ML Pipeline
- `ml/churn_model.pkl` — Random Forest churn prediction model
- `ml/encoders.pkl` — Label encoders for categorical telco features
- Auto-scoring on app load: segments + churn_probability computed and persisted to SQLite

### Data Layer (Priority order)
1. Supabase — if `SUPABASE_URL` and `SUPABASE_KEY` are set
2. Local SQLite (`data/mock_crm.db`) — fallback, auto-initialized with 50 mock customers

## UI Features (v2.0)

### Segmentation Tab
- Donut chart by segment with color-coded breakdown
- Scatter plot: Spend vs Tenure, bubble size = LTV
- Churn risk histogram by segment
- Revenue by segment horizontal bar chart

### Customers Tab
- Search by name, filter by segment, sort by any metric
- Color-coded churn risk (red >60%, yellow >30%, green <30%)
- Customer detail expander with full profile view

### Budget Optimizer Tab
- Interactive budget slider + segment focus selector
- SciPy SLSQP optimization via MCP API (with local fallback)
- Discount allocation bar chart (top 20 customers)
- Cost vs Expected Revenue Saved scatter plot
- Uplift model diminishing returns curve

### KPI Simulator Tab
- Interactive sliders: discount %, targeting %, base churn, LTV, customer base
- Real-time net benefit and ROI calculations
- Discount sensitivity analysis chart (revenue vs cost vs net benefit)
- Segment-level impact breakdown table

### Agent Debate Tab
- Customer selector with ML risk profile shown inline
- Boardroom debate: AI (Gemini) or simulation fallback
- Retention email generation: AI or template fallback
- Historical agent action log from SQLite

## Startup
`bash start.sh` — Launches FastAPI on localhost:8000 and Streamlit on 0.0.0.0:5000

## Environment Variables (see `.env.example`)
- `SUPABASE_URL` / `SUPABASE_KEY` — Cloud database (optional, falls back to SQLite)
- `GOOGLE_API_KEY` — Gemini 2.0 Flash (optional, falls back to simulation)
- `HACKATHON_API_KEY` — API auth key

## Key Dependencies
- `streamlit` 1.57+ with `streamlit-autorefresh`
- `fastapi` + `uvicorn`
- `google-genai` (Gemini 2.0 Flash)
- `supabase`
- `econml` + `scikit-learn` 1.6.x (pinned for compatibility)
- `scipy` (SLSQP optimization)
- `pandas`, `plotly`, `numpy`, `python-dotenv`
