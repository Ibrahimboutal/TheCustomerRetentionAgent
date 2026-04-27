# 🤖 Customer Retention Agent

A professional-grade AI agent system designed to automate customer retention using the **Model Context Protocol (MCP)** and **Google Cloud Agent Builder**. This project identifies high-value and at-risk customers from a CRM database and executes autonomous retention strategies.

## 🏗️ Architecture

1.  **Environment (Mock CRM)**: A SQLite database (`mock_crm.db`) containing transaction history and customer segments.
2.  **Superpower (MCP Server)**: A FastAPI-powered MCP server (`server.py`) that exposes data-querying and action-taking tools to the AI.
3.  **Brain (Google Cloud Agent)**: A Gemini-powered agent configured to analyze segments and trigger retention actions.
4.  **UI Dashboard**: A premium Streamlit interface (`app.py`) for monitoring the agent's thought process and database state.

## 🚀 Features

-   **RFM Analysis**: Automatically calculates Recency, Frequency, and Monetary scores.
-   **Strict Segmentation**: Classifies users into 4 key segments: *Champions*, *Loyal*, *Big Spenders*, and *At Risk*.
-   **Autonomous Actions**:
    -   Generates unique **20% win-back codes** for "At Risk" users.
    -   Flags "Big Spenders" as **VIPs** for early product access.
-   **Real-time Monitoring**: Premium dark-mode dashboard with interactive Plotly visualizations.

## 🛠️ Setup Instructions

### 1. Prerequisites
- Python 3.10+
- `pip install fastapi uvicorn pandas plotly streamlit mcp`

### 2. Initialize the CRM
Seed the database with mock customer data:
```bash
python crm_init.py
```

### 3. Run the MCP Server
Start the FastAPI server (Default port 8000):
```bash
uvicorn server:app --port 8000
```

### 4. Expose for Google Cloud (Demo Only)
If testing with Google Cloud Agent Builder locally, use ngrok to create a public tunnel:
```bash
ngrok http 8000
```

### 5. Launch the Dashboard
Monitor the CRM and trigger the retention pipeline:
```bash
streamlit run app.py
```

## 🧠 Agent Configuration

To connect this to **Google Cloud Agent Builder**:
1.  **Tools**: Add a new MCP tool pointing to your ngrok URL.
2.  **Goal**: "You are a Senior Retention Strategist. Your goal is to analyze customer data daily, identify segments, and take immediate action to retain them."
3.  **Instructions**: "Use `get_customers` to see the base, `segment_customers` to categorize them, and then use `generate_discount` or `flag_vip` based on the classification."

---
*Created for the Hackathon - Automating Retention with Agentic AI.*
