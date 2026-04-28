import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import time
from datetime import datetime
from streamlit_autorefresh import st_autorefresh

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
        line-height: 1.4;
    }
    
    .marketing-voice {
        color: #FF79C6;
        font-weight: bold;
        border-bottom: 1px solid #FF79C6;
    }
    
    .finance-voice {
        color: #F1FA8C;
        font-weight: bold;
        border-bottom: 1px solid #F1FA8C;
    }
</style>
""", unsafe_allow_html=True)

DB_PATH = "mock_crm.db"

def load_data():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df

def fetch_agent_logs():
    conn = sqlite3.connect(DB_PATH)
    logs = pd.read_sql_query("SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT 20", conn)
    conn.close()
    return logs

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

    st.write("### 💰 ROI Projection: AI Retention Strategy")
    # Heuristic calculation for the chart
    at_risk_revenue = df[df['segment'] == 'At Risk']['total_spend'].sum()
    if at_risk_revenue > 0:
        roi_data = pd.DataFrame({
            'Category': ['Current Revenue', 'Projected (With AI)'],
            'Amount': [at_risk_revenue, at_risk_revenue * 1.3]
        })
        fig3 = px.bar(roi_data, x='Category', y='Amount', color='Category',
                     title='Projected ROI for "At Risk" Segment (30% Lift)',
                     color_discrete_map={'Current Revenue': '#7B2CBF', 'Projected (With AI)': '#4DFF88'})
        fig3.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig3, width='stretch')
    else:
        st.info("Run the segmentation to see ROI projections.")

with tab2:
    st.dataframe(df.style.background_gradient(subset=['total_spend'], cmap='Purples'), width='stretch')

with tab3:
    st.markdown("### 📡 Live Agent Feed")
    # Refreshes the page every 5 seconds automatically for the live feed
    st_autorefresh(interval=5000, key="agent_feed_refresh")
    
    st.info("Showing real-world actions taken by the Google AI Agent via the MCP Server.")
    
    if st.button("🔄 Refresh Live Feed"):
        st.rerun()

    agent_logs = fetch_agent_logs()
    if agent_logs.empty:
        st.write("No agent activity recorded yet. Waiting for Google AI Agent to call tools...")
    else:
        for idx, row in agent_logs.iterrows():
            content = row['result']
            # Highlight boardroom debate voices
            content = content.replace("Marketing:", "<span class='marketing-voice'>Marketing:</span>")
            content = content.replace("Finance:", "<span class='finance-voice'>Finance:</span>")
            
            st.markdown(f"""
            <div class='log-container'>
                <span style='color: #9D4EDD;'>[{row['timestamp']}]</span> 
                <b>{row['tool_name']}</b><br>
                <small>Args: {row['arguments']}</small><br>
                <span style='color: #4DFF88;'>Result: {content}</span>
            </div>
            """, unsafe_allow_html=True)

# Footer
st.markdown("<br><p style='text-align: center; color: #5A189A;'>Hackathon Prototype - Customer Retention Agent v1.0</p>", unsafe_allow_html=True)
