import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import time
import numpy as np
import json
import sqlite3
import pickle
import os
import sys
import warnings
import requests
import io
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")
ML_DIR  = os.path.join(BASE_DIR, "ml")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

MCP_URL = "http://127.0.0.1:8000/"

# ── Supabase ────────────────────────────────────────────────────────────────
@st.cache_resource
def get_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            from supabase import create_client
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None

supabase = get_supabase()

# ── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Retention War Room",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;600;700&display=swap');

  :root {
    --primary:  #00F5FF;
    --secondary:#7000FF;
    --accent:   #FF006E;
    --success:  #4DFF88;
    --warn:     #FFD700;
    --bg:       #050508;
    --card-bg:  rgba(15,15,25,0.85);
    --border:   rgba(0,245,255,0.15);
  }

  .stApp {
    background: radial-gradient(ellipse at 80% 0%, #0d0d2b 0%, #050508 60%);
    color:#FFF; font-family:'Inter',sans-serif;
  }
  .main-header {
    font-family:'Orbitron',sans-serif;
    background:linear-gradient(90deg,var(--primary),var(--secondary),var(--accent));
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    font-size:2.8rem; font-weight:900; text-transform:uppercase;
    letter-spacing:3px; margin-bottom:0; line-height:1.1;
  }
  .sub-header {
    color:#9D4EDD; font-size:.9rem; letter-spacing:2px;
    text-transform:uppercase; margin-top:4px;
  }
  .metric-card {
    background:var(--card-bg); border:1px solid var(--border);
    border-radius:16px; padding:18px 20px;
    backdrop-filter:blur(20px);
    box-shadow:0 8px 32px rgba(0,0,0,.6),inset 0 1px 0 rgba(255,255,255,.05);
    transition:all .3s ease; height:100%;
  }
  .metric-card:hover {
    border-color:var(--primary);
    box-shadow:0 0 24px rgba(0,245,255,.2),0 8px 32px rgba(0,0,0,.6);
    transform:translateY(-2px);
  }
  .metric-label { font-size:.72rem; color:#888; text-transform:uppercase; letter-spacing:1.5px; margin-bottom:6px; }
  .metric-value { font-family:'Orbitron',sans-serif; font-size:1.85rem; font-weight:700; line-height:1; }
  .metric-delta { font-size:.72rem; color:#4DFF88; margin-top:4px; }

  .thought-stream {
    background:rgba(0,0,0,.7); border-left:3px solid var(--primary);
    padding:14px 18px; border-radius:0 12px 12px 0;
    font-family:'Courier New',monospace; font-size:.82rem; color:#00FF41;
    margin-bottom:10px; box-shadow:inset 0 0 15px rgba(0,255,65,.05); line-height:1.6;
  }
  .agent-tag { color:var(--primary); font-weight:bold; text-transform:uppercase; }

  .risk-high { background:rgba(255,77,77,.2); border:1px solid #FF4D4D; color:#FF4D4D;
               padding:2px 10px; border-radius:20px; font-size:.75rem; font-weight:600; }
  .risk-med  { background:rgba(255,215,0,.15); border:1px solid #FFD700; color:#FFD700;
               padding:2px 10px; border-radius:20px; font-size:.75rem; font-weight:600; }
  .risk-low  { background:rgba(77,255,136,.15); border:1px solid #4DFF88; color:#4DFF88;
               padding:2px 10px; border-radius:20px; font-size:.75rem; font-weight:600; }

  .priority-card {
    background:rgba(255,77,77,.08); border:1px solid rgba(255,77,77,.3);
    border-radius:10px; padding:10px 12px; margin-bottom:8px;
  }
  .priority-name { font-weight:600; font-size:.85rem; color:#FFF; }
  .priority-risk { font-size:.78rem; color:#FF4D4D; }

  .stTabs [data-baseweb="tab-list"] { gap:6px; background:transparent; border-bottom:1px solid var(--border); }
  .stTabs [data-baseweb="tab"] {
    background:var(--card-bg); border-radius:10px 10px 0 0; color:#888;
    padding:0 18px; height:42px; border:1px solid var(--border); border-bottom:none;
    font-size:.82rem; font-weight:600; letter-spacing:.5px;
  }
  .stTabs [aria-selected="true"] {
    background:rgba(0,245,255,.08) !important;
    border-color:var(--primary) !important; color:var(--primary) !important;
  }
  .stButton > button {
    background:linear-gradient(135deg,var(--secondary),var(--primary));
    color:#fff; border:none; border-radius:8px;
    font-weight:600; letter-spacing:.5px; transition:all .3s ease;
  }
  .stButton > button:hover { transform:translateY(-1px); box-shadow:0 6px 20px rgba(0,245,255,.3); }
  .action-btn > button {
    background:rgba(0,245,255,.1) !important; border:1px solid var(--border) !important;
    color:var(--primary) !important; font-size:.8rem !important; padding:4px 12px !important;
  }
  .section-title {
    font-family:'Orbitron',sans-serif; font-size:.95rem; color:var(--primary);
    text-transform:uppercase; letter-spacing:2px; margin:16px 0 12px;
    padding-bottom:8px; border-bottom:1px solid var(--border);
  }
  .info-pill {
    display:inline-block; background:rgba(112,0,255,.2); border:1px solid rgba(112,0,255,.4);
    color:#C77DFF; padding:4px 12px; border-radius:20px; font-size:.78rem; margin:2px;
  }
  .compare-card {
    background:var(--card-bg); border:1px solid var(--border);
    border-radius:12px; padding:18px; text-align:center;
  }
  .compare-label { font-size:.75rem; color:#888; text-transform:uppercase; letter-spacing:1px; }
  .compare-val   { font-family:'Orbitron',sans-serif; font-size:1.6rem; font-weight:700; margin:8px 0 4px; }
  .compare-delta { font-size:.8rem; }
  [data-testid="stSidebar"] { background:rgba(5,5,15,.95) !important; border-right:1px solid var(--border); }
</style>
""", unsafe_allow_html=True)


# ── ML engine ───────────────────────────────────────────────────────────────
@st.cache_resource
def load_ml_models():
    try:
        with open(os.path.join(ML_DIR, 'churn_model.pkl'), 'rb') as f:
            model = pickle.load(f)
        with open(os.path.join(ML_DIR, 'encoders.pkl'), 'rb') as f:
            encoders = pickle.load(f)
        return model, encoders
    except Exception:
        return None, {}

CHURN_MODEL, ENCODERS = load_ml_models()
FEATURE_NAMES = ['gender','SeniorCitizen','Partner','Dependents','tenure',
                 'PhoneService','MultipleLines','InternetService','OnlineSecurity',
                 'OnlineBackup','DeviceProtection','TechSupport','StreamingTV',
                 'StreamingMovies','Contract','PaperlessBilling','PaymentMethod',
                 'MonthlyCharges']


def safe_encode(le, value):
    val = str(value).strip()
    if hasattr(le, 'classes_'):
        lower = [str(c).lower() for c in le.classes_]
        if val.lower() in lower:
            return le.transform([le.classes_[lower.index(val.lower())]])[0]
    return 0


def encode_row(row) -> np.ndarray:
    x = []
    for col in FEATURE_NAMES:
        if col in ENCODERS:
            x.append(float(safe_encode(ENCODERS[col], row.get(col, ''))))
        else:
            x.append(float(row.get(col, 0) or 0))
    return np.array(x)


def get_churn_drivers(row) -> pd.DataFrame:
    """Approximate per-customer feature contribution using model feature importances."""
    if CHURN_MODEL is None:
        return pd.DataFrame()
    try:
        importances = CHURN_MODEL.feature_importances_
        enc = encode_row(row)
        # Normalise encoded values to [0,1] range per feature
        contributions = []
        for i, fname in enumerate(FEATURE_NAMES):
            raw = enc[i]
            contrib = float(importances[i]) * abs(float(raw))
            display_val = row.get(fname, raw)
            contributions.append({'Feature': fname, 'Contribution': contrib,
                                   'Importance': float(importances[i]),
                                   'Value': str(display_val)[:20]})
        return (pd.DataFrame(contributions)
                .sort_values('Contribution', ascending=False)
                .head(8)
                .reset_index(drop=True))
    except Exception:
        return pd.DataFrame()


def score_and_segment(df: pd.DataFrame) -> pd.DataFrame:
    if CHURN_MODEL is None or df.empty:
        if 'churn_probability' not in df.columns:
            df['churn_probability'] = 0.0
        return df
    X = pd.DataFrame()
    for col in FEATURE_NAMES:
        if col in df.columns:
            if col in ENCODERS:
                X[col] = df[col].apply(lambda v: safe_encode(ENCODERS[col], v))
            else:
                X[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            X[col] = 0
    warnings.filterwarnings('ignore')
    probs = CHURN_MODEL.predict_proba(X.values)[:, 1]
    df = df.copy()
    df['churn_risk']        = probs
    df['churn_probability'] = (probs * 100).round(1)
    def classify(r):
        if r['churn_risk'] > 0.5:   return 'At Risk'
        if r['MonthlyCharges'] > 90: return 'Big Spender'
        if r['MonthlyCharges'] > 65: return 'Champion'
        return 'Loyal'
    df['segment'] = df.apply(classify, axis=1)
    return df


def persist_scores(df: pd.DataFrame):
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    cur  = conn.cursor()
    for _, row in df.iterrows():
        cur.execute("UPDATE customers SET segment=?, churn_probability=? WHERE customer_id=?",
                    (row.get('segment','Unassigned'),
                     float(row.get('churn_probability', 0)),
                     int(row['customer_id'])))
    conn.commit(); conn.close()


# ── MCP helper ───────────────────────────────────────────────────────────────
def mcp_call(tool: str, args: dict = {}, timeout: int = 15):
    res = requests.post(MCP_URL, json={
        "jsonrpc": "2.0", "method": "tools/call",
        "params": {"name": tool, "arguments": args}
    }, timeout=timeout).json()
    return json.loads(res['result']['content'][0]['text'])


# ── Data loading ─────────────────────────────────────────────────────────────
def load_data() -> pd.DataFrame:
    if supabase:
        try:
            res = supabase.table("customers").select("*").execute()
            df  = pd.DataFrame(res.data)
            if not df.empty:
                expected = ["customer_id","name","email","gender","SeniorCitizen",
                            "Partner","Dependents","tenure","PhoneService","MultipleLines",
                            "InternetService","OnlineSecurity","OnlineBackup","DeviceProtection",
                            "TechSupport","StreamingTV","StreamingMovies","Contract",
                            "PaperlessBilling","PaymentMethod","MonthlyCharges","TotalCharges",
                            "segment","vip_flag","discount_code","churn_probability"]
                mapping = {c.lower(): c for c in expected}
                df.columns = [mapping.get(c.lower(), c) for c in df.columns]
                return df
        except Exception:
            pass
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df   = pd.read_sql_query("SELECT * FROM customers", conn)
        conn.close()
        return df
    return pd.DataFrame()


def get_logs() -> pd.DataFrame:
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        try:
            df = pd.read_sql_query(
                "SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT 20", conn)
            conn.close(); return df
        except Exception:
            conn.close()
    return pd.DataFrame()


def write_log(tool: str, args_str: str, result: str):
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("INSERT INTO agent_logs VALUES (?,?,?,?)",
                     (datetime.now().isoformat(), tool, args_str, result))
        conn.commit(); conn.close()


# ── Chart constants ───────────────────────────────────────────────────────────
DARK = dict(
    paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(5,5,15,.4)',
    font_color="#C0C0C0", font_family="Inter",
    margin=dict(t=36, b=20, l=10, r=10),
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(255,255,255,.1)', borderwidth=1),
    xaxis=dict(gridcolor='rgba(255,255,255,.05)', zerolinecolor='rgba(255,255,255,.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,.05)', zerolinecolor='rgba(255,255,255,.1)')
)
SEG_COLOR = {
    'At Risk':'#FF4D4D', 'Champion':'#4DFF88',
    'Big Spender':'#FFD700', 'Loyal':'#00F5FF', 'Unassigned':'#888'
}
UPLIFT = lambda d: 1 - np.exp(-10 * d)


# ════════════════════════════════════════════════════════════════════════════
# HEADER
# ════════════════════════════════════════════════════════════════════════════
c_logo, c_title = st.columns([1, 9])
with c_logo:
    st.image("https://img.icons8.com/fluency/96/robot-3.png", width=70)
with c_title:
    st.markdown("<h1 class='main-header'>Retention War Room</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Causal AI · Multi-Agent Debate · SciPy Optimization</p>",
                unsafe_allow_html=True)

st_autorefresh(interval=30000, key="datarefresh")

# ── Load + auto-score ────────────────────────────────────────────────────────
raw_df = load_data()
if raw_df.empty:
    st.error("No data. Run `python data/crm_init.py` to initialise the database.")
    st.stop()

needs_scoring = (
    'segment' not in raw_df.columns
    or raw_df['segment'].isin(['Unassigned', None, '']).mean() > 0.5
    or raw_df.get('churn_probability', pd.Series([0])).max() == 0
)
if needs_scoring and CHURN_MODEL is not None:
    with st.spinner("Running ML scoring engine..."):
        raw_df = score_and_segment(raw_df)
        persist_scores(raw_df)
else:
    if 'churn_probability' not in raw_df.columns:
        raw_df['churn_probability'] = 0.0
    if 'churn_risk' not in raw_df.columns:
        raw_df['churn_risk'] = raw_df['churn_probability'] / 100.0

df = raw_df.copy()
for col in ['MonthlyCharges','TotalCharges','churn_probability','churn_risk']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
if 'vip_flag' not in df.columns:
    df['vip_flag'] = 0


# ════════════════════════════════════════════════════════════════════════════
# TOP METRICS  (7 cards)
# ════════════════════════════════════════════════════════════════════════════
at_risk      = len(df[df['segment'] == 'At Risk'])
champions    = len(df[df['segment'] == 'Champion'])
spenders     = len(df[df['segment'] == 'Big Spender'])
avg_churn    = df['churn_probability'].mean()
total_rev    = df['TotalCharges'].sum()
rev_at_risk  = df[df['segment'] == 'At Risk']['TotalCharges'].sum()
vip_count    = int(df['vip_flag'].sum())
discounted   = int(df['discount_code'].notna().sum()) if 'discount_code' in df.columns else 0

metrics = [
    ("Total Customers",   len(df),              "#00F5FF", ""),
    ("At Risk 🚨",         at_risk,              "#FF4D4D", f"{at_risk/max(len(df),1)*100:.0f}% of base"),
    ("Revenue at Risk 💸", f"${rev_at_risk:,.0f}","#FF6B6B", f"{at_risk} customers"),
    ("Champions 🏆",       champions,            "#4DFF88", "High value"),
    ("Big Spenders 💰",    spenders,             "#FFD700", f">${df[df['segment']=='Big Spender']['MonthlyCharges'].mean():.0f}/mo avg" if spenders else "—"),
    ("Avg Churn Risk",    f"{avg_churn:.1f}%",  "#C77DFF", "ML predicted"),
    ("Total Revenue",     f"${total_rev:,.0f}", "#00F5FF", f"{vip_count} VIP · {discounted} discounted"),
]
cols = st.columns(len(metrics))
for col, (label, val, color, delta) in zip(cols, metrics):
    with col:
        st.markdown(f"""
        <div class='metric-card'>
          <div class='metric-label'>{label}</div>
          <div class='metric-value' style='color:{color}'>{val}</div>
          <div class='metric-delta'>{delta}</div>
        </div>""", unsafe_allow_html=True)

st.write("")

# ════════════════════════════════════════════════════════════════════════════
# SYSTEM ARCHITECTURE PANEL  (collapsible — great for demo / judges)
# ════════════════════════════════════════════════════════════════════════════
with st.expander("🏗️ System Architecture — How the Agent Works", expanded=False):
    arch_l, arch_r = st.columns([3, 2])
    with arch_l:
        st.markdown("""
<div style='font-family:monospace;font-size:.78rem;color:#00F5FF;
            background:rgba(0,0,0,.5);border:1px solid rgba(0,245,255,.15);
            border-radius:12px;padding:18px 22px;line-height:1.8'>
<span style='color:#C77DFF;font-weight:bold'>STREAMLIT WAR ROOM UI  (port 5000)</span><br>
&nbsp;&nbsp;Segmentation · Customers · Cohort · Optimizer · Simulator · Debate<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│  HTTP JSON-RPC 2.0<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
<span style='color:#C77DFF;font-weight:bold'>FASTAPI MCP SERVER  (port 8000)</span><br>
&nbsp;&nbsp;get_customers · segment_customers · generate_discount · flag_vip<br>
&nbsp;&nbsp;initiate_boardroom_debate · draft_empathy_email · trigger_macro_optimization<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
<span style='color:#4DFF88;font-weight:bold'>BOARDROOM DEBATE</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;<span style='color:#FFD700;font-weight:bold'>DECISION ENGINE</span><br>
&nbsp;CS Agent  ↔  CFO Agent&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;SciPy SLSQP<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;↓  Orchestrator&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Maximize Σ P·LTV·Uplift<br>
<span style='color:#FF6B9D;font-weight:bold'>GEMINI 2.0 FLASH</span>&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;s.t. Σ d·LTV ≤ Budget<br>
&nbsp;(→ simulation fallback)&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;0 ≤ d ≤ 0.30<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
<span style='color:#C77DFF;font-weight:bold'>ML SCORING ENGINE</span><br>
&nbsp;Random Forest · EconML X-Learner<br>
&nbsp;Uplift: 1 − e^(−10·d) · Feature Importance Drivers<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;│<br>
&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;▼<br>
<span style='color:#00F5FF;font-weight:bold'>SQLITE / SUPABASE CRM  +  AGENT ACTION LOG</span>
</div>
""", unsafe_allow_html=True)

    with arch_r:
        st.markdown("""
<div style='background:rgba(0,0,0,.4);border:1px solid rgba(112,0,255,.25);
            border-radius:12px;padding:18px 20px;font-size:.82rem;line-height:2'>
<div style='color:#C77DFF;font-weight:bold;font-family:Orbitron;
            font-size:.85rem;margin-bottom:10px'>AGENT TOOLS (MCP)</div>

<span style='color:#00F5FF'>►</span> <b>generate_discount</b><br>
<span style='font-size:.74rem;color:#888'>Creates personalised discount code in CRM</span><br>

<span style='color:#00F5FF'>►</span> <b>flag_vip</b><br>
<span style='font-size:.74rem;color:#888'>Elevates customer tier, logs action</span><br>

<span style='color:#00F5FF'>►</span> <b>initiate_boardroom_debate</b><br>
<span style='font-size:.74rem;color:#888'>Runs 3-agent Gemini debate on one customer</span><br>

<span style='color:#00F5FF'>►</span> <b>draft_empathy_email</b><br>
<span style='font-size:.74rem;color:#888'>Writes personalised retention email</span><br>

<span style='color:#00F5FF'>►</span> <b>trigger_macro_optimization</b><br>
<span style='font-size:.74rem;color:#888'>SLSQP across all customers + budget</span><br>

<div style='margin-top:14px;padding-top:12px;border-top:1px solid rgba(255,255,255,.08);
            color:#4DFF88;font-size:.78rem'>
✅ All tools work without API keys<br>
✅ Gemini adds live AI reasoning<br>
✅ Every action logged to DB
</div>
</div>
""", unsafe_allow_html=True)

    # Mini agent flow chart
    flow_nodes = ['User selects<br>customer', 'MCP Server<br>receives call',
                  'Gemini debate<br>CS vs CFO', 'Orchestrator<br>decides discount',
                  'Action logged<br>to CRM DB']
    fig_flow = go.Figure()
    for i, node in enumerate(flow_nodes):
        clr = ['#7000FF','#00F5FF','#FF4D4D','#4DFF88','#FFD700'][i]
        fig_flow.add_trace(go.Scatter(
            x=[i], y=[0], mode='markers+text',
            marker=dict(size=52, color=clr, opacity=0.85,
                        line=dict(color='white', width=2)),
            text=[node], textposition='top center',
            textfont=dict(size=10, color='white'),
            showlegend=False
        ))
        if i < len(flow_nodes) - 1:
            fig_flow.add_annotation(x=i+0.5, y=0, text="→",
                                    font=dict(size=20, color='#888'),
                                    showarrow=False)
    DARK_FLOW = dict(
        paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(5,5,15,.4)',
        font_color="#C0C0C0", font_family="Inter",
        height=140,
        margin=dict(t=36, b=50, l=10, r=10),
        xaxis=dict(visible=False, gridcolor='rgba(255,255,255,.05)'),
        yaxis=dict(visible=False, gridcolor='rgba(255,255,255,.05)'),
        title='Multi-Agent Execution Flow',
        title_font_color='#C77DFF', title_font_family='Orbitron',
    )
    fig_flow.update_layout(**DARK_FLOW)
    st.plotly_chart(fig_flow, use_container_width=True)

# ════════════════════════════════════════════════════════════════════════════
# TABS
# ════════════════════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📊 Segmentation",
    "👥 Customers",
    "🔬 Cohort Analysis",
    "⚙️ Budget Optimizer",
    "📈 KPI Simulator",
    "🤖 Agent Debate",
])


# ═══ TAB 1 — SEGMENTATION ════════════════════════════════════════════════════
with tab1:
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        seg_counts = df['segment'].value_counts().reset_index()
        seg_counts.columns = ['segment','count']
        fig_pie = px.pie(seg_counts, names='segment', values='count',
                         title='Customer Segments',
                         color='segment', color_discrete_map=SEG_COLOR, hole=0.45)
        fig_pie.update_traces(textfont_size=13, pull=[0.05]*len(seg_counts))
        fig_pie.update_layout(**DARK, title_font_color='#00F5FF', title_font_family='Orbitron')
        st.plotly_chart(fig_pie, use_container_width=True)

    with r1c2:
        fig_sc = px.scatter(df, x='tenure', y='MonthlyCharges',
                            color='segment', color_discrete_map=SEG_COLOR,
                            size='TotalCharges', size_max=30, hover_name='name',
                            hover_data={'churn_probability':':.1f','tenure':True,'MonthlyCharges':':.2f'},
                            title='Spend vs Tenure (bubble = LTV)')
        fig_sc.update_layout(**DARK, title_font_color='#00F5FF', title_font_family='Orbitron')
        st.plotly_chart(fig_sc, use_container_width=True)

    r2c1, r2c2 = st.columns(2)

    with r2c1:
        fig_hist = px.histogram(df, x='churn_probability', nbins=20,
                                color='segment', color_discrete_map=SEG_COLOR,
                                title='Churn Risk Distribution',
                                labels={'churn_probability':'Churn Probability (%)'})
        fig_hist.update_layout(**DARK, title_font_color='#00F5FF',
                               title_font_family='Orbitron', bargap=0.05)
        st.plotly_chart(fig_hist, use_container_width=True)

    with r2c2:
        rev_seg = (df.groupby('segment')
                   .agg(Total_Revenue=('TotalCharges','sum'))
                   .reset_index()
                   .sort_values('Total_Revenue', ascending=True))
        fig_rev = go.Figure(go.Bar(
            x=rev_seg['Total_Revenue'], y=rev_seg['segment'], orientation='h',
            marker=dict(color=[SEG_COLOR.get(s,'#888') for s in rev_seg['segment']], opacity=0.85),
            text=[f"${v:,.0f}" for v in rev_seg['Total_Revenue']], textposition='auto'
        ))
        fig_rev.update_layout(**DARK, title='Revenue by Segment',
                              title_font_color='#00F5FF', title_font_family='Orbitron')
        st.plotly_chart(fig_rev, use_container_width=True)

    # Risk vs Revenue scatter by segment summary
    seg_summary = df.groupby('segment').agg(
        Avg_Churn=('churn_probability','mean'),
        Total_Rev=('TotalCharges','sum'),
        Count=('customer_id','count')
    ).reset_index()
    fig_bub = px.scatter(seg_summary, x='Avg_Churn', y='Total_Rev',
                         size='Count', color='segment', color_discrete_map=SEG_COLOR,
                         text='segment', size_max=60,
                         title='Risk vs Revenue — Segment Summary',
                         labels={'Avg_Churn':'Avg Churn Risk (%)','Total_Rev':'Total Revenue ($)'})
    fig_bub.update_traces(textposition='top center')
    fig_bub.update_layout(**DARK, title_font_color='#00F5FF',
                          title_font_family='Orbitron', height=320)
    st.plotly_chart(fig_bub, use_container_width=True)


# ═══ TAB 2 — CUSTOMERS ═══════════════════════════════════════════════════════
with tab2:
    st.markdown("<div class='section-title'>Customer Intelligence</div>", unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        search = st.text_input("Search by name", placeholder="e.g. Jennifer")
    with fc2:
        seg_filter = st.multiselect("Filter segment", options=df['segment'].unique().tolist(),
                                    default=df['segment'].unique().tolist())
    with fc3:
        sort_by = st.selectbox("Sort by", ["churn_probability","TotalCharges","MonthlyCharges","tenure"])

    filt = df[df['segment'].isin(seg_filter)]
    if search:
        filt = filt[filt['name'].str.contains(search, case=False, na=False)]
    filt = filt.sort_values(by=sort_by, ascending=False)

    display_cols = [c for c in ['customer_id','name','segment','churn_probability',
                                 'MonthlyCharges','TotalCharges','Contract',
                                 'tenure','vip_flag','discount_code'] if c in filt.columns]

    def risk_color(v):
        if v > 60:  return 'color:#FF4D4D;font-weight:bold'
        if v > 30:  return 'color:#FFD700'
        return 'color:#4DFF88'

    styled = (filt[display_cols].style
              .map(risk_color, subset=['churn_probability'])
              .background_gradient(subset=['MonthlyCharges'], cmap='Purples')
              .format({'TotalCharges':'${:,.2f}','MonthlyCharges':'${:,.2f}',
                       'churn_probability':'{:.1f}%'}))
    st.dataframe(styled, use_container_width=True, height=380)

    exp_l, exp_r = st.columns([3, 1])
    with exp_l:
        st.caption(f"Showing {len(filt)} of {len(df)} customers")
    with exp_r:
        csv_buf = io.StringIO()
        filt[display_cols].to_csv(csv_buf, index=False)
        st.download_button(
            label="⬇ Export CSV",
            data=csv_buf.getvalue(),
            file_name=f"retention_customers_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # ── Customer detail + actions ──────────────────────────────────────────
    with st.expander("🔍 Customer Detail & Actions", expanded=False):
        if filt.empty:
            st.info("No customers match filters.")
        else:
            detail_id = st.selectbox(
                "Select customer",
                filt['customer_id'].tolist(),
                format_func=lambda x: (
                    f"ID {x} — {filt[filt['customer_id']==x]['name'].values[0]}"
                ) if len(filt[filt['customer_id']==x]) > 0 else str(x)
            )
            row = df[df['customer_id'] == detail_id].iloc[0]
            churn_pct = float(row.get('churn_probability', 0))
            badge_cls  = "risk-high" if churn_pct > 60 else ("risk-med" if churn_pct > 30 else "risk-low")
            badge_lbl  = "HIGH RISK" if churn_pct > 60 else ("MEDIUM RISK" if churn_pct > 30 else "LOW RISK")

            d1, d2, d3, d4 = st.columns(4)
            with d1:
                st.markdown(f"**Name:** {row['name']}")
                st.markdown(f"**Segment:** {row.get('segment','—')}")
                st.markdown(f"<span class='{badge_cls}'>{badge_lbl} — {churn_pct:.1f}%</span>",
                            unsafe_allow_html=True)
            with d2:
                st.markdown(f"**Monthly:** ${float(row.get('MonthlyCharges',0)):,.2f}")
                st.markdown(f"**LTV:** ${float(row.get('TotalCharges',0)):,.2f}")
                st.markdown(f"**Tenure:** {int(row.get('tenure',0))} months")
            with d3:
                st.markdown(f"**Contract:** {row.get('Contract','—')}")
                st.markdown(f"**Internet:** {row.get('InternetService','—')}")
                st.markdown(f"**Payment:** {row.get('PaymentMethod','—')}")
            with d4:
                st.markdown(f"**VIP:** {'✅' if row.get('vip_flag',0) else '—'}")
                existing_code = row.get('discount_code') or '—'
                st.markdown(f"**Discount:** `{existing_code}`")
                st.markdown(f"**Gender:** {row.get('gender','—')}")

            st.markdown("---")
            st.markdown("**Quick Actions**")
            a1, a2, a3 = st.columns(3)

            with a1:
                if st.button("🎁 Generate Discount Code", key=f"disc_{detail_id}",
                             use_container_width=True):
                    with st.spinner("Generating..."):
                        try:
                            result = mcp_call("generate_discount", {"customer_id": int(detail_id)})
                            st.success(result.get('msg', 'Done'))
                            write_log("generate_discount", str(detail_id), result.get('msg',''))
                        except Exception as e:
                            st.error(f"Error: {e}")

            with a2:
                if st.button("⭐ Flag as VIP", key=f"vip_{detail_id}",
                             use_container_width=True):
                    with st.spinner("Flagging..."):
                        try:
                            result = mcp_call("flag_vip", {"customer_id": int(detail_id)})
                            st.success(result.get('msg', 'VIP status updated'))
                            write_log("flag_vip", str(detail_id), result.get('msg',''))
                        except Exception as e:
                            st.error(f"Error: {e}")

            with a3:
                if st.button("✉️ Draft Email", key=f"email_{detail_id}",
                             use_container_width=True):
                    with st.spinner("Drafting..."):
                        try:
                            result = mcp_call("draft_empathy_email",
                                             {"customer_id": int(detail_id), "tone": "empathetic"})
                            st.text_area("Email Draft", value=result.get('email_body',''), height=160)
                        except Exception as e:
                            st.error(f"Error: {e}")

            # ── Churn Risk Drivers ────────────────────────────────────────
            st.markdown("**Churn Risk Drivers** — feature contribution to this customer's score")
            drivers = get_churn_drivers(row)
            if not drivers.empty:
                fig_drivers = go.Figure(go.Bar(
                    x=drivers['Contribution'],
                    y=drivers['Feature'],
                    orientation='h',
                    text=drivers['Value'],
                    textposition='auto',
                    marker=dict(
                        color=drivers['Contribution'],
                        colorscale=[[0,'#00F5FF'],[0.5,'#7000FF'],[1,'#FF4D4D']],
                        showscale=False
                    )
                ))
                fig_drivers.update_layout(**DARK,
                                          title=f"Top Risk Drivers — {row['name']}",
                                          title_font_color='#FF4D4D',
                                          title_font_family='Orbitron',
                                          height=300, xaxis_title='Contribution Score')
                st.plotly_chart(fig_drivers, use_container_width=True)
            else:
                st.info("ML model not loaded — driver analysis unavailable.")


# ═══ TAB 3 — COHORT ANALYSIS ═════════════════════════════════════════════════
with tab3:
    st.markdown("<div class='section-title'>Cohort Analysis</div>", unsafe_allow_html=True)

    # Tenure buckets
    df['tenure_bucket'] = pd.cut(
        df['tenure'], bins=[0,12,24,48,72],
        labels=['0–12 mo','13–24 mo','25–48 mo','49+ mo']
    )

    ca1, ca2 = st.columns(2)

    with ca1:
        # Avg churn risk by tenure bucket
        cohort_churn = (df.groupby('tenure_bucket', observed=True)
                        .agg(Avg_Churn=('churn_probability','mean'),
                             Count=('customer_id','count'))
                        .reset_index())
        fig_tc = go.Figure(go.Bar(
            x=cohort_churn['tenure_bucket'].astype(str),
            y=cohort_churn['Avg_Churn'],
            text=[f"{v:.1f}%" for v in cohort_churn['Avg_Churn']],
            textposition='outside',
            marker=dict(
                color=cohort_churn['Avg_Churn'],
                colorscale=[[0,'#4DFF88'],[0.5,'#FFD700'],[1,'#FF4D4D']],
                showscale=False
            )
        ))
        fig_tc.update_layout(**DARK, title='Avg Churn Risk by Tenure',
                             title_font_color='#00F5FF', title_font_family='Orbitron',
                             xaxis_title='Tenure', yaxis_title='Churn Risk (%)', height=320)
        st.plotly_chart(fig_tc, use_container_width=True)

    with ca2:
        # Segment mix by contract type
        ct_seg = (df.groupby(['Contract','segment'])
                  .size().reset_index(name='count'))
        fig_ct = px.bar(ct_seg, x='Contract', y='count', color='segment',
                        color_discrete_map=SEG_COLOR, barmode='stack',
                        title='Segment Mix by Contract Type')
        fig_ct.update_layout(**DARK, title_font_color='#00F5FF',
                             title_font_family='Orbitron', height=320)
        st.plotly_chart(fig_ct, use_container_width=True)

    ca3, ca4 = st.columns(2)

    with ca3:
        # Heatmap: Contract × InternetService → avg churn risk
        heat_data = (df.groupby(['Contract','InternetService'])
                     ['churn_probability'].mean()
                     .reset_index()
                     .pivot(index='Contract', columns='InternetService',
                            values='churn_probability'))
        fig_heat = go.Figure(go.Heatmap(
            z=heat_data.values,
            x=heat_data.columns.tolist(),
            y=heat_data.index.tolist(),
            colorscale=[[0,'#050508'],[0.4,'#7000FF'],[0.7,'#FF6B6B'],[1,'#FF4D4D']],
            text=[[f"{v:.1f}%" for v in row_] for row_ in heat_data.values],
            texttemplate="%{text}",
            showscale=True,
            colorbar=dict(title='Churn %', tickfont=dict(color='#C0C0C0'))
        ))
        fig_heat.update_layout(**DARK,
                               title='Churn Risk Heatmap: Contract × Internet',
                               title_font_color='#00F5FF', title_font_family='Orbitron',
                               height=320)
        st.plotly_chart(fig_heat, use_container_width=True)

    with ca4:
        # Revenue survival by tenure bucket
        surv = (df.groupby('tenure_bucket', observed=True)
                .agg(Avg_LTV=('TotalCharges','mean'),
                     At_Risk_Pct=('churn_probability', lambda x: (x>50).mean()*100))
                .reset_index())
        fig_surv = go.Figure()
        fig_surv.add_trace(go.Bar(
            x=surv['tenure_bucket'].astype(str), y=surv['Avg_LTV'],
            name='Avg LTV ($)', marker_color='#00F5FF', opacity=0.7
        ))
        fig_surv.add_trace(go.Scatter(
            x=surv['tenure_bucket'].astype(str), y=surv['At_Risk_Pct'],
            name='% At Risk', yaxis='y2',
            mode='lines+markers', line=dict(color='#FF4D4D', width=3),
            marker=dict(size=8, symbol='diamond')
        ))
        DARK_DUAL = {k: v for k, v in DARK.items() if k not in ('yaxis',)}
        fig_surv.update_layout(
            **DARK_DUAL, title='LTV & At-Risk Rate by Tenure',
            title_font_color='#00F5FF', title_font_family='Orbitron', height=320,
            yaxis=dict(title='Avg LTV ($)', gridcolor='rgba(255,255,255,.05)'),
            yaxis2=dict(title='% At Risk', overlaying='y', side='right',
                        showgrid=False, ticksuffix='%')
        )
        st.plotly_chart(fig_surv, use_container_width=True)

    # ── Payment method breakdown ──────────────────────────────────────────
    st.markdown("<div class='section-title'>Payment & Billing Analysis</div>",
                unsafe_allow_html=True)
    pb1, pb2 = st.columns(2)

    with pb1:
        pay_churn = (df.groupby('PaymentMethod')
                     .agg(Avg_Churn=('churn_probability','mean'),
                          Count=('customer_id','count'))
                     .sort_values('Avg_Churn', ascending=True)
                     .reset_index())
        fig_pay = go.Figure(go.Bar(
            x=pay_churn['Avg_Churn'], y=pay_churn['PaymentMethod'],
            orientation='h', text=[f"{v:.1f}%" for v in pay_churn['Avg_Churn']],
            textposition='auto',
            marker=dict(color=pay_churn['Avg_Churn'],
                        colorscale=[[0,'#4DFF88'],[1,'#FF4D4D']], showscale=False)
        ))
        fig_pay.update_layout(**DARK, title='Avg Churn Risk by Payment Method',
                              title_font_color='#00F5FF', title_font_family='Orbitron',
                              height=280, xaxis_title='Churn Risk (%)')
        st.plotly_chart(fig_pay, use_container_width=True)

    with pb2:
        bill_seg = (df.groupby(['PaperlessBilling','segment'])
                    .size().reset_index(name='count'))
        fig_bill = px.bar(bill_seg, x='PaperlessBilling', y='count', color='segment',
                          color_discrete_map=SEG_COLOR, barmode='group',
                          title='Paperless Billing vs Segment')
        fig_bill.update_layout(**DARK, title_font_color='#00F5FF',
                               title_font_family='Orbitron', height=280)
        st.plotly_chart(fig_bill, use_container_width=True)

    # ── Feature correlation with churn ────────────────────────────────────
    st.markdown("<div class='section-title'>Feature Correlation with Churn Risk</div>",
                unsafe_allow_html=True)
    num_cols = ['tenure','MonthlyCharges','TotalCharges','SeniorCitizen']
    num_cols = [c for c in num_cols if c in df.columns]
    corr_vals = {c: float(df[c].corr(df['churn_probability'])) for c in num_cols}
    corr_df = pd.DataFrame({'Feature':list(corr_vals.keys()),
                            'Correlation':list(corr_vals.values())}).sort_values('Correlation')
    fig_corr = go.Figure(go.Bar(
        x=corr_df['Correlation'], y=corr_df['Feature'], orientation='h',
        marker=dict(
            color=corr_df['Correlation'],
            colorscale=[[0,'#FF4D4D'],[0.5,'#888'],[1,'#4DFF88']],
            showscale=False
        ),
        text=[f"{v:.3f}" for v in corr_df['Correlation']], textposition='auto'
    ))
    fig_corr.update_layout(**DARK, title='Pearson Correlation with Churn Probability',
                           title_font_color='#00F5FF', title_font_family='Orbitron',
                           xaxis_title='Correlation', height=250)
    st.plotly_chart(fig_corr, use_container_width=True)


# ═══ TAB 4 — BUDGET OPTIMIZER ════════════════════════════════════════════════
with tab4:
    st.markdown("<div class='section-title'>SciPy SLSQP Budget Optimizer</div>",
                unsafe_allow_html=True)
    st.markdown(
        "Maximize Σ( Pᵢ · LTVᵢ · Uplift(dᵢ) ) subject to Σ( dᵢ · LTVᵢ ) ≤ Budget, "
        "0 ≤ dᵢ ≤ 30%."
    )

    oc1, oc2, oc3 = st.columns([2, 1, 1])
    with oc1:
        budget = st.slider("Retention Budget ($)", 500, 20000, 5000, 250)
    with oc2:
        focus_seg = st.selectbox("Focus segment",
                                  ["All","At Risk","Champion","Big Spender","Loyal"])
    with oc3:
        st.write(""); st.write("")
        run_opt = st.button("▶ Run Optimization", use_container_width=True)

    cohort = df.copy() if focus_seg == "All" else df[df['segment'] == focus_seg].copy()

    if run_opt and not cohort.empty:
        with st.spinner("Running SciPy SLSQP..."):
            try:
                opt_data = mcp_call("trigger_macro_optimization",
                                    {"budget": float(budget)}, timeout=20)
                opt_data['status'] = 'success'
            except Exception:
                sys.path.insert(0, BASE_DIR)
                from agent.decision_engine import DecisionEngine
                allocated, total_spend = DecisionEngine.optimize_cohort_discounts(
                    cohort, budget=budget)
                opt_data = {
                    "status": "success",
                    "budget_used": total_spend,
                    "customers_optimized": len(allocated),
                    "avg_discount_pct": round(
                        np.mean([v['discount_pct'] for v in allocated.values()]), 1
                    ) if allocated else 0,
                    "allocations": {str(k): v for k, v in allocated.items()}
                }
            st.session_state['opt_result'] = opt_data
            st.session_state['opt_budget'] = budget
            st.session_state['opt_cohort'] = cohort.copy()

    opt_data   = st.session_state.get('opt_result', {})
    opt_cohort = st.session_state.get('opt_cohort', cohort)

    if opt_data.get('status') == 'success':
        km1, km2, km3, km4 = st.columns(4)
        with km1:
            st.metric("Budget Allocated",
                      f"${opt_data.get('budget_used',0):,.0f}",
                      f"of ${st.session_state.get('opt_budget',budget):,}")
        with km2:
            st.metric("Customers Optimized", opt_data.get('customers_optimized', 0))
        with km3:
            st.metric("Avg Discount", f"{opt_data.get('avg_discount_pct',0):.1f}%")
        with km4:
            util = opt_data.get('budget_used',1) / max(budget,1) * 100
            st.metric("Budget Utilization", f"{util:.0f}%")

        allocs = opt_data.get('allocations', {})
        if allocs:
            rows_ = []
            for c_id, info in allocs.items():
                cr = df[df['customer_id'] == int(c_id)]
                rows_.append({
                    'Customer':      cr['name'].values[0] if len(cr) else f"ID {c_id}",
                    'Segment':       cr['segment'].values[0] if len(cr) else '—',
                    'Discount (%)':  info.get('discount_pct', info.get('rate',0)*100),
                    'Cost ($)':      info.get('cost', 0),
                    'Expected Save ($)': info.get('expected_save', 0)
                })
            alloc_df = pd.DataFrame(rows_).sort_values('Discount (%)', ascending=False)

            ac1, ac2 = st.columns(2)
            with ac1:
                fig_a = px.bar(alloc_df.head(20), x='Discount (%)', y='Customer',
                               orientation='h', color='Segment',
                               color_discrete_map=SEG_COLOR,
                               title='Optimal Discount Allocation (Top 20)')
                fig_a.update_layout(**DARK, title_font_color='#00F5FF',
                                    title_font_family='Orbitron', height=400)
                st.plotly_chart(fig_a, use_container_width=True)
            with ac2:
                fig_roi = px.scatter(alloc_df, x='Cost ($)', y='Expected Save ($)',
                                     color='Segment', color_discrete_map=SEG_COLOR,
                                     size='Discount (%)', hover_name='Customer',
                                     title='Cost vs Expected Revenue Saved')
                mx = max(alloc_df['Cost ($)'].max(), alloc_df['Expected Save ($)'].max())
                fig_roi.add_shape(type='line', x0=0, y0=0, x1=mx, y1=mx,
                                  line=dict(color='#888', dash='dot'))
                fig_roi.update_layout(**DARK, title_font_color='#00F5FF',
                                      title_font_family='Orbitron', height=400)
                st.plotly_chart(fig_roi, use_container_width=True)

            with st.expander("Full Allocation Table"):
                st.dataframe(alloc_df.style.format(
                    {'Discount (%)':'{:.1f}%','Cost ($)':'${:,.2f}',
                     'Expected Save ($)':'${:,.2f}'}),
                    use_container_width=True)
                alloc_csv = io.StringIO()
                alloc_df.to_csv(alloc_csv, index=False)
                st.download_button(
                    label="⬇ Download Allocation Report (CSV)",
                    data=alloc_csv.getvalue(),
                    file_name=f"budget_allocation_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv"
                )

        # ── Strategy Comparison: Naive vs SLSQP ──────────────────────────
        st.markdown("<div class='section-title'>Strategy Comparison: Naive vs SLSQP</div>",
                    unsafe_allow_html=True)
        st.markdown("Compare giving everyone an equal discount against the optimizer's allocation.")

        if not opt_cohort.empty and allocs:
            probs_c = opt_cohort['churn_probability'].values / 100.0
            ltvs_c  = opt_cohort['TotalCharges'].values.astype(float)
            ltvs_c  = np.where(ltvs_c <= 0, 1.0, ltvs_c)
            n_c     = len(opt_cohort)

            # Naive: equal budget share per LTV unit
            used_budget = st.session_state.get('opt_budget', budget)
            naive_d     = min(used_budget / ltvs_c.sum() if ltvs_c.sum() > 0 else 0, 0.30)
            naive_exp   = float(np.sum(probs_c * ltvs_c * UPLIFT(naive_d)))
            naive_cost  = float(naive_d * ltvs_c.sum())
            naive_roi   = naive_exp / max(naive_cost, 1)

            # SLSQP result
            slsqp_exp   = sum(
                float(probs_c[i]) * float(ltvs_c[i]) * UPLIFT(alloc_df.iloc[i]['Discount (%)']/100)
                for i in range(min(n_c, len(alloc_df)))
            ) if not alloc_df.empty else 0
            slsqp_cost  = opt_data.get('budget_used', used_budget)
            slsqp_roi   = slsqp_exp / max(slsqp_cost, 1)

            improvement = ((slsqp_exp - naive_exp) / max(naive_exp, 1)) * 100

            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                st.markdown(f"""
                <div class='compare-card'>
                  <div class='compare-label'>Naive Equal Distribution</div>
                  <div class='compare-val' style='color:#888'>{naive_d*100:.1f}%</div>
                  <div style='font-size:.75rem;color:#888'>uniform discount</div>
                  <hr style='border-color:rgba(255,255,255,.1)'>
                  <div class='compare-label'>Expected Revenue Retained</div>
                  <div class='compare-val' style='color:#888'>${naive_exp:,.0f}</div>
                  <div class='compare-delta' style='color:#888'>ROI {naive_roi:.2f}x</div>
                </div>""", unsafe_allow_html=True)
            with sc2:
                arrow = "▲" if improvement > 0 else "▼"
                clr   = "#4DFF88" if improvement > 0 else "#FF4D4D"
                st.markdown(f"""
                <div class='compare-card' style='border-color:var(--primary)'>
                  <div class='compare-label' style='color:var(--primary)'>Improvement</div>
                  <div class='compare-val' style='color:{clr}'>{arrow} {abs(improvement):.1f}%</div>
                  <div class='compare-delta' style='color:{clr}'>more revenue retained</div>
                  <hr style='border-color:rgba(0,245,255,.2)'>
                  <div class='compare-label'>Extra Revenue</div>
                  <div class='compare-val' style='color:{clr};font-size:1.2rem'>
                    ${slsqp_exp - naive_exp:+,.0f}
                  </div>
                </div>""", unsafe_allow_html=True)
            with sc3:
                st.markdown(f"""
                <div class='compare-card'>
                  <div class='compare-label'>SLSQP Optimized</div>
                  <div class='compare-val' style='color:var(--primary)'>{opt_data.get('avg_discount_pct',0):.1f}%</div>
                  <div style='font-size:.75rem;color:#888'>avg optimal discount</div>
                  <hr style='border-color:rgba(255,255,255,.1)'>
                  <div class='compare-label'>Expected Revenue Retained</div>
                  <div class='compare-val' style='color:var(--primary)'>${slsqp_exp:,.0f}</div>
                  <div class='compare-delta'>ROI {slsqp_roi:.2f}x</div>
                </div>""", unsafe_allow_html=True)

            # Waterfall: naive → slsqp
            fig_wf = go.Figure(go.Waterfall(
                orientation='v',
                measure=['absolute','relative','total'],
                x=['Naive Strategy','SLSQP Gain','Optimized'],
                y=[naive_exp, slsqp_exp - naive_exp, 0],
                text=[f'${naive_exp:,.0f}', f'+${slsqp_exp-naive_exp:,.0f}', f'${slsqp_exp:,.0f}'],
                textposition='outside',
                connector=dict(line=dict(color='rgba(255,255,255,.2)')),
                increasing=dict(marker=dict(color='#4DFF88')),
                decreasing=dict(marker=dict(color='#FF4D4D')),
                totals=dict(marker=dict(color='#00F5FF'))
            ))
            fig_wf.update_layout(**DARK, title='Revenue Retained: Naive vs SLSQP',
                                 title_font_color='#00F5FF', title_font_family='Orbitron',
                                 yaxis_title='Expected Revenue ($)', height=300)
            st.plotly_chart(fig_wf, use_container_width=True)

    else:
        st.info("Set your budget and click **▶ Run Optimization** to compute allocations.")

    # Uplift curve (always visible)
    st.markdown("<div class='section-title'>Uplift Model — Diminishing Returns</div>",
                unsafe_allow_html=True)
    d_r = np.linspace(0, 0.30, 200)
    fig_u = go.Figure()
    fig_u.add_trace(go.Scatter(
        x=d_r*100, y=UPLIFT(d_r)*100, mode='lines', name='Retention Uplift',
        line=dict(color='#00F5FF', width=3), fill='tozeroy',
        fillcolor='rgba(0,245,255,.06)'
    ))
    # Mark the 10%, 15%, 20%, 25% points
    for mark_d in [10, 15, 20, 25]:
        u_val = UPLIFT(mark_d/100)*100
        fig_u.add_annotation(x=mark_d, y=u_val, text=f"{u_val:.0f}%",
                             showarrow=True, arrowhead=2, ax=20, ay=-30,
                             font=dict(color='#C77DFF', size=11))
    fig_u.update_layout(**DARK, title='Discount % → Retention Uplift  [ 1 - e^{-10d} ]',
                        title_font_color='#00F5FF', title_font_family='Orbitron',
                        xaxis_title='Discount (%)', yaxis_title='Uplift (%)', height=260)
    st.plotly_chart(fig_u, use_container_width=True)


# ═══ TAB 5 — KPI SIMULATOR ════════════════════════════════════════════════════
with tab5:
    st.markdown("<div class='section-title'>Retention Strategy Simulator</div>",
                unsafe_allow_html=True)
    st.markdown("Model the financial impact of different interventions before committing budget.")

    sc1, sc2 = st.columns([1, 2])
    with sc1:
        st.markdown("**Strategy Parameters**")
        discount_rate    = st.slider("Discount Offered (%)", 0, 30, 15)
        intervention_pct = st.slider("Customers Targeted (%)", 0, 100, 40)
        base_churn_rate  = st.slider("Base Churn Rate (%)", 1, 50, 25)
        avg_ltv_sim      = st.slider("Avg Customer LTV ($)", 500, 10000, int(df['TotalCharges'].mean()))
        total_cust_sim   = st.slider("Total Customer Base", 10, 5000, len(df))

    with sc2:
        uplift_val    = float(UPLIFT(discount_rate / 100))
        targeted      = int(total_cust_sim * intervention_pct / 100)
        at_risk_base  = int(total_cust_sim * base_churn_rate / 100)
        saves         = int(at_risk_base * intervention_pct / 100 * uplift_val)
        cost_sim      = targeted * avg_ltv_sim * discount_rate / 100
        rev_retained  = saves * avg_ltv_sim
        net_benefit   = rev_retained - cost_sim
        roi_ratio     = rev_retained / max(cost_sim, 1)

        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric("Customers Targeted", f"{targeted:,}")
        kc2.metric("Estimated Saves", f"{saves:,}",
                   delta=f"+{saves/max(at_risk_base,1)*100:.0f}% of at-risk")
        kc3.metric("Net Benefit", f"${net_benefit:,.0f}",
                   delta=f"ROI {roi_ratio:.1f}x",
                   delta_color="normal" if net_benefit > 0 else "inverse")
        kc4.metric("Uplift Achieved", f"{uplift_val*100:.1f}%")

        # Sensitivity chart
        discount_range = np.arange(0, 31)
        scen = []
        for d in discount_range:
            u = float(UPLIFT(d/100))
            t = int(total_cust_sim * intervention_pct / 100)
            s = int(at_risk_base * intervention_pct / 100 * u)
            c_ = t * avg_ltv_sim * d / 100
            r_ = s * avg_ltv_sim
            scen.append({'Discount (%)':d, 'Net Benefit':r_-c_,
                         'Revenue Retained':r_, 'Cost':c_})
        scen_df = pd.DataFrame(scen)

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(x=scen_df['Discount (%)'], y=scen_df['Revenue Retained'],
                                     name='Revenue Retained', line=dict(color='#4DFF88', width=2.5),
                                     fill='tozeroy', fillcolor='rgba(77,255,136,.04)'))
        fig_sim.add_trace(go.Scatter(x=scen_df['Discount (%)'], y=scen_df['Cost'],
                                     name='Intervention Cost', line=dict(color='#FF4D4D', width=2.5),
                                     fill='tozeroy', fillcolor='rgba(255,77,77,.04)'))
        fig_sim.add_trace(go.Scatter(x=scen_df['Discount (%)'], y=scen_df['Net Benefit'],
                                     name='Net Benefit', line=dict(color='#00F5FF', width=3, dash='dot')))
        fig_sim.add_vline(x=discount_rate, line_color='#7000FF', line_dash='dash',
                          annotation_text=f"Current: {discount_rate}%",
                          annotation_font_color='#C77DFF')
        fig_sim.update_layout(**DARK, title='Discount Rate Sensitivity',
                              title_font_color='#00F5FF', title_font_family='Orbitron',
                              xaxis_title='Discount (%)', yaxis_title='$ Value', height=340)
        st.plotly_chart(fig_sim, use_container_width=True)

    # ── A/B Test Simulation ───────────────────────────────────────────────
    st.markdown("<div class='section-title'>A/B Strategy Test Simulation</div>",
                unsafe_allow_html=True)
    ab1, ab2 = st.columns(2)
    with ab1:
        st.markdown("**Strategy A (Broad)**")
        a_disc   = st.slider("Discount A (%)", 0, 30, 10, key="a_disc")
        a_target = st.slider("Target A (%)", 0, 100, 80, key="a_tgt")
    with ab2:
        st.markdown("**Strategy B (Targeted)**")
        b_disc   = st.slider("Discount B (%)", 0, 30, 20, key="b_disc")
        b_target = st.slider("Target B (%)", 0, 100, 30, key="b_tgt")

    def sim_strategy(disc, tgt_pct, n, churn_pct, ltv):
        u   = float(UPLIFT(disc/100))
        t   = int(n * tgt_pct/100)
        s   = int(n * churn_pct/100 * tgt_pct/100 * u)
        c_  = t * ltv * disc/100
        r_  = s * ltv
        return t, s, c_, r_, r_-c_

    at_, as_, ac_, ar_, an_ = sim_strategy(
        a_disc, a_target, total_cust_sim, base_churn_rate, avg_ltv_sim)
    bt_, bs_, bc_, br_, bn_ = sim_strategy(
        b_disc, b_target, total_cust_sim, base_churn_rate, avg_ltv_sim)

    labels = ['Customers Targeted','Estimated Saves','Cost ($)','Revenue ($)','Net Benefit ($)']
    fig_ab = go.Figure()
    fig_ab.add_trace(go.Bar(name='Strategy A (Broad)',
                            x=labels,
                            y=[at_, as_, ac_, ar_, an_],
                            marker_color='#7000FF', opacity=0.85))
    fig_ab.add_trace(go.Bar(name='Strategy B (Targeted)',
                            x=labels,
                            y=[bt_, bs_, bc_, br_, bn_],
                            marker_color='#00F5FF', opacity=0.85))
    fig_ab.update_layout(**DARK, barmode='group', title='A/B Strategy Comparison',
                         title_font_color='#00F5FF', title_font_family='Orbitron', height=320)
    st.plotly_chart(fig_ab, use_container_width=True)

    winner = "A (Broad)" if an_ > bn_ else "B (Targeted)"
    diff   = abs(an_ - bn_)
    if an_ != bn_:
        st.success(f"**Strategy {winner}** yields ${diff:,.0f} more net benefit.")

    # Segment-level breakdown
    st.markdown("<div class='section-title'>Segment-Level Impact</div>", unsafe_allow_html=True)
    rows_seg = []
    for seg in df['segment'].unique():
        sg   = df[df['segment'] == seg]
        ac_s = sg['churn_probability'].mean() / 100
        ltv_s= sg['TotalCharges'].mean()
        u_s  = float(UPLIFT(discount_rate/100))
        sv_s = ac_s * u_s * len(sg)
        rows_seg.append({'Segment':seg, 'Count':len(sg),
                         'Avg Churn':f"{ac_s*100:.1f}%",
                         'Avg LTV':f"${ltv_s:,.0f}",
                         'Est. Saves':f"{sv_s:.1f}",
                         'Revenue Retained':f"${sv_s*ltv_s:,.0f}"})
    st.dataframe(pd.DataFrame(rows_seg), use_container_width=True)


# ═══ TAB 6 — AGENT DEBATE ════════════════════════════════════════════════════
with tab6:
    st.markdown("<div class='section-title'>Autonomous Boardroom Debate</div>",
                unsafe_allow_html=True)

    if not GOOGLE_API_KEY:
        st.info("**Simulation Mode** — add `GOOGLE_API_KEY` to enable live Gemini debates.",
                icon="ℹ️")

    bc1, bc2 = st.columns([2, 1])
    with bc1:
        selected_id = st.selectbox(
            "Select customer",
            df['customer_id'].tolist(),
            format_func=lambda x: (
                f"ID {x} — {df[df['customer_id']==x]['name'].values[0]} "
                f"({df[df['customer_id']==x]['segment'].values[0]}, "
                f"{df[df['customer_id']==x]['churn_probability'].values[0]:.1f}% risk)"
            ) if len(df[df['customer_id']==x]) > 0 else str(x)
        )
    with bc2:
        tone = st.selectbox("Email tone", ["empathetic","professional","urgent","friendly"])

    sel = df[df['customer_id'] == selected_id]
    if len(sel):
        sr = sel.iloc[0]
        cp = float(sr.get('churn_probability', 0))
        bc = "risk-high" if cp>60 else ("risk-med" if cp>30 else "risk-low")
        st.markdown(
            f"<span class='info-pill'>{sr.get('segment','—')}</span>"
            f"<span class='info-pill'>${float(sr.get('TotalCharges',0)):,.0f} LTV</span>"
            f"<span class='info-pill'>{sr.get('Contract','—')}</span>"
            f"&nbsp;&nbsp;<span class='{bc}'>{cp:.1f}% churn risk</span>",
            unsafe_allow_html=True
        )

    ab1, ab2 = st.columns(2)
    with ab1: run_debate = st.button("🚀 Execute Boardroom Debate", use_container_width=True)
    with ab2: run_email  = st.button("✉️ Draft Retention Email",   use_container_width=True)

    if run_debate:
        with st.status("Initialising agent debate...", expanded=True) as status:
            st.write("🔍 Fetching customer ML risk profile...")
            time.sleep(0.3)
            st.write("⚖️ Engaging Customer Success vs CFO personas...")
            time.sleep(0.3)
            st.write("🧠 Orchestrator computing final decision...")
            try:
                debate_data = mcp_call("initiate_boardroom_debate",
                                       {"customer_id": int(selected_id)}, timeout=30)
            except Exception:
                from agent.boardroom import BoardroomDebate
                sr_ = df[df['customer_id']==selected_id].iloc[0]
                engine = BoardroomDebate()
                debate_data = engine.run_debate(
                    sr_['name'], f"{float(sr_.get('churn_probability',30)):.1f}%",
                    float(sr_.get('TotalCharges', 1000))
                )

            if 'error' not in debate_data:
                ai_lbl = "🤖 Gemini AI" if debate_data.get('ai_powered') else "🎭 Simulation"
                st.markdown(f"""
                <div class='thought-stream'>
                  <span class='agent-tag'>[DEBATE TRANSCRIPT]</span> {ai_lbl}<br><br>
                  {debate_data.get('debate_transcript','—')}
                </div>""", unsafe_allow_html=True)
                dc1, dc2 = st.columns(2)
                with dc1: st.success(f"✅ **{debate_data.get('discount',0)}% Discount Approved**")
                with dc2: st.info(f"📋 {debate_data.get('summary','')}")
                status.update(label="✅ Debate Complete", state="complete", expanded=False)
                write_log("boardroom_debate", str(selected_id),
                          f"{debate_data.get('discount',0)}% approved")
            else:
                st.error(debate_data['error'])
                status.update(label="❌ Debate Failed", state="error")

    if run_email:
        with st.spinner("Generating email..."):
            try:
                result = mcp_call("draft_empathy_email",
                                  {"customer_id": int(selected_id), "tone": tone}, timeout=20)
            except Exception as e:
                result = {"email_body": f"Error: {e}", "ai_powered": False}
            lbl = "✨ Gemini" if result.get('ai_powered') else "📝 Template"
            st.markdown(f"**{lbl} Retention Email**")
            st.text_area("Preview", value=result.get('email_body',''), height=200)
            write_log("draft_email", str(selected_id),
                      f"{tone} email — {'AI' if result.get('ai_powered') else 'template'}")

    st.write("---")
    st.markdown("<div class='section-title'>Historical Agent Action Log</div>",
                unsafe_allow_html=True)
    logs_df = get_logs()
    if not logs_df.empty:
        for _, lr in logs_df.iterrows():
            ts   = str(lr.get('timestamp',''))[:19]
            tool = lr.get('tool_name','')
            res  = lr.get('result','')
            st.markdown(f"""
            <div class='thought-stream' style='color:#E0AAFF;border-left-color:#7000FF;font-size:.8rem'>
              <span style='color:var(--primary)'>[{ts}]</span> <b>{tool}</b>: {res}
            </div>""", unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='thought-stream'>No agent actions logged yet.</div>",
            unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot-3.png", width=65)
    st.markdown("<h3 style='color:#00F5FF;font-family:Orbitron;margin:0'>WAR ROOM</h3>",
                unsafe_allow_html=True)
    st.markdown("<p style='color:#666;font-size:.75rem;margin-top:2px'>v3.0 · Causal AI</p>",
                unsafe_allow_html=True)

    # System status
    st.markdown("**System Status**")
    if supabase:                st.success("🟢 Supabase")
    else:                       st.info("🟡 SQLite Mode")
    if CHURN_MODEL:             st.success("🟢 ML Model")
    else:                       st.warning("🟠 No ML Model")
    if GOOGLE_API_KEY:          st.success("🟢 Gemini Active")
    else:                       st.warning("🟡 Gemini: Simulation")
    try:
        requests.get(MCP_URL, timeout=1)
        st.success("🟢 MCP Server")
    except Exception:
        st.warning("🟠 MCP Offline")

    st.divider()

    # ── Priority Queue ────────────────────────────────────────────────────
    st.markdown("**🚨 Priority Queue**")
    st.caption("Highest expected revenue loss — act now")

    # Sort by churn_probability × TotalCharges (expected loss)
    pq = df.copy()
    pq['expected_loss'] = pq['churn_probability'] / 100 * pq['TotalCharges']
    pq = (pq[pq['segment'] == 'At Risk']
          .sort_values('expected_loss', ascending=False)
          .head(5))

    for _, pr in pq.iterrows():
        cp_  = float(pr['churn_probability'])
        el_  = float(pr['expected_loss'])
        name = str(pr['name'])
        cid  = int(pr['customer_id'])
        st.markdown(f"""
        <div class='priority-card'>
          <div class='priority-name'>{name}</div>
          <div class='priority-risk'>⚠ {cp_:.1f}% churn · ${el_:,.0f} at risk</div>
        </div>""", unsafe_allow_html=True)
        p1, p2 = st.columns(2)
        with p1:
            if st.button("🎁 Discount", key=f"pq_disc_{cid}", use_container_width=True):
                try:
                    r_ = mcp_call("generate_discount", {"customer_id": cid})
                    st.toast(f"✅ {r_.get('msg','Done')}")
                    write_log("generate_discount", str(cid), r_.get('msg',''))
                except Exception as e:
                    st.toast(f"❌ {e}")
        with p2:
            if st.button("⭐ VIP", key=f"pq_vip_{cid}", use_container_width=True):
                try:
                    r_ = mcp_call("flag_vip", {"customer_id": cid})
                    st.toast(f"✅ {r_.get('msg','Done')}")
                    write_log("flag_vip", str(cid), r_.get('msg',''))
                except Exception as e:
                    st.toast(f"❌ {e}")

    st.divider()

    # Quick actions
    st.markdown("**Quick Actions**")
    if st.button("↺ Re-run ML Scoring", use_container_width=True):
        with st.spinner("Scoring..."):
            try:
                d_ = mcp_call("segment_customers", {}, timeout=20)
                st.success(f"Done: {d_.get('summary',{})}")
            except Exception:
                fresh = load_data()
                scored = score_and_segment(fresh)
                persist_scores(scored)
                st.success("Scored locally!")
        st.rerun()

    if st.button("⟳ Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("**Overview**")
    st.markdown(f"<span class='info-pill'>{len(df)} customers</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='info-pill'>{at_risk} at risk</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='info-pill'>${rev_at_risk:,.0f} at risk</span>",
                unsafe_allow_html=True)
    st.markdown(f"<span class='info-pill'>avg {avg_churn:.1f}% churn</span>",
                unsafe_allow_html=True)

    st.divider()
    st.markdown(
        "<p style='color:#5A189A;font-size:.72rem;text-align:center'>"
        "Retention War Room v3.0<br>Causal AI · Hackathon Build</p>",
        unsafe_allow_html=True)
