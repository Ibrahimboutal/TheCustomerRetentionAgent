import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import time
from datetime import datetime

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
    
    .sub-header {
        font-size: 1.2rem;
        color: #9D4EDD;
        margin-bottom: 2rem;
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
    
    .stButton>button {
        background: linear-gradient(45deg, #7B2CBF, #5A189A);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.8rem 2rem;
        font-weight: 600;
        transition: all 0.3s;
        width: 100%;
    }
    
    .stButton>button:hover {
        background: linear-gradient(45deg, #9D4EDD, #7B2CBF);
        box-shadow: 0 0 20px rgba(157, 78, 221, 0.6);
        transform: scale(1.02);
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

DB_PATH = "mock_crm.db"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df

def run_retention_pipeline():
    # This simulates the Gemini Agent calling the MCP tools
    logs = []
    
    def add_log(msg, type="info"):
        emoji = "🔍" if type=="info" else "⚡" if type=="action" else "✅"
        logs.append(f"{emoji} [{datetime.now().strftime('%H:%M:%S')}] {msg}")
        log_area.markdown("\n".join([f"<div class='log-container'>{l}</div>" for l in logs]), unsafe_allow_html=True)
        time.sleep(1)

    add_log("Agent Initialized: Senior Retention Strategist activated.")
    add_log("Action 1: Querying database for recent transactions...")
    
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    
    add_log(f"Data Ingested: {len(df)} customer records retrieved.")
    add_log("Calculating RFM scores for the customer base...")
    
    # Simulate tool call: segment_customers
    add_log("Action 2: Running Categorization Model (MCP: segment_customers)...")
    
    # Internal segmentation logic for simulation
    today = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    df['recency'] = (today - df['last_purchase_date']).dt.days
    
    segments = []
    for idx, row in df.iterrows():
        # Updated strictly for 4 segments
        if row['recency'] <= 30 and row['purchase_count'] >= 10 and row['total_spend'] >= 1000:
            segment = "Champions"
        elif row['total_spend'] >= 1500:
            segment = "Big Spenders"
        elif row['recency'] > 60:  # Catch-all for older inactive users
            segment = "At Risk"
        else:
            segment = "Loyal"      # Default fallback for active, regular users
        
        segments.append(segment)
        conn.execute("UPDATE customers SET segment = ? WHERE customer_id = ?", (segment, row['customer_id']))
    
    conn.commit()
    add_log("Segmentation Complete: 4 distinct segments identified.")
    
    # Action 3: Autonomous Execution
    add_log("Action 3: Executing Targeted Retention Strategies...")
    
    at_risk = df[df['recency'] > 90]
    for idx, row in at_risk.head(5).iterrows():
        code = f"WINBACK20-{idx}X99"
        conn.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, row['customer_id']))
        add_log(f"Tool Call: generate_discount_code(id={row['customer_id']}) -> {code}", "action")
        
    big_spenders = df[df['total_spend'] >= 1500]
    for idx, row in big_spenders.head(3).iterrows():
        conn.execute("UPDATE customers SET vip_flag = 1 WHERE customer_id = ?", (row['customer_id'],))
        add_log(f"Tool Call: flag_vip_customer(id={row['customer_id']}) -> Success", "action")

    conn.commit()
    conn.close()
    add_log("Pipeline Run Finished. Database updated.", "success")
    st.balloons()
    time.sleep(1)
    st.rerun()

# --- UI LAYOUT ---

st.markdown("<h1 class='main-header'>Customer Retention Agent</h1>", unsafe_allow_html=True)
st.markdown("<p class='sub-header'>Powered by Model Context Protocol (MCP) & Gemini Agent Builder</p>", unsafe_allow_html=True)

df = load_data()

# Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/robot-3.png", width=100)
    st.title("Control Center")
    if st.button("🚀 Run Daily Retention Pipeline"):
        st.session_state.running = True
    
    st.divider()
    st.info("The agent will automatically analyze segments and take win-back actions.")

# Top Metrics
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"<div class='metric-card'><h3>Total Customers</h3><h2>{len(df)}</h2></div>", unsafe_allow_html=True)
with col2:
    at_risk_count = len(df[df['segment'] == 'At Risk'])
    st.markdown(f"<div class='metric-card'><h3>At Risk</h3><h2 style='color: #FF4D4D;'>{at_risk_count}</h2></div>", unsafe_allow_html=True)
with col3:
    champions_count = len(df[df['segment'] == 'Champions'])
    st.markdown(f"<div class='metric-card'><h3>Champions</h3><h2 style='color: #4DFF88;'>{champions_count}</h2></div>", unsafe_allow_html=True)
with col4:
    revenue = f"${df['total_spend'].sum():,.0f}"
    st.markdown(f"<div class='metric-card'><h3>Total Revenue</h3><h2>{revenue}</h2></div>", unsafe_allow_html=True)

st.write("---")

# Main Content
tab1, tab2, tab3 = st.tabs(["📊 Segmentation Analytics", "👥 Customer Database", "🧠 Agent Thought Process"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(df, names='segment', title='Customer Segments Distribution', 
                     color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig, width='stretch')
    
    with c2:
        fig2 = px.scatter(df, x='purchase_count', y='total_spend', color='segment',
                         size='total_spend', hover_name='name', title='Spend vs Frequency by Segment')
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig2, width='stretch')

with tab2:
    st.dataframe(df.style.background_gradient(subset=['total_spend'], cmap='Purples'), width='stretch')

with tab3:
    log_area = st.empty()
    if 'running' in st.session_state and st.session_state.running:
        run_retention_pipeline()
        del st.session_state.running
    else:
        st.write("Waiting for agent activation... Click 'Run Daily Retention Pipeline' to start.")

# Footer
st.markdown("<br><p style='text-align: center; color: #5A189A;'>Hackathon Prototype - Customer Retention Agent v1.0</p>", unsafe_allow_html=True)
