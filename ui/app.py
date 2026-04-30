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

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

@st.cache_resource
def get_supabase():
    if SUPABASE_URL and SUPABASE_KEY:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    return None

supabase = get_supabase()

# Page config for premium feel
st.set_page_config(
    page_title="Retention Agent | Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for high-end aesthetics
st.markdown("""
<style>
    :root {
        --primary-color: #7B2CBF;
        --secondary-color: #3C096C;
        --background-color: #10002B;
        --text-color: #E0AAFF;
    }
    
    .stApp {
        background-color: #10002B;
        color: #E0AAFF;
    }
    
    .main-header {
        font-family: 'Outfit', sans-serif;
        background: linear-gradient(90deg, #7B2CBF, #9D4EDD);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
    }
    
    .metric-card {
        background: rgba(60, 9, 108, 0.4);
        border: 1px solid #7B2CBF;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        transition: transform 0.3s ease;
    }
    
    .metric-card:hover {
        transform: translateY(-5px);
        border-color: #9D4EDD;
    }
    
    .log-container {
        background: #000000;
        border-left: 4px solid #7B2CBF;
        padding: 15px;
        border-radius: 0 10px 10px 0;
        font-family: 'Courier New', Courier, monospace;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

def load_data():
    if supabase:
        res = supabase.table("customers").select("*").execute()
        df = pd.DataFrame(res.data)
        if not df.empty:
            expected = ["customer_id", "name", "email", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges", "segment", "vip_flag", "discount_code"]
            mapping = {col.lower(): col for col in expected}
            df.columns = [mapping.get(c.lower(), c) for c in df.columns]
        return df
    return pd.DataFrame()

# --- UI LAYOUT ---
st.markdown("<h1 class='main-header'>Customer Retention Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #9D4EDD;'>Live Supabase Cloud Dashboard</p>", unsafe_allow_html=True)

# Auto-refresh
st_autorefresh(interval=5000, key="datarefresh")

df = load_data()

if df.empty:
    st.error("No data found in Supabase. Please check your connection.")
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
    st.markdown("### 📡 Live Agent Action Logs")
    if supabase:
        logs_res = supabase.table("agent_logs").select("*").order("timestamp", desc=True).limit(15).execute()
        logs_df = pd.DataFrame(logs_res.data)
        if not logs_df.empty:
            for _, row in logs_df.iterrows():
                st.markdown(f"""
                <div class='log-container'>
                    <span style='color: #9D4EDD;'>[{row['timestamp']}]</span> 
                    <b>{row['tool_name']}</b><br>
                    <div style='color: #E0AAFF;'>Result: {row['result']}</div>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("No agent actions recorded in Supabase yet.")

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot-3.png", width=80)
    st.title("MCP Controller")
    st.success("🟢 Connected to Supabase")
    st.divider()
    st.write("The Gemini Agent is currently processing churn risks and updating segments in real-time.")
    if st.button("Force DB Refresh"):
        st.rerun()

st.markdown("<br><p style='text-align: center; color: #5A189A;'>Hackathon Prototype - Customer Retention Agent v1.1</p>", unsafe_allow_html=True)
