import streamlit as st
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh
import sys
import os
import numpy as np
import json
from supabase import create_client
from dotenv import load_dotenv

load_dotenv()

# =========================
# CONFIG & SUPABASE
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

import sqlite3

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")

@st.cache_resource
def get_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        try:
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        except Exception:
            return None
    return None

supabase = get_supabase()

# Page config for premium feel
st.set_page_config(
    page_title="Retention Agent | Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-end aesthetics (War Room / Neon Glassmorphism)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700&family=Inter:wght@300;400;700&display=swap');

    :root {
        --primary: #00F5FF;
        --secondary: #7000FF;
        --bg: #050505;
        --card-bg: rgba(20, 20, 20, 0.7);
    }
    
    .stApp {
        background: radial-gradient(circle at top right, #1a1a2e, #050505);
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    .main-header {
        font-family: 'Orbitron', sans-serif;
        background: linear-gradient(90deg, var(--primary), var(--secondary));
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3.5rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin-bottom: 0rem;
    }

    /* Glassmorphism Cards */
    .metric-card {
        background: var(--card-bg);
        border: 1px solid rgba(0, 245, 255, 0.2);
        border-radius: 20px;
        padding: 25px;
        text-align: left;
        backdrop-filter: blur(15px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.8);
        transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
    }
    
    .metric-card:hover {
        transform: scale(1.02);
        border-color: var(--primary);
        box-shadow: 0 0 20px rgba(0, 245, 255, 0.3);
    }

    .metric-value {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.2rem;
        font-weight: 700;
        margin: 10px 0;
    }

    /* Thought Stream Styles */
    .thought-stream {
        background: rgba(0, 0, 0, 0.9);
        border-left: 2px solid var(--primary);
        padding: 15px;
        border-radius: 0 15px 15px 0;
        font-family: 'Courier New', monospace;
        font-size: 0.9rem;
        color: #00FF41;
        margin-bottom: 15px;
        box-shadow: inset 0 0 10px rgba(0, 255, 65, 0.1);
    }
    
    .agent-tag {
        color: var(--primary);
        font-weight: bold;
        text-transform: uppercase;
    }

    /* Tabs Styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 20px;
        background-color: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: var(--card-bg);
        border-radius: 10px 10px 0px 0px;
        color: white;
        padding: 0 20px;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: rgba(0, 245, 255, 0.1) !important;
        border-bottom: 2px solid var(--primary) !important;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    if supabase:
        try:
            res = supabase.table("customers").select("*").execute()
            df = pd.DataFrame(res.data)
            if not df.empty:
                expected = ["customer_id", "name", "email", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges", "segment", "vip_flag", "discount_code"]
                mapping = {col.lower(): col for col in expected}
                df.columns = [mapping.get(c.lower(), c) for c in df.columns]
                return df
        except Exception:
            pass
    # Fallback to local SQLite
    if os.path.exists(DB_PATH):
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query("SELECT * FROM customers", conn)
        conn.close()
        return df
    return pd.DataFrame()

# --- UI LAYOUT ---
st.markdown("<h1 class='main-header'>Customer Retention Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #9D4EDD;'>Live Supabase Cloud Dashboard</p>", unsafe_allow_html=True)

# Auto-refresh
st_autorefresh(interval=5000, key="datarefresh")

df = load_data()

if df.empty:
    st.error("No data found. Please check your database connection or ensure data/mock_crm.db exists.")
    st.stop()

# Top Metrics
col1, col2, col3, col4, col5 = st.columns(5)
with col1:
    st.markdown(f"<div class='metric-card'><h3>Total Customers</h3><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
with col2:
    at_risk = len(df[df['segment'] == 'At Risk'])
    st.markdown(f"<div class='metric-card'><h3>At Risk 🚨</h3><h2 style='color: #FF4D4D;'>{at_risk}</h2></div>", unsafe_allow_html=True)
with col3:
    champions = len(df[df['segment'] == 'Champion'])
    st.markdown(f"<div class='metric-card'><h3>Champions 🏆</h3><h2 style='color: #4DFF88;'>{champions}</h2></div>", unsafe_allow_html=True)
with col4:
    spenders = len(df[df['segment'] == 'Big Spender'])
    st.markdown(f"<div class='metric-card'><h3>Big Spenders 💰</h3><h2 style='color: #FFD700;'>{spenders}</h2></div>", unsafe_allow_html=True)
with col5:
    rev = f"${df['TotalCharges'].sum():,.0f}"
    st.markdown(f"<div class='metric-card'><h3>Total Revenue</h3><h2>{rev}</h2></div>", unsafe_allow_html=True)

st.write("---")

tab1, tab2, tab3 = st.tabs(["📊 Segmentation", "👥 Customer List", "📡 Agent Activity"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(df, names='segment', title='Market Segmentation', 
                     color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig, use_container_width=True)
    with c2:
        fig2 = px.scatter(df, x='tenure', y='MonthlyCharges', color='segment',
                         size='TotalCharges', hover_name='name', title='Spend vs Tenure Analysis')
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig2, use_container_width=True)

with tab2:
    # Stylized Dataframe
    st.dataframe(
        df[['customer_id', 'name', 'segment', 'MonthlyCharges', 'TotalCharges', 'vip_flag', 'discount_code']]
        .sort_values(by='TotalCharges', ascending=False)
        .style.background_gradient(subset=['MonthlyCharges'], cmap='Purples')
        .format({'TotalCharges': '${:,.2f}', 'MonthlyCharges': '${:,.2f}'}),
        use_container_width=True
    )

with tab3:
    st.markdown("### 📡 Agent Intelligence & Thought Stream")
    
    selected_customer = st.selectbox("Select Customer for Autonomous Review", df['customer_id'].tolist(), format_func=lambda x: f"ID {x} - {df[df['customer_id']==x]['name'].values[0]}")
    
    if st.button("🚀 Execute Autonomous Boardroom Debate"):
        with st.status("Initializing Gemini Boardroom Agents...", expanded=True) as status:
            st.write("🔍 Analyzing customer churn risk...")
            time.sleep(1)
            st.write("⚖️ Engaging Multi-Agent Debate (Success vs CFO)...")
            
            # Call the new debate tool
            try:
                # Simulate the tool call for the UI demo if server is local
                import requests
                res = requests.post("http://127.0.0.1:8000/", json={
                    "jsonrpc": "2.0", "method": "tools/call", "params": {"name": "initiate_boardroom_debate", "arguments": {"customer_id": int(selected_customer)}}
                }).json()
                
                debate_data = json.loads(res['result']['content'][0]['text'])
                
                st.markdown(f"""
                <div class='thought-stream'>
                    <span class='agent-tag'>[ORCHESTRATOR]</span> Analyzing viewpoints...<br><br>
                    {debate_data.get('debate_transcript', 'Debate in progress...')}
                </div>
                """, unsafe_allow_html=True)
                
                st.success(f"Decision Reached: {debate_data['discount']}% Discount Approved")
                st.info(f"Summary: {debate_data['summary']}")
                status.update(label="✅ Decision Finalized", state="complete", expanded=False)
                
            except Exception as e:
                st.error(f"Agent connection error: {e}")
                status.update(label="❌ Debate Deadlock", state="error")

    st.write("---")
    st.markdown("#### 📜 Historical Action Logs")
    if supabase:
        try:
            logs_res = supabase.table("agent_logs").select("*").order("timestamp", desc=True).limit(10).execute()
            logs_df = pd.DataFrame(logs_res.data)
            if not logs_df.empty:
                for _, row in logs_df.iterrows():
                    st.markdown(f"""
                    <div class='thought-stream' style='color: #E0AAFF; border-left-color: var(--secondary);'>
                        <span style='color: var(--primary);'>[{row['timestamp']}]</span> 
                        <b>{row['tool_name']}</b>: {row['result']}
                    </div>
                    """, unsafe_allow_html=True)
        except:
            st.info("No historical logs available.")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot-3.png", width=80)
    st.title("MCP Controller")
    if supabase:
        st.success("🟢 Connected to Supabase")
    else:
        st.info("🟡 Running on Local SQLite DB")
    st.divider()
    st.write("The Gemini Agent is currently processing churn risks and updating segments in real-time.")
    if st.button("Force DB Refresh"):
        st.rerun()

st.markdown("<br><p style='text-align: center; color: #5A189A;'>Hackathon Prototype - Customer Retention Agent v1.1</p>", unsafe_allow_html=True)
