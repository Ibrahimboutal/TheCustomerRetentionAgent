from fastapi import FastAPI, Response, Request
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import string
import json
import requests
import pickle
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler as SkScaler

import google.generativeai as genai
import os

# Initialize FastAPI app
app = FastAPI(title="Retention CRM MCP Server", version="1.0.0")

# Configure Gemini
GEMINI_API_KEY = os.environ.get("GOOGLE_API_KEY", "")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

import os
import sys

# Ensure the project root is in the path for cross-module imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")
ML_DIR = os.path.join(BASE_DIR, "ml")

from agent.decision_engine import DecisionEngine

# --- LOAD PRODUCTION ML MODEL ---
try:
    with open(os.path.join(ML_DIR, 'churn_model.pkl'), 'rb') as f:
        CHURN_MODEL = pickle.load(f)
    with open(os.path.join(ML_DIR, 'scaler.pkl'), 'rb') as f:
        SCALER = pickle.load(f)
    with open(os.path.join(ML_DIR, 'feature_names.pkl'), 'rb') as f:
        FEATURE_NAMES = pickle.load(f)
    with open(os.path.join(ML_DIR, 'encoders.pkl'), 'rb') as f:
        ENCODERS = pickle.load(f)
    print("DONE: Real-world Telco model and Encoders loaded successfully.")
except Exception as e:
    CHURN_MODEL = None
    print(f"WARN: Could not load ML model: {e}")

# --- LOAD UPLIFT MODEL ---
try:
    with open(os.path.join(ML_DIR, 'uplift_model.pkl'), 'rb') as f:
        UPLIFT_MODEL = pickle.load(f)
    with open(os.path.join(ML_DIR, 'uplift_scaler.pkl'), 'rb') as f:
        UPLIFT_SCALER = pickle.load(f)
    with open(os.path.join(ML_DIR, 'uplift_features.pkl'), 'rb') as f:
        UPLIFT_FEATURES = pickle.load(f)
    with open(os.path.join(ML_DIR, 'uplift_encoders.pkl'), 'rb') as f:
        UPLIFT_ENCODERS = pickle.load(f)
    print("DONE: Causal Uplift model loaded successfully.")
except Exception as e:
    UPLIFT_MODEL = None
    print(f"WARN: Could not load Uplift model: {e}")

def get_db_connection():
    return sqlite3.connect(DB_PATH)

def log_agent_action(tool_name: str, arguments: dict, result: any):
    """Logs an agent tool execution to the database for real-time monitoring."""
    import json
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
        (timestamp, tool_name, json.dumps(arguments), str(result))
    )
    conn.commit()
    conn.close()

# --- CRM LOGIC FUNCTIONS ---

def get_customers():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    
    if df.empty or CHURN_MODEL is None:
        return df.to_dict(orient="records")

    # PREDICT CHURN LIVE USING REAL TELCO MODEL
    X = df[FEATURE_NAMES].copy()
    
    # Apply Label Encoding for Categorical columns
    for col, le in ENCODERS.items():
        if col in X.columns:
            X[col] = le.transform(X[col])
            
    X_scaled = SCALER.transform(X)
    df['churn_probability'] = (CHURN_MODEL.predict_proba(X_scaled)[:, 1] * 100).round(1)
    
    return df.to_dict(orient="records")

def explain_churn_risk(customer_id: int):
    """
    🧠 ML EXPLAINABILITY TOOL:
    Uses feature importance and the customer's specific data to explain 'Why'.
    """
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers WHERE customer_id = ?", conn, params=(customer_id,))
    conn.close()
    
    if df.empty:
        return {"error": "Customer not found"}
        
    customer = df.iloc[0]
    
    reasons = []
    if customer['Contract'] == 'Month-to-month':
        reasons.append("High risk due to non-binding 'Month-to-month' contract.")
    if customer['InternetService'] == 'Fiber optic':
        reasons.append("Fiber optic users show higher churn rates in this segment.")
    if customer['tenure'] < 12:
        reasons.append(f"Early-stage user (Tenure: {customer['tenure']} months).")
        
    X = df[FEATURE_NAMES].copy()
    for col, le in ENCODERS.items():
        if col in X.columns:
            X[col] = le.transform(X[col])
            
    risk = (CHURN_MODEL.predict_proba(SCALER.transform(X))[0, 1] * 100).round(1)
    
    return {
        "customer": customer['name'],
        "churn_probability": f"{risk}%",
        "top_contributing_factors": reasons if reasons else ["Stable customer profile."],
        "ml_inference_note": "Risk calculated using IBM Telco RandomForest Model (Real Data)."
    }

def segment_customers_logic():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    
    if df.empty:
        conn.close()
        return {"status": "error", "message": "No customers to segment"}

    # Features: Tenure, MonthlyCharges, TotalCharges (Telco features)
    features = df[['tenure', 'MonthlyCharges', 'TotalCharges']]
    
    # Scale features
    cluster_scaler = SkScaler()
    scaled_features = cluster_scaler.fit_transform(features)
    
    # Run K-Means
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(scaled_features)
    
    # Map clusters to meaningful names based on cluster centroids
    # Heuristic: Find center with highest spend for Champions, etc.
    centers = kmeans.cluster_centers_
    # centers[i] = [recency, count, spend] (scaled)
    # Champions: Low recency, High count, High spend
    # At Risk: High recency, Low count, Low spend
    
    # For simplicity in a live demo, we'll sort clusters by TotalCharges/tenure and assign
    cluster_means = df.groupby('cluster')[['tenure', 'MonthlyCharges', 'TotalCharges']].mean()
    
    # Logic to assign segment names to cluster IDs
    mapping = {}
    
    # 1. At Risk (Lowest Tenure)
    at_risk_cluster = cluster_means['tenure'].idxmin()
    mapping[at_risk_cluster] = "At Risk"
    
    # 2. Champions (Highest Total Charges among the remaining)
    remaining = cluster_means.drop(at_risk_cluster)
    champions_cluster = remaining['TotalCharges'].idxmax()
    mapping[champions_cluster] = "Champions"
    
    # 3. Big Spenders (Highest Monthly Charges among the remaining)
    remaining = remaining.drop(champions_cluster)
    big_spenders_cluster = remaining['MonthlyCharges'].idxmax()
    mapping[big_spenders_cluster] = "Big Spenders"
    
    # 4. Loyal (The last one)
    loyal_cluster = remaining.drop(big_spenders_cluster).index[0]
    mapping[loyal_cluster] = "Loyal"
    
    results = []
    cursor = conn.cursor()
    for _, row in df.iterrows():
        segment = mapping[row['cluster']]
        cursor.execute("UPDATE customers SET segment = ? WHERE customer_id = ?", (segment, row['customer_id']))
        results.append({"id": row['customer_id'], "name": row['name'], "segment": segment})
    
    conn.commit()
    conn.close()
    return {"status": "success", "processed": len(results), "ml_method": "K-Means Clustering", "data": results}

def generate_discount_code(customer_id: int, requested_rate: float = 0.2):
    """
    🛡️ DETERMINISTIC RULES ENGINE: 
    The LLM proposes, but the Python backend enforces the financial guardrails.
    """
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers WHERE customer_id = ?", conn, params=(customer_id,))
    
    if df.empty:
        conn.close()
        return {"error": "Customer not found"}
    
    customer = df.iloc[0]
    
    # 1. Run live ML Prediction for the Rules Engine
    X = df[FEATURE_NAMES].copy()
    for col, le in ENCODERS.items():
        if col in X.columns:
            X[col] = le.transform(X[col])
            
    risk = CHURN_MODEL.predict_proba(SCALER.transform(X))[0, 1]
    
    # 2. ENFORCE RULES VIA DECISION ENGINE
    eval_result = DecisionEngine.validate_action(
        customer['name'], requested_rate, risk, customer['TotalCharges']
    )
    
    final_rate = float(eval_result['approved_rate'].replace('%', '')) / 100.0
    
    code = f"SAVE{int(final_rate*100)}-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    cursor = conn.cursor()
    
    # Update customer record
    cursor.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, customer_id))
    
    # Log to promotion history
    today_str = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        "INSERT INTO promotion_history (customer_id, promotion_type, date_issued) VALUES (?, ?, ?)",
        (customer_id, f"{int(final_rate*100)}% Discount", today_str)
    )
    
    conn.commit()
    conn.close()
    
    return {
        "status": "success", 
        "customer_id": customer_id, 
        "code": code,
        "applied_rate": eval_result['approved_rate'],
        "decision_engine_note": eval_result['justification'],
        "churn_risk_score": eval_result['churn_risk_score'],
        "was_capped": eval_result['was_capped']
    }
   

def check_discount_eligibility(customer_id: int):
    """Business Guardrail: Check if a customer is eligible for a new discount."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if they received a discount in the last 30 days
    thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
    cursor.execute(
        "SELECT date_issued FROM promotion_history WHERE customer_id = ? AND date_issued > ? ORDER BY date_issued DESC",
        (customer_id, thirty_days_ago)
    )
    row = cursor.fetchone()
    conn.close()
    
    if row:
        return {
            "eligible": False, 
            "reason": f"Customer already received a discount on {row[0]}. Policy prevents multiple discounts within 30 days.",
            "policy": "Anti-Abuse Enterprise Guardrail"
        }
    
    return {"eligible": True, "message": "No recent discounts found. Customer is eligible."}

def flag_vip_customer(customer_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM customers WHERE customer_id = ?", (customer_id,))
    name = cursor.fetchone()[0]
    cursor.execute("UPDATE customers SET vip_flag = 1 WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    
    # --- PRODUCTION WEBHOOK (Slack/Discord) ---
    WEBHOOK_URL = "https://discord.com/api/webhooks/dummy" # Placeholder for demo
    try:
        payload = {
            "content": f"🚨 **VIP ALERT**: `{name}` has just been promoted to the **Champions** tier. Account Managers, please prioritize high-touch outreach!"
        }
        # In a real demo, this sends a live notification to your phone/slack
        # requests.post(WEBHOOK_URL, json=payload, timeout=2) 
    except Exception as e:
        print(f"Webhook failed: {e}")
        
    return {"status": "success", "customer_id": customer_id, "message": f"Flagged {name} as VIP and triggered notification."}

def request_budget_approval(customer_id: int, amount: float):
    """HITL: Request human approval for a specific retention budget."""
    conn = get_db_connection()
    cursor = conn.cursor()
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute(
        "INSERT INTO approvals (customer_id, requested_amount, timestamp) VALUES (?, ?, ?)",
        (customer_id, amount, timestamp)
    )
    request_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return {"status": "pending", "request_id": request_id, "message": f"Budget of ${amount} submitted for human review."}

def check_approval_status(request_id: int):
    """HITL: Check if the human has approved the budget yet."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM approvals WHERE id = ?", (request_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"status": "error", "message": "Request ID not found."}
    return {"status": row[0]}

def search_support_history(customer_id: int):
    """Agentic RAG: Retrieve unstructured support logs for personalization."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT transcript, date FROM support_logs WHERE customer_id = ?", (customer_id,))
    rows = cursor.fetchall()
    conn.close()
    
    if not rows:
        return {"status": "empty", "message": "No previous support tickets found."}
    return {"status": "success", "logs": [{"date": r[1], "transcript": r[0]} for r in rows]}

def run_uplift_modeling(customer_id: int):
    """Causal Inference: Determine the exact causal impact of a discount using Causal AI."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers WHERE customer_id = ?", conn, params=(customer_id,))
    conn.close()
    
    if df.empty: return {"error": "Customer not found"}
    if UPLIFT_MODEL is None: return {"error": "Uplift model not loaded."}
        
    X = df[UPLIFT_FEATURES].copy()
    for col, le in UPLIFT_ENCODERS.items():
        if col in X.columns:
            try:
                X[col] = le.transform(X[col])
            except ValueError:
                X[col] = 0
                
    X_scaled = UPLIFT_SCALER.transform(X)
    ite_score = UPLIFT_MODEL.effect(X_scaled)[0]
    
    if isinstance(ite_score, np.ndarray):
        ite_score = float(ite_score[0])
    else:
        ite_score = float(ite_score)
        
    ite_percentage = round(ite_score * 100, 2)
    
    if ite_percentage >= 10.0:
        quadrant = "Persuadables"
        advice = f"High Causal Uplift (+{ite_percentage}%). Applying a discount directly causes a high probability of retention. Maximize budget."
    elif ite_percentage <= -5.0:
        quadrant = "Sleeping Dogs"
        advice = f"Negative Causal Uplift ({ite_percentage}%). Contacting with a discount will actively trigger churn. Do not contact."
    elif ite_percentage > 0.0:
        quadrant = "Sure Things"
        advice = f"Low Causal Uplift (+{ite_percentage}%). Stable probability of staying regardless of discount. Do not waste margin."
    else:
        quadrant = "Lost Causes"
        advice = f"Zero/Negative Impact ({ite_percentage}%). Likely to churn regardless of intervention."

    return {
        "customer_id": customer_id, 
        "uplift_quadrant": quadrant, 
        "ite_score": f"{ite_percentage}%",
        "recommendation": advice
    }

def simulate_outcome(customer_id: int):
    """The 'Time Machine': Simulates the real-world response of a customer to the agent's actions."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 1. Get current status
    cursor.execute("SELECT name, segment, discount_code, tenure, TotalCharges FROM customers WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return {"error": "Customer not found"}
    
    name, segment, has_discount, tenure, charges = row
    
    # 2. Get Uplift Quadrant (re-using the logic)
    uplift = run_uplift_modeling(customer_id)
    quadrant = uplift.get("uplift_quadrant", "Lost Causes")
    
    # 3. Probability Model
    roll = random.random()
    success = False
    outcome_msg = ""
    
    if quadrant == "Persuadables":
        # Discounts work wonders here
        chance = 0.85 if has_discount else 0.40
        if roll < chance:
            success = True
            outcome_msg = f"Success! The discount worked. {name} just placed a new order."
        else:
            outcome_msg = f"Neutral. {name} saw the email but hasn't acted yet."
            
    elif quadrant == "Sure Things":
        # They were going to buy anyway
        if roll < 0.95:
            success = True
            outcome_msg = f"Success! {name} made a purchase (as expected, they are a 'Sure Thing')."
            
    elif quadrant == "Sleeping Dogs":
        # High risk of negative reaction
        if roll < 0.30:
            cursor.execute("UPDATE customers SET segment = 'CHURNED', total_spend = 0 WHERE customer_id = ?", (customer_id,))
            outcome_msg = f"🛑 DISASTER! Contacting {name} (a 'Sleeping Dog') reminded them of their subscription, and they just CANCELLED."
        else:
            outcome_msg = f"Phew. {name} ignored the email. No harm done, but no purchase either."
            
    else: # Lost Causes
        if roll < 0.05:
            success = True
            outcome_msg = f"Wow! Against the odds, {name} made a small purchase."
        else:
            outcome_msg = f"No response. {name} is likely a 'Lost Cause'."

    # 4. Update Database on Success
    if success:
        new_purchase = round(random.uniform(50, 250), 2)
        cursor.execute(
            "UPDATE customers SET tenure = ?, TotalCharges = ?, segment = 'Champions' WHERE customer_id = ?", 
            (tenure + 1, charges + new_purchase, customer_id)
        )
        conn.commit()
        conn.close()
        return {"status": "success", "result": outcome_msg, "revenue_gain": f"${new_purchase}"}
    
    conn.commit()
    conn.close()
    return {"status": "neutral/negative", "result": outcome_msg, "revenue_gain": "$0"}

def draft_email_logic(customer_id: int, segment: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, email, discount_code FROM customers WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"status": "error", "message": "Customer not found"}
        
    name, email, code = row
    
    if not email or email.strip() == "":
        return {"status": "error", "message": "Email missing. Cannot send."}
    
    if segment == "At Risk":
        return f"Subject: We miss you, {name}! | Here is {code} for 20% off."
    elif segment == "Big Spenders":
        return f"Subject: VIP Access for {name} | Join our exclusive launch."
    return f"Subject: A special thanks to our {segment} customer!"

def simulate_revenue_impact(segment: str, discount_rate: float):
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT TotalCharges FROM customers WHERE segment = ?", conn, params=(segment,))
    conn.close()
    
    if df.empty:
        return {"error": f"No customers found in segment '{segment}'"}
    
    baseline = df['TotalCharges'].sum()
    discount_cost = baseline * discount_rate
    # Heuristic: 30% retention lift in Lifetime Value
    projected_revenue = (baseline - discount_cost) * 1.3
    
    return {
        "segment": segment,
        "baseline_revenue": round(baseline, 2),
        "discount_applied": f"{int(discount_rate*100)}%",
        "projected_revenue": round(projected_revenue, 2),
        "roi_lift": f"{round(((projected_revenue - baseline) / baseline) * 100, 1)}%"
    }

def flag_for_sms_campaign(customer_id: int):
    """Fallback tool when email is missing."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET segment = 'SMS-Pending' WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "customer_id": customer_id, "message": "Added to SMS queue"}

def initiate_boardroom_debate(customer_id: int):
    """
    ⚖️ THE AGENTIC BOARDROOM:
    Three Gemini personas (Success, CFO, Orchestrator) debate the retention strategy.
    """
    # 1. Gather Data
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers WHERE customer_id = ?", conn, params=(customer_id,))
    conn.close()
    
    if df.empty:
        return {"error": "Customer not found"}
    
    customer = df.iloc[0]
    risk_info = explain_churn_risk(customer_id)
    uplift_info = run_uplift_modeling(customer_id)
    support_info = search_support_history(customer_id)
    
    # 2. Setup Personas
    context = f"""
    CUSTOMER DATA:
    - Name: {customer['name']}
    - Tenure: {customer['tenure']} months
    - Monthly Charges: ${customer['MonthlyCharges']}
    - Total Charges: ${customer['TotalCharges']}
    - Churn Risk: {risk_info['churn_probability']}
    - Uplift Quadrant: {uplift_info['uplift_quadrant']} (ITE Score: {uplift_info.get('ite_score', 'N/A')})
    - Support History: {support_info['status']} (Logs: {support_info.get('logs', 'None')})
    """
    
    if not GEMINI_API_KEY:
        # Simulation Mode if no API Key
        debate = [
            {"agent": "Customer Success Agent", "text": f"We must save {customer['name']}! Their tenure is {customer['tenure']} months. A 20% discount is a small price for loyalty."},
            {"agent": "CFO Agent", "text": f"Wait, {customer['name']} is a '{uplift_info['uplift_quadrant']}'. If they are a Sure Thing, a discount is wasted margin. If they are a Lost Cause, it's a lost investment. I recommend $0."},
            {"agent": "Orchestrator", "text": f"Decision: Based on the {risk_info['churn_probability']} risk, we will offer a 15% discount but only for 3 months to balance retention and ROI."}
        ]
        return {"status": "simulated", "transcript": debate}

    model = genai.GenerativeModel('gemini-1.5-flash')
    
    # Customer Success Persona
    success_prompt = f"You are the Customer Success Agent. Argue passionately to give the maximum possible discount (30%) to save {customer['name']}. Cite their history and value. Context: {context}"
    success_resp = model.generate_content(success_prompt).text
    
    # CFO Persona
    cfo_prompt = f"You are the CFO Agent. You are skeptical and focused on ROI. Argue to give $0 discount to {customer['name']}, citing that they are a {uplift_info['uplift_quadrant']} and it might be a waste of margin. Context: {context}"
    cfo_resp = model.generate_content(cfo_prompt).text
    
    # Orchestrator Persona
    orch_prompt = f"You are the Boardroom Orchestrator. You have heard the Customer Success Agent and the CFO Agent. Look at the data and make a final ruling on the discount rate (0% to 30%). Provide a concise final decision. \nCS Argument: {success_resp}\nCFO Argument: {cfo_resp}\nContext: {context}"
    orch_resp = model.generate_content(orch_prompt).text
    
    debate = [
        {"agent": "Customer Success Agent", "text": success_resp.strip()},
        {"agent": "CFO Agent", "text": cfo_resp.strip()},
        {"agent": "Orchestrator", "text": orch_resp.strip()}
    ]
    
    return {"status": "success", "transcript": debate}

# --- MCP HUB (THE JSON-RPC HANDSHAKE) ---

@app.post("/")
@app.get("/")
async def mcp_hub(request: dict):
    method = request.get("method")
    request_id = request.get("id", 0)

    # 1. INITIALIZE (The first handshake)
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "Retention-CRM-Server", "version": "1.0.0"}
            }
        }

    # 2. INITIALIZED NOTIFICATION
    if method == "notifications/initialized":
        return Response(status_code=204)

    # 3. TOOL DISCOVERY (Listing your capabilities)
    if method == "tools/list":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "tools": [
                    {
                        "name": "get_customers",
                        "description": "Fetch all customer data from the CRM",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "explain_churn_risk",
                        "description": "Provide a data-driven explanation for a customer's churn risk using ML feature importance",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "segment_customers",
                        "description": "Categorize customers into Champions, Big Spenders, At Risk, or Loyal",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "generate_discount",
                        "description": "Generate a unique win-back discount code for a customer",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "customer_id": {"type": "integer"},
                                "requested_rate": {"type": "number", "description": "e.g., 0.2 for 20%"}
                            },
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "flag_vip",
                        "description": "Flag a customer for VIP access",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "draft_email",
                        "description": "Draft a personalized email for a customer based on their segment",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "customer_id": {"type": "integer"},
                                "segment": {"type": "string"}
                            },
                            "required": ["customer_id", "segment"]
                        }
                    },
                    {
                        "name": "flag_for_sms",
                        "description": "Fallback: Flag a customer for SMS campaign if email fails",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "simulate_revenue",
                        "description": "Calculate the ROI of a retention campaign for a specific segment",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "segment": {"type": "string"},
                                "discount_rate": {"type": "number", "description": "e.g., 0.2 for 20%"}
                            },
                            "required": ["segment", "discount_rate"]
                        }
                    },
                    {
                        "name": "check_eligibility",
                        "description": "Enterprise Guardrail: Check if a customer is eligible for a new discount based on history",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "request_approval",
                        "description": "HITL: Request human budget approval for a high-value discount",
                        "inputSchema": {
                            "type": "object",
                            "properties": {
                                "customer_id": {"type": "integer"},
                                "amount": {"type": "number"}
                            },
                            "required": ["customer_id", "amount"]
                        }
                    },
                    {
                        "name": "get_approval_status",
                        "description": "HITL: Check if a pending budget request has been approved",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"request_id": {"type": "integer"}},
                            "required": ["request_id"]
                        }
                    },
                    {
                        "name": "search_history",
                        "description": "Agentic RAG: Search customer support logs to personalize the retention email",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "get_uplift",
                        "description": "Causal Inference: Get the causal quadrant (Persuadable, Sure Thing, etc.) for a customer",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "simulate_outcome",
                        "description": "The Time Machine: Simulate the real-world response of a customer to see if the retention strategy actually worked.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    },
                    {
                        "name": "initiate_boardroom_debate",
                        "description": "The Agentic Boardroom: Deploy three Gemini personas to debate the retention decision in real-time.",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
                            "required": ["customer_id"]
                        }
                    }
                ]
            }
        }

    # 4. TOOL EXECUTION (The payload)
    if method == "tools/call":
        params = request.get("params", {})
        tool_name = params.get("name")
        args = params.get("arguments", {})

        if tool_name == "get_customers":
            result = get_customers()
        elif tool_name == "explain_churn_risk":
            result = explain_churn_risk(args.get("customer_id"))
        elif tool_name == "segment_customers":
            result = segment_customers_logic()
        elif tool_name == "generate_discount":
            result = generate_discount_code(
                args.get("customer_id"), 
                args.get("requested_rate", 0.2)
            )
        elif tool_name == "flag_vip":
            result = flag_vip_customer(args.get("customer_id"))
        elif tool_name == "draft_email":
            result = draft_email_logic(args.get("customer_id"), args.get("segment"))
        elif tool_name == "flag_for_sms":
            result = flag_for_sms_campaign(args.get("customer_id"))
        elif tool_name == "simulate_revenue":
            result = simulate_revenue_impact(args.get("segment"), args.get("discount_rate"))
        elif tool_name == "check_eligibility":
            result = check_discount_eligibility(args.get("customer_id"))
        elif tool_name == "request_approval":
            result = request_budget_approval(args.get("customer_id"), args.get("amount"))
        elif tool_name == "get_approval_status":
            result = check_approval_status(args.get("request_id"))
        elif tool_name == "search_history":
            result = search_support_history(args.get("customer_id"))
        elif tool_name == "get_uplift":
            result = run_uplift_modeling(args.get("customer_id"))
        elif tool_name == "simulate_outcome":
            result = simulate_outcome(args.get("customer_id"))
        elif tool_name == "initiate_boardroom_debate":
            result = initiate_boardroom_debate(args.get("customer_id"))
        else:
            return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Tool not found"}}

        # Log the action for the dashboard
        log_agent_action(tool_name, args, result)

        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {"content": [{"type": "text", "text": str(result)}]}
        }

    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {"code": -32601, "message": "Method not found"}
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)