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
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")
ML_DIR = os.path.join(BASE_DIR, "ml")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# =========================
# SUPABASE
# =========================
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

# =========================
# PAGE CONFIG & STYLES
# =========================
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
        --primary: #00F5FF;
        --secondary: #7000FF;
        --accent: #FF006E;
        --success: #4DFF88;
        --warn: #FFD700;
        --bg: #050508;
        --card-bg: rgba(15, 15, 25, 0.85);
        --border: rgba(0, 245, 255, 0.15);
    }

    .stApp {
        background: radial-gradient(ellipse at 80% 0%, #0d0d2b 0%, #050508 60%);
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }

    .main-header {
        font-family: 'Orbitron', sans-serif;
        background: linear-gradient(90deg, var(--primary), var(--secondary), var(--accent));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 900;
        text-transform: uppercase;
        letter-spacing: 3px;
        margin-bottom: 0;
        line-height: 1.1;
    }

    .sub-header {
        color: #9D4EDD;
        font-size: 0.9rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        margin-top: 4px;
    }

    .metric-card {
        background: var(--card-bg);
        border: 1px solid var(--border);
        border-radius: 16px;
        padding: 20px 22px;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0,0,0,0.6), inset 0 1px 0 rgba(255,255,255,0.05);
        transition: all 0.3s ease;
        height: 100%;
    }
    .metric-card:hover {
        border-color: var(--primary);
        box-shadow: 0 0 24px rgba(0,245,255,0.2), 0 8px 32px rgba(0,0,0,0.6);
        transform: translateY(-2px);
    }
    .metric-label {
        font-size: 0.75rem;
        color: #888;
        text-transform: uppercase;
        letter-spacing: 1.5px;
        margin-bottom: 8px;
    }
    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 2rem;
        font-weight: 700;
        line-height: 1;
    }
    .metric-delta {
        font-size: 0.75rem;
        color: #4DFF88;
        margin-top: 4px;
    }

    .thought-stream {
        background: rgba(0,0,0,0.7);
        border-left: 3px solid var(--primary);
        padding: 16px 20px;
        border-radius: 0 12px 12px 0;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        color: #00FF41;
        margin-bottom: 12px;
        box-shadow: inset 0 0 15px rgba(0,255,65,0.05);
        line-height: 1.6;
    }
    .agent-tag { color: var(--primary); font-weight: bold; text-transform: uppercase; }

    .risk-badge-high {
        background: rgba(255,77,77,0.2);
        border: 1px solid #FF4D4D;
        color: #FF4D4D;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .risk-badge-med {
        background: rgba(255,215,0,0.15);
        border: 1px solid #FFD700;
        color: #FFD700;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .risk-badge-low {
        background: rgba(77,255,136,0.15);
        border: 1px solid #4DFF88;
        color: #4DFF88;
        padding: 2px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
        border-bottom: 1px solid var(--border);
    }
    .stTabs [data-baseweb="tab"] {
        background: var(--card-bg);
        border-radius: 10px 10px 0 0;
        color: #888;
        padding: 0 20px;
        height: 44px;
        border: 1px solid var(--border);
        border-bottom: none;
        font-size: 0.85rem;
        font-weight: 600;
        letter-spacing: 0.5px;
    }
    .stTabs [aria-selected="true"] {
        background: rgba(0,245,255,0.08) !important;
        border-color: var(--primary) !important;
        color: var(--primary) !important;
    }

    div[data-testid="stSelectbox"] > div { background: var(--card-bg); border-color: var(--border); }
    div[data-testid="stSlider"] .stSlider { color: var(--primary); }
    .stButton > button {
        background: linear-gradient(135deg, var(--secondary), var(--primary));
        color: white;
        border: none;
        border-radius: 8px;
        font-weight: 600;
        letter-spacing: 0.5px;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-1px);
        box-shadow: 0 6px 20px rgba(0,245,255,0.3);
    }

    .section-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1rem;
        color: var(--primary);
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 16px 0 12px;
        padding-bottom: 8px;
        border-bottom: 1px solid var(--border);
    }

    .info-pill {
        display: inline-block;
        background: rgba(112,0,255,0.2);
        border: 1px solid rgba(112,0,255,0.4);
        color: #C77DFF;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        margin: 2px;
    }

    [data-testid="stSidebar"] {
        background: rgba(5,5,15,0.95) !important;
        border-right: 1px solid var(--border);
    }
</style>
""", unsafe_allow_html=True)


# =========================
# ML SCORING ENGINE
# =========================
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
FEATURE_NAMES = ['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
                 'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
                 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV',
                 'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod',
                 'MonthlyCharges']


def safe_encode(le, value):
    val = str(value).strip()
    if hasattr(le, 'classes_'):
        classes_lower = [str(c).lower() for c in le.classes_]
        if val.lower() in classes_lower:
            idx = classes_lower.index(val.lower())
            return le.transform([le.classes_[idx]])[0]
    return 0


def score_and_segment(df: pd.DataFrame) -> pd.DataFrame:
    """Run ML scoring and segment classification on the dataframe."""
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
    df['churn_risk'] = probs
    df['churn_probability'] = (probs * 100).round(1)

    def classify(row):
        if row['churn_risk'] > 0.5:
            return 'At Risk'
        if row['MonthlyCharges'] > 90:
            return 'Big Spender'
        if row['MonthlyCharges'] > 65:
            return 'Champion'
        return 'Loyal'

    df['segment'] = df.apply(classify, axis=1)
    return df


def persist_scores(df: pd.DataFrame):
    """Write ML scores back to SQLite."""
    if not os.path.exists(DB_PATH):
        return
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(
            "UPDATE customers SET segment=?, churn_probability=? WHERE customer_id=?",
            (row.get('segment', 'Unassigned'),
             float(row.get('churn_probability', 0)),
             int(row['customer_id']))
        )
    conn.commit()
    conn.close()


# =========================
# DATA LOADING
# =========================
def load_data() -> pd.DataFrame:
    if supabase:
        try:
            res = supabase.table("customers").select("*").execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                expected = ["customer_id", "name", "email", "gender", "SeniorCitizen",
                            "Partner", "Dependents", "tenure", "PhoneService", "MultipleLines",
                            "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection",
                            "TechSupport", "StreamingTV", "StreamingMovies", "Contract",
                            "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges",
                            "segment", "vip_flag", "discount_code", "churn_probability"]
                mapping = {c.lower(): c for c in expected}
                df.columns = [mapping.get(c.lower(), c) for c in df.columns]
                return df
        except Exception:
            pass

    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM customers", conn)
        conn.close()
        return df

    return pd.DataFrame()


def get_logs() -> pd.DataFrame:
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        try:
            df = pd.read_sql_query(
                "SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT 20", conn
            )
            conn.close()
            return df
        except Exception:
            conn.close()
    return pd.DataFrame()


# =========================
# CHART HELPERS
# =========================
DARK_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(5,5,15,0.4)',
    font_color="#C0C0C0",
    font_family="Inter",
    margin=dict(t=36, b=20, l=10, r=10),
    legend=dict(bgcolor='rgba(0,0,0,0)', bordercolor='rgba(255,255,255,0.1)', borderwidth=1),
    xaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.1)'),
    yaxis=dict(gridcolor='rgba(255,255,255,0.05)', zerolinecolor='rgba(255,255,255,0.1)')
)

SEGMENT_COLORS = {
    'At Risk': '#FF4D4D',
    'Champion': '#4DFF88',
    'Big Spender': '#FFD700',
    'Loyal': '#00F5FF',
    'Unassigned': '#888888'
}


# =========================
# HEADER
# =========================
col_logo, col_title = st.columns([1, 8])
with col_logo:
    st.image("https://img.icons8.com/fluency/96/robot-3.png", width=70)
with col_title:
    st.markdown("<h1 class='main-header'>Retention War Room</h1>", unsafe_allow_html=True)
    st.markdown("<p class='sub-header'>Causal AI · Multi-Agent Debate · SciPy Optimization</p>",
                unsafe_allow_html=True)

st_autorefresh(interval=30000, key="datarefresh")

# =========================
# LOAD + AUTO-SCORE
# =========================
raw_df = load_data()

if raw_df.empty:
    st.error("No data found. Run `python data/crm_init.py` to initialize the database.")
    st.stop()

# Auto-score if segments are unassigned or churn_probability is missing/zero
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
for col in ['MonthlyCharges', 'TotalCharges', 'churn_probability', 'churn_risk']:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)

# =========================
# TOP METRICS
# =========================
at_risk = len(df[df['segment'] == 'At Risk'])
champions = len(df[df['segment'] == 'Champion'])
spenders = len(df[df['segment'] == 'Big Spender'])
avg_churn = df['churn_probability'].mean()
total_rev = df['TotalCharges'].sum()
vip_count = int(df.get('vip_flag', pd.Series([0])).sum()) if 'vip_flag' in df.columns else 0

m1, m2, m3, m4, m5, m6 = st.columns(6)
metrics = [
    (m1, "Total Customers", len(df), "#00F5FF", ""),
    (m2, "At Risk 🚨", at_risk, "#FF4D4D", f"{at_risk/len(df)*100:.0f}% of base"),
    (m3, "Champions 🏆", champions, "#4DFF88", "High value"),
    (m4, "Big Spenders 💰", spenders, "#FFD700", f">${df[df['segment']=='Big Spender']['MonthlyCharges'].mean():.0f}/mo avg" if spenders else ""),
    (m5, "Avg Churn Risk", f"{avg_churn:.1f}%", "#C77DFF", "ML predicted"),
    (m6, "Total Revenue", f"${total_rev:,.0f}", "#00F5FF", f"{vip_count} VIP customers"),
]
for col, label, val, color, delta in metrics:
    with col:
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-label'>{label}</div>
            <div class='metric-value' style='color:{color}'>{val}</div>
            <div class='metric-delta'>{delta}</div>
        </div>""", unsafe_allow_html=True)

st.write("")

# =========================
# TABS
# =========================
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Segmentation",
    "👥 Customers",
    "⚙️ Budget Optimizer",
    "📈 KPI Simulator",
    "🤖 Agent Debate"
])


# ── TAB 1: SEGMENTATION ──────────────────────────────────────────────────────
with tab1:
    r1c1, r1c2 = st.columns(2)

    with r1c1:
        seg_counts = df['segment'].value_counts().reset_index()
        seg_counts.columns = ['segment', 'count']
        color_map = SEGMENT_COLORS
        fig_pie = px.pie(
            seg_counts, names='segment', values='count',
            title='Customer Segments',
            color='segment', color_discrete_map=color_map,
            hole=0.45
        )
        fig_pie.update_traces(textfont_size=13, pull=[0.05] * len(seg_counts))
        fig_pie.update_layout(**DARK_LAYOUT, title_font_color='#00F5FF',
                              title_font_family='Orbitron')
        st.plotly_chart(fig_pie, use_container_width=True)

    with r1c2:
        fig_scatter = px.scatter(
            df, x='tenure', y='MonthlyCharges',
            color='segment', color_discrete_map=color_map,
            size='TotalCharges', size_max=30,
            hover_name='name',
            hover_data={'churn_probability': ':.1f', 'tenure': True, 'MonthlyCharges': ':.2f'},
            title='Spend vs Tenure (bubble = LTV)',
        )
        fig_scatter.update_layout(**DARK_LAYOUT, title_font_color='#00F5FF',
                                  title_font_family='Orbitron')
        st.plotly_chart(fig_scatter, use_container_width=True)

    r2c1, r2c2 = st.columns(2)

    with r2c1:
        fig_hist = px.histogram(
            df, x='churn_probability', nbins=20,
            color='segment', color_discrete_map=color_map,
            title='Churn Risk Distribution',
            labels={'churn_probability': 'Churn Probability (%)'}
        )
        fig_hist.update_layout(**DARK_LAYOUT, title_font_color='#00F5FF',
                               title_font_family='Orbitron', bargap=0.05)
        st.plotly_chart(fig_hist, use_container_width=True)

    with r2c2:
        rev_by_seg = df.groupby('segment').agg(
            Total_Revenue=('TotalCharges', 'sum'),
            Count=('customer_id', 'count'),
            Avg_Churn=('churn_probability', 'mean')
        ).reset_index().sort_values('Total_Revenue', ascending=True)

        fig_bar = go.Figure(go.Bar(
            x=rev_by_seg['Total_Revenue'],
            y=rev_by_seg['segment'],
            orientation='h',
            marker=dict(
                color=[SEGMENT_COLORS.get(s, '#888') for s in rev_by_seg['segment']],
                opacity=0.85
            ),
            text=[f"${v:,.0f}" for v in rev_by_seg['Total_Revenue']],
            textposition='auto'
        ))
        fig_bar.update_layout(**DARK_LAYOUT, title='Revenue by Segment',
                              title_font_color='#00F5FF', title_font_family='Orbitron')
        st.plotly_chart(fig_bar, use_container_width=True)


# ── TAB 2: CUSTOMERS ─────────────────────────────────────────────────────────
with tab2:
    st.markdown("<div class='section-title'>Customer Intelligence</div>", unsafe_allow_html=True)

    fc1, fc2, fc3 = st.columns([2, 2, 1])
    with fc1:
        search_term = st.text_input("Search by name", placeholder="e.g. Jennifer Smith")
    with fc2:
        seg_filter = st.multiselect("Filter by segment", options=df['segment'].unique().tolist(),
                                    default=df['segment'].unique().tolist())
    with fc3:
        sort_by = st.selectbox("Sort by", ["TotalCharges", "churn_probability", "MonthlyCharges", "tenure"])

    filtered = df[df['segment'].isin(seg_filter)]
    if search_term:
        filtered = filtered[filtered['name'].str.contains(search_term, case=False, na=False)]
    filtered = filtered.sort_values(by=sort_by, ascending=False)

    display_cols = ['customer_id', 'name', 'segment', 'churn_probability',
                    'MonthlyCharges', 'TotalCharges', 'Contract', 'tenure', 'vip_flag', 'discount_code']
    display_cols = [c for c in display_cols if c in filtered.columns]

    def risk_color(val):
        if val > 60:
            return 'color: #FF4D4D; font-weight: bold'
        if val > 30:
            return 'color: #FFD700'
        return 'color: #4DFF88'

    styled = (
        filtered[display_cols]
        .style
        .map(risk_color, subset=['churn_probability'])
        .background_gradient(subset=['MonthlyCharges'], cmap='Purples')
        .format({
            'TotalCharges': '${:,.2f}',
            'MonthlyCharges': '${:,.2f}',
            'churn_probability': '{:.1f}%'
        })
    )
    st.dataframe(styled, use_container_width=True, height=420)

    st.markdown(f"*Showing {len(filtered)} of {len(df)} customers*")

    # Customer detail expander
    with st.expander("Customer Detail View"):
        detail_id = st.selectbox(
            "Select customer",
            filtered['customer_id'].tolist(),
            format_func=lambda x: f"ID {x} — {filtered[filtered['customer_id'] == x]['name'].values[0]}"
            if len(filtered[filtered['customer_id'] == x]) > 0 else str(x)
        )
        if detail_id:
            row = df[df['customer_id'] == detail_id].iloc[0]
            d1, d2, d3, d4 = st.columns(4)
            churn_pct = float(row.get('churn_probability', 0))
            badge_class = "risk-badge-high" if churn_pct > 60 else ("risk-badge-med" if churn_pct > 30 else "risk-badge-low")
            badge_label = "HIGH RISK" if churn_pct > 60 else ("MEDIUM RISK" if churn_pct > 30 else "LOW RISK")
            with d1:
                st.markdown(f"**Name:** {row['name']}")
                st.markdown(f"**Segment:** {row.get('segment','—')}")
                st.markdown(f"<span class='{badge_class}'>{badge_label} — {churn_pct:.1f}%</span>",
                            unsafe_allow_html=True)
            with d2:
                st.markdown(f"**Monthly:** ${float(row.get('MonthlyCharges',0)):,.2f}")
                st.markdown(f"**Total LTV:** ${float(row.get('TotalCharges',0)):,.2f}")
                st.markdown(f"**Tenure:** {int(row.get('tenure',0))} months")
            with d3:
                st.markdown(f"**Contract:** {row.get('Contract','—')}")
                st.markdown(f"**Internet:** {row.get('InternetService','—')}")
                st.markdown(f"**Payment:** {row.get('PaymentMethod','—')}")
            with d4:
                st.markdown(f"**VIP:** {'✅' if row.get('vip_flag',0) else '—'}")
                st.markdown(f"**Discount:** {row.get('discount_code','None') or 'None'}")
                st.markdown(f"**Gender:** {row.get('gender','—')}")


# ── TAB 3: BUDGET OPTIMIZER ──────────────────────────────────────────────────
with tab3:
    st.markdown("<div class='section-title'>SciPy SLSQP Budget Optimizer</div>", unsafe_allow_html=True)
    st.markdown(
        "Solve the constrained optimization problem: **Maximize** Σ( Pᵢ · LTVᵢ · Uplift(dᵢ) ) "
        "subject to Σ( dᵢ · LTVᵢ ) ≤ Budget, with 0 ≤ dᵢ ≤ 30%.",
        unsafe_allow_html=False
    )

    oc1, oc2, oc3 = st.columns([2, 1, 1])
    with oc1:
        budget = st.slider("Retention Budget ($)", min_value=500, max_value=20000,
                           value=5000, step=250)
    with oc2:
        focus_seg = st.selectbox("Focus on segment", ["All", "At Risk", "Champion", "Big Spender", "Loyal"])
    with oc3:
        st.write("")
        st.write("")
        run_opt = st.button("Run Optimization", use_container_width=True)

    if run_opt or st.session_state.get('opt_result'):
        cohort = df.copy()
        if focus_seg != "All":
            cohort = cohort[cohort['segment'] == focus_seg]

        if cohort.empty:
            st.warning("No customers in selected segment.")
        else:
            if run_opt:
                with st.spinner("Running SciPy SLSQP..."):
                    try:
                        res = requests.post("http://127.0.0.1:8000/", json={
                            "jsonrpc": "2.0", "method": "tools/call",
                            "params": {"name": "trigger_macro_optimization", "arguments": {"budget": float(budget)}}
                        }, timeout=15).json()
                        opt_data = json.loads(res['result']['content'][0]['text'])
                        st.session_state['opt_result'] = opt_data
                        st.session_state['opt_budget'] = budget
                        st.session_state['opt_cohort'] = cohort
                    except Exception as e:
                        # Fall back to local computation
                        sys.path.insert(0, BASE_DIR)
                        from agent.decision_engine import DecisionEngine
                        allocated, total_spend = DecisionEngine.optimize_cohort_discounts(cohort, budget=budget)
                        opt_data = {
                            "status": "success",
                            "budget_used": total_spend,
                            "customers_optimized": len(allocated),
                            "avg_discount_pct": round(np.mean([v['discount_pct'] for v in allocated.values()]), 1) if allocated else 0,
                            "allocations": {str(k): v for k, v in allocated.items()}
                        }
                        st.session_state['opt_result'] = opt_data
                        st.session_state['opt_budget'] = budget
                        st.session_state['opt_cohort'] = cohort

            opt_data = st.session_state.get('opt_result', {})
            opt_cohort = st.session_state.get('opt_cohort', cohort)

            if opt_data.get('status') == 'success':
                r1, r2, r3, r4 = st.columns(4)
                with r1:
                    st.metric("Budget Allocated", f"${opt_data.get('budget_used', 0):,.0f}",
                              f"of ${st.session_state.get('opt_budget', budget):,}")
                with r2:
                    st.metric("Customers Optimized", opt_data.get('customers_optimized', 0))
                with r3:
                    st.metric("Avg Discount", f"{opt_data.get('avg_discount_pct', 0):.1f}%")
                with r4:
                    efficiency = opt_data.get('budget_used', 1) / max(budget, 1) * 100
                    st.metric("Budget Utilization", f"{efficiency:.0f}%")

                # Build allocation chart
                allocs = opt_data.get('allocations', {})
                if allocs:
                    rows = []
                    for c_id, info in allocs.items():
                        cust_row = df[df['customer_id'] == int(c_id)]
                        name = cust_row['name'].values[0] if len(cust_row) > 0 else f"ID {c_id}"
                        seg = cust_row['segment'].values[0] if len(cust_row) > 0 else "Unknown"
                        rows.append({
                            'Customer': name,
                            'Segment': seg,
                            'Discount (%)': info.get('discount_pct', info.get('rate', 0) * 100),
                            'Cost ($)': info.get('cost', 0),
                            'Expected Save ($)': info.get('expected_save', 0)
                        })
                    alloc_df = pd.DataFrame(rows).sort_values('Discount (%)', ascending=False)

                    ac1, ac2 = st.columns(2)
                    with ac1:
                        fig_alloc = px.bar(
                            alloc_df.head(20), x='Discount (%)', y='Customer',
                            orientation='h', color='Segment',
                            color_discrete_map=SEGMENT_COLORS,
                            title='Optimal Discount Allocation (Top 20)',
                        )
                        fig_alloc.update_layout(**DARK_LAYOUT, title_font_color='#00F5FF',
                                               title_font_family='Orbitron', height=420)
                        st.plotly_chart(fig_alloc, use_container_width=True)

                    with ac2:
                        fig_roi = px.scatter(
                            alloc_df, x='Cost ($)', y='Expected Save ($)',
                            color='Segment', color_discrete_map=SEGMENT_COLORS,
                            size='Discount (%)', hover_name='Customer',
                            title='Cost vs Expected Revenue Saved',
                        )
                        fig_roi.add_shape(type='line', x0=0, y0=0,
                                          x1=alloc_df['Cost ($)'].max(),
                                          y1=alloc_df['Cost ($)'].max(),
                                          line=dict(color='#888', dash='dot'))
                        fig_roi.update_layout(**DARK_LAYOUT, title_font_color='#00F5FF',
                                             title_font_family='Orbitron', height=420)
                        st.plotly_chart(fig_roi, use_container_width=True)

                    with st.expander("Full Allocation Table"):
                        st.dataframe(
                            alloc_df.style.format({
                                'Discount (%)': '{:.1f}%',
                                'Cost ($)': '${:,.2f}',
                                'Expected Save ($)': '${:,.2f}'
                            }),
                            use_container_width=True
                        )
            else:
                st.info("Click **Run Optimization** to compute the optimal budget allocation.")

    # Uplift curve visualization (always visible)
    st.markdown("<div class='section-title'>Uplift Model — Diminishing Returns</div>",
                unsafe_allow_html=True)
    d_range = np.linspace(0, 0.30, 100)
    uplift_vals = 1 - np.exp(-10 * d_range)
    fig_uplift = go.Figure()
    fig_uplift.add_trace(go.Scatter(
        x=d_range * 100, y=uplift_vals * 100,
        mode='lines', name='Retention Uplift',
        line=dict(color='#00F5FF', width=3),
        fill='tozeroy', fillcolor='rgba(0,245,255,0.08)'
    ))
    fig_uplift.update_layout(
        **DARK_LAYOUT, title='Discount % → Retention Uplift (1 - e^{-10d})',
        title_font_color='#00F5FF', title_font_family='Orbitron',
        xaxis_title='Discount (%)', yaxis_title='Uplift (%)', height=280
    )
    st.plotly_chart(fig_uplift, use_container_width=True)


# ── TAB 4: KPI SIMULATOR ─────────────────────────────────────────────────────
with tab4:
    st.markdown("<div class='section-title'>Retention Strategy Simulator</div>", unsafe_allow_html=True)
    st.markdown("Model the financial impact of different intervention strategies before committing budget.")

    sc1, sc2 = st.columns([1, 2])
    with sc1:
        st.markdown("**Strategy Parameters**")
        discount_rate = st.slider("Discount Offered (%)", 0, 30, 15)
        intervention_rate = st.slider("Customers Targeted (%)", 0, 100, 40)
        base_churn_rate = st.slider("Base Churn Rate (%)", 1, 50, 25)
        avg_ltv = st.slider("Avg Customer LTV ($)", 500, 10000, int(df['TotalCharges'].mean()))
        total_customers = st.slider("Total Customer Base", 10, 5000, len(df))

    with sc2:
        uplift = float(1 - np.exp(-10 * discount_rate / 100))
        targeted = int(total_customers * intervention_rate / 100)
        at_risk_base = int(total_customers * base_churn_rate / 100)
        saves = int(at_risk_base * intervention_rate / 100 * uplift)
        cost = targeted * avg_ltv * discount_rate / 100
        revenue_retained = saves * avg_ltv
        net_benefit = revenue_retained - cost
        roi_ratio = revenue_retained / max(cost, 1)

        kc1, kc2, kc3, kc4 = st.columns(4)
        kc1.metric("Customers Targeted", f"{targeted:,}")
        kc2.metric("Estimated Saves", f"{saves:,}",
                   delta=f"+{saves/max(at_risk_base,1)*100:.0f}% of at-risk")
        kc3.metric("Net Benefit", f"${net_benefit:,.0f}",
                   delta=f"ROI {roi_ratio:.1f}x",
                   delta_color="normal" if net_benefit > 0 else "inverse")
        kc4.metric("Uplift Achieved", f"{uplift * 100:.1f}%")

        # Scenario comparison chart
        discount_range = np.arange(0, 31, 1)
        scenarios = []
        for d in discount_range:
            u = float(1 - np.exp(-10 * d / 100))
            t = int(total_customers * intervention_rate / 100)
            s = int(at_risk_base * intervention_rate / 100 * u)
            c_val = t * avg_ltv * d / 100
            r_val = s * avg_ltv
            scenarios.append({'Discount (%)': d, 'Net Benefit ($)': r_val - c_val,
                               'Revenue Retained ($)': r_val, 'Cost ($)': c_val})
        scen_df = pd.DataFrame(scenarios)

        fig_sim = go.Figure()
        fig_sim.add_trace(go.Scatter(
            x=scen_df['Discount (%)'], y=scen_df['Revenue Retained ($)'],
            name='Revenue Retained', line=dict(color='#4DFF88', width=2.5),
            fill='tozeroy', fillcolor='rgba(77,255,136,0.05)'
        ))
        fig_sim.add_trace(go.Scatter(
            x=scen_df['Discount (%)'], y=scen_df['Cost ($)'],
            name='Intervention Cost', line=dict(color='#FF4D4D', width=2.5),
            fill='tozeroy', fillcolor='rgba(255,77,77,0.05)'
        ))
        fig_sim.add_trace(go.Scatter(
            x=scen_df['Discount (%)'], y=scen_df['Net Benefit ($)'],
            name='Net Benefit', line=dict(color='#00F5FF', width=3, dash='dot')
        ))
        fig_sim.add_vline(x=discount_rate, line_color='#7000FF',
                          line_dash='dash', annotation_text=f"Current: {discount_rate}%",
                          annotation_font_color='#C77DFF')
        fig_sim.update_layout(
            **DARK_LAYOUT, title='Discount Rate Sensitivity Analysis',
            title_font_color='#00F5FF', title_font_family='Orbitron',
            xaxis_title='Discount (%)', yaxis_title='$ Value', height=360
        )
        st.plotly_chart(fig_sim, use_container_width=True)

    # Segment-level KPI breakdown
    st.markdown("<div class='section-title'>Segment-Level Impact</div>", unsafe_allow_html=True)
    seg_impact = []
    for seg in df['segment'].unique():
        seg_df = df[df['segment'] == seg]
        avg_churn_seg = seg_df['churn_probability'].mean() / 100
        avg_ltv_seg = seg_df['TotalCharges'].mean()
        u = float(1 - np.exp(-10 * discount_rate / 100))
        saves_seg = avg_churn_seg * u * len(seg_df)
        rev_seg = saves_seg * avg_ltv_seg
        seg_impact.append({
            'Segment': seg, 'Count': len(seg_df),
            'Avg Churn Risk': f"{avg_churn_seg * 100:.1f}%",
            'Avg LTV': f"${avg_ltv_seg:,.0f}",
            'Est. Saves': f"{saves_seg:.1f}",
            'Revenue Retained': f"${rev_seg:,.0f}"
        })
    st.dataframe(pd.DataFrame(seg_impact), use_container_width=True)


# ── TAB 5: AGENT DEBATE ──────────────────────────────────────────────────────
with tab5:
    st.markdown("<div class='section-title'>Autonomous Boardroom Debate</div>", unsafe_allow_html=True)

    if not GOOGLE_API_KEY:
        st.info(
            "Running in **Simulation Mode** — set `GOOGLE_API_KEY` in your environment to enable "
            "live Gemini-powered debates. The simulation uses deterministic logic based on real ML scores.",
            icon="ℹ️"
        )

    bc1, bc2 = st.columns([2, 1])
    with bc1:
        selected_id = st.selectbox(
            "Select customer for autonomous review",
            df['customer_id'].tolist(),
            format_func=lambda x: (
                f"ID {x} — {df[df['customer_id']==x]['name'].values[0]} "
                f"({df[df['customer_id']==x]['segment'].values[0]}, "
                f"{df[df['customer_id']==x]['churn_probability'].values[0]:.1f}% churn risk)"
            ) if len(df[df['customer_id']==x]) > 0 else str(x)
        )
    with bc2:
        tone = st.selectbox("Email tone", ["empathetic", "professional", "urgent", "friendly"])

    selected_row = df[df['customer_id'] == selected_id].iloc[0] if len(df[df['customer_id'] == selected_id]) > 0 else None
    if selected_row is not None:
        churn_pct = float(selected_row.get('churn_probability', 0))
        badge = "risk-badge-high" if churn_pct > 60 else ("risk-badge-med" if churn_pct > 30 else "risk-badge-low")
        st.markdown(
            f"<span class='info-pill'>{selected_row.get('segment','—')}</span>"
            f"<span class='info-pill'>${float(selected_row.get('TotalCharges',0)):,.0f} LTV</span>"
            f"<span class='info-pill'>{selected_row.get('Contract','—')}</span>"
            f"&nbsp;&nbsp;<span class='{badge}'>{churn_pct:.1f}% churn risk</span>",
            unsafe_allow_html=True
        )

    ab1, ab2 = st.columns(2)
    with ab1:
        run_debate = st.button("🚀 Execute Boardroom Debate", use_container_width=True)
    with ab2:
        run_email = st.button("✉️ Draft Retention Email", use_container_width=True)

    if run_debate:
        with st.status("Initializing agent debate...", expanded=True) as status:
            st.write("🔍 Fetching customer ML risk profile...")
            time.sleep(0.4)
            st.write("⚖️ Engaging Customer Success vs CFO personas...")
            time.sleep(0.4)
            st.write("🧠 Orchestrator computing final decision...")

            try:
                res = requests.post("http://127.0.0.1:8000/", json={
                    "jsonrpc": "2.0", "method": "tools/call",
                    "params": {"name": "initiate_boardroom_debate",
                               "arguments": {"customer_id": int(selected_id)}}
                }, timeout=30).json()
                debate_data = json.loads(res['result']['content'][0]['text'])
            except Exception:
                from agent.boardroom import BoardroomDebate
                if selected_row is not None:
                    engine = BoardroomDebate()
                    debate_data = engine.run_debate(
                        selected_row['name'],
                        f"{float(selected_row.get('churn_probability', 30)):.1f}%",
                        float(selected_row.get('TotalCharges', 1000))
                    )
                else:
                    debate_data = {"error": "Customer not found"}

            if 'error' not in debate_data:
                ai_badge = "🤖 AI-Powered" if debate_data.get('ai_powered') else "🎭 Simulation"
                st.markdown(f"""
                <div class='thought-stream'>
                    <span class='agent-tag'>[DEBATE TRANSCRIPT]</span> {ai_badge}<br><br>
                    {debate_data.get('debate_transcript', 'No transcript available.')}
                </div>
                """, unsafe_allow_html=True)

                dc1, dc2 = st.columns(2)
                with dc1:
                    st.success(f"✅ Decision: **{debate_data.get('discount', 0)}% Discount Approved**")
                with dc2:
                    st.info(f"📋 {debate_data.get('summary', '')}")
                status.update(label="✅ Debate Complete", state="complete", expanded=False)
            else:
                st.error(debate_data['error'])
                status.update(label="❌ Debate Failed", state="error")

    if run_email:
        with st.spinner("Generating retention email..."):
            try:
                res = requests.post("http://127.0.0.1:8000/", json={
                    "jsonrpc": "2.0", "method": "tools/call",
                    "params": {"name": "draft_empathy_email",
                               "arguments": {"customer_id": int(selected_id), "tone": tone}}
                }, timeout=20).json()
                email_data = json.loads(res['result']['content'][0]['text'])
            except Exception as e:
                email_data = {"email_body": f"Error generating email: {e}", "ai_powered": False}

            ai_label = "✨ Gemini-Generated" if email_data.get('ai_powered') else "📝 Template"
            st.markdown(f"**{ai_label} Retention Email:**")
            st.text_area("Email Preview", value=email_data.get('email_body', ''), height=200)

    st.write("---")
    st.markdown("<div class='section-title'>Historical Agent Action Log</div>", unsafe_allow_html=True)
    logs_df = get_logs()
    if not logs_df.empty:
        for _, log_row in logs_df.iterrows():
            ts = str(log_row.get('timestamp', ''))[:19]
            tool = log_row.get('tool_name', '')
            result = log_row.get('result', '')
            st.markdown(f"""
            <div class='thought-stream' style='color: #E0AAFF; border-left-color: #7000FF; font-size:0.8rem;'>
                <span style='color: var(--primary);'>[{ts}]</span>
                <b>{tool}</b>: {result}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown(
            "<div class='thought-stream'>No agent actions logged yet. Run a debate or generate a discount to see logs.</div>",
            unsafe_allow_html=True
        )


# =========================
# SIDEBAR
# =========================
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot-3.png", width=70)
    st.markdown("<h3 style='color:#00F5FF; font-family:Orbitron;'>WAR ROOM</h3>", unsafe_allow_html=True)

    st.markdown("**System Status**")
    if supabase:
        st.success("🟢 Supabase Connected")
    else:
        st.info("🟡 Local SQLite Mode")

    if CHURN_MODEL:
        st.success("🟢 ML Model Loaded")
    else:
        st.warning("🟠 ML Model Missing")

    if GOOGLE_API_KEY:
        st.success("🟢 Gemini API Active")
    else:
        st.warning("🟡 Gemini: Simulation Mode")

    try:
        r = requests.get("http://127.0.0.1:8000/", timeout=1)
        st.success("🟢 MCP Server Running")
    except Exception:
        st.warning("🟠 MCP Server Offline")

    st.divider()

    st.markdown("**Quick Actions**")
    if st.button("Re-run ML Scoring", use_container_width=True):
        with st.spinner("Scoring..."):
            try:
                res = requests.post("http://127.0.0.1:8000/", json={
                    "jsonrpc": "2.0", "method": "tools/call",
                    "params": {"name": "segment_customers", "arguments": {}}
                }, timeout=20).json()
                data = json.loads(res['result']['content'][0]['text'])
                st.success(f"Scored! Summary: {data.get('summary', {})}")
            except Exception as e:
                # Fallback to local
                fresh = load_data()
                scored = score_and_segment(fresh)
                persist_scores(scored)
                st.success("Scored locally!")
        st.rerun()

    if st.button("Refresh Dashboard", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("**Dataset Overview**")
    st.markdown(f"<span class='info-pill'>{len(df)} customers</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='info-pill'>{at_risk} at risk</span>", unsafe_allow_html=True)
    st.markdown(f"<span class='info-pill'>Avg risk {avg_churn:.1f}%</span>", unsafe_allow_html=True)

    st.divider()
    st.markdown(
        "<p style='color:#5A189A; font-size:0.75rem; text-align:center;'>"
        "Retention War Room v2.0<br>Causal AI · Hackathon Build</p>",
        unsafe_allow_html=True
    )
