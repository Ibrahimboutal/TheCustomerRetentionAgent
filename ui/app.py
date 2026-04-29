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
    
    .customer-success-voice {
        color: #4DFF88;
        font-weight: bold;
        border-bottom: 1px solid #4DFF88;
    }
    
    .cfo-voice {
        color: #FF4D4D;
        font-weight: bold;
        border-bottom: 1px solid #FF4D4D;
    }

    .orchestrator-voice {
        color: #FFD700;
        font-weight: bold;
        border-bottom: 1px solid #FFD700;
    }
</style>
""", unsafe_allow_html=True)

import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")

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
    
    # Removed the dead button and replaced it with a live status monitor
    st.markdown("""
    <div style='background-color: rgba(77, 255, 136, 0.1); border: 1px solid #4DFF88; padding: 10px; border-radius: 5px; text-align: center;'>
        <h4 style='color: #4DFF88; margin: 0;'>🟢 System Online</h4>
        <small style='color: #E0AAFF;'>Awaiting Agent Commands via MCP</small>
    </div>
    """, unsafe_allow_html=True)
    
    st.divider()
    st.info("The Gemini Agent operates autonomously from the Google Cloud Console. Watch this dashboard update in real-time as the Agent executes its strategy.")

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
    revenue = f"${df['TotalCharges'].sum():,.0f}"
    st.markdown(f"<div class='metric-card'><h3>Total Revenue</h3><h2>{revenue}</h2></div>", unsafe_allow_html=True)

st.write("---")

# Main Content
tab1, tab2, tab3, tab4 = st.tabs(["📊 Segmentation Analytics", "👥 Customer Database", "🧠 Agent Thought Process", "🔐 Approval Queue"])

with tab1:
    c1, c2 = st.columns(2)
    with c1:
        fig = px.pie(df, names='segment', title='Customer Segments Distribution', 
                     color_discrete_sequence=px.colors.qualitative.Prism)
        fig.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig, width='stretch')
    
    with c2:
        fig2 = px.scatter(df, x='tenure', y='TotalCharges', color='segment',
                         size='TotalCharges', hover_name='name', title='LTV vs Tenure by Segment')
        fig2.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig2, width='stretch')

    st.markdown("---")
    st.subheader("📈 Business Impact Projection (Monte Carlo Simulation)")
    col_a, col_b = st.columns([2, 1])
    
    with col_a:
        roi_data = pd.DataFrame({
            "Scenario": ["Control (10% Blast)", "Agent (ML + RAG)"],
            "Net Revenue Retained": [43100, 134800],
            "Customers Saved": [49, 152]
        })
        fig_roi = px.bar(roi_data, x="Scenario", y="Net Revenue Retained", 
                         color="Scenario", text_auto='.2s',
                         title="Projected Net Revenue Retained ($)")
        fig_roi.update_layout(paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font_color="#E0AAFF")
        st.plotly_chart(fig_roi, use_container_width=True)
        
    with col_b:
        st.info("**Simulation Assumptions:**")
        st.write("- **Intervention Lift:** +12% absolute improvement in save rate.")
        st.write("- **Precision:** ML prevents 40% discount waste on 'Sure Things'.")
        st.write("- **Personalization:** RAG-driven empathy reduces 'Sleeping Dog' risk.")
        st.success("**Projected Lift: +212% Net Revenue**")

with tab2:
    st.dataframe(df.style.background_gradient(subset=['TotalCharges'], cmap='Purples'), width='stretch')

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
            
            # Handle Boardroom Debate Transcript
            if "transcript" in content and "initiate_boardroom_debate" in row['tool_name']:
                try:
                    # Parse the result string if it's a string representation of a dict
                    if isinstance(content, str):
                        import ast
                        result_dict = ast.literal_eval(content)
                    else:
                        result_dict = content
                    
                    transcript = result_dict.get('transcript', [])
                    debate_html = "<div style='margin-top: 10px; border-left: 2px solid #7B2CBF; padding-left: 15px;'>"
                    for entry in transcript:
                        agent = entry['agent']
                        text = entry['text']
                        voice_class = "orchestrator-voice"
                        if "Success" in agent: voice_class = "customer-success-voice"
                        elif "CFO" in agent: voice_class = "cfo-voice"
                        
                        debate_html += f"<p><span class='{voice_class}'>{agent}:</span> {text}</p>"
                    debate_html += "</div>"
                    content = debate_html
                except Exception as e:
                    content = f"Error rendering debate: {e}<br>{content}"
            else:
                # Fallback for other tools or legacy logs
                content = content.replace("Marketing:", "<span class='customer-success-voice'>Marketing:</span>")
                content = content.replace("Finance:", "<span class='cfo-voice'>Finance:</span>")
            
            st.markdown(f"""
            <div class='log-container'>
                <span style='color: #9D4EDD;'>[{row['timestamp']}]</span> 
                <b>{row['tool_name']}</b><br>
                <small>Args: {row['arguments']}</small><br>
                <div style='color: #E0AAFF;'>Result: {content}</div>
            </div>
            """, unsafe_allow_html=True)

with tab4:
    st.markdown("### 🔐 Pending Budget Approvals")
    st.info("The AI Agent has paused and is requesting budget for high-value discounts.")
    
    conn = sqlite3.connect(DB_PATH)
    approvals_df = pd.read_sql_query("""
        SELECT a.id, c.name, a.requested_amount, a.status, a.timestamp 
        FROM approvals a 
        JOIN customers c ON a.customer_id = c.customer_id
        WHERE a.status = 'pending'
        ORDER BY a.timestamp DESC
    """, conn)
    
    if approvals_df.empty:
        st.success("No pending approvals. The agent is free to execute standard strategies.")
    else:
        for idx, row in approvals_df.iterrows():
            col_a, col_b, col_c = st.columns([2, 1, 1])
            with col_a:
                st.markdown(f"**{row['name']}** requested **${row['requested_amount']}**")
                st.caption(f"Request ID: {row['id']} | Time: {row['timestamp']}")
            with col_b:
                if st.button(f"✅ Approve #{row['id']}", key=f"app_{row['id']}"):
                    conn.execute("UPDATE approvals SET status = 'approved' WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.toast(f"Budget approved for {row['name']}!")
                    st.rerun()
            with col_c:
                if st.button(f"❌ Reject #{row['id']}", key=f"rej_{row['id']}"):
                    conn.execute("UPDATE approvals SET status = 'rejected' WHERE id = ?", (row['id'],))
                    conn.commit()
                    st.toast(f"Budget rejected for {row['name']}.")
                    st.rerun()
            st.divider()
    conn.close()

# Footer
st.markdown("<br><p style='text-align: center; color: #5A189A;'>Hackathon Prototype - Customer Retention Agent v1.0</p>", unsafe_allow_html=True)
