from fastapi import FastAPI, Response, Request
import sqlite3
import pandas as pd
from datetime import datetime, timedelta
import random
import string
import json
import requests
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# Initialize FastAPI app
app = FastAPI(title="Retention CRM MCP Server", version="1.0.0")

DB_PATH = "mock_crm.db"

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
    
    # Add a mock ML churn probability score for the agent
    # Heuristic: Probability increases with recency (max 180 days in mock data)
    today = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    df['recency'] = (today - df['last_purchase_date']).dt.days
    df['churn_probability'] = df['recency'].apply(lambda x: min(100, round((x / 180) * 100, 1)))
    
    return df.to_dict(orient="records")

def segment_customers_logic():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    
    if df.empty:
        conn.close()
        return {"status": "error", "message": "No customers to segment"}

    # Prepare data for K-Means (RFM features)
    today = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    df['recency'] = (today - df['last_purchase_date']).dt.days
    
    # Features: Recency, Frequency (purchase_count), Monetary (total_spend)
    features = df[['recency', 'purchase_count', 'total_spend']]
    
    # Scale features
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)
    
    # Run K-Means
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(scaled_features)
    
    # Map clusters to meaningful names based on cluster centroids
    # Heuristic: Find center with highest spend for Champions, etc.
    centers = kmeans.cluster_centers_
    # centers[i] = [recency, count, spend] (scaled)
    # Champions: Low recency, High count, High spend
    # At Risk: High recency, Low count, Low spend
    
    # For simplicity in a live demo, we'll sort clusters by spend/count and assign
    cluster_means = df.groupby('cluster')[['recency', 'purchase_count', 'total_spend']].mean()
    
    # Logic to assign segment names to cluster IDs
    mapping = {}
    
    # 1. At Risk (Highest Recency)
    at_risk_cluster = cluster_means['recency'].idxmax()
    mapping[at_risk_cluster] = "At Risk"
    
    # 2. Champions (Highest Purchase Count among the remaining)
    remaining = cluster_means.drop(at_risk_cluster)
    champions_cluster = remaining['purchase_count'].idxmax()
    mapping[champions_cluster] = "Champions"
    
    # 3. Big Spenders (Highest Total Spend among the remaining)
    remaining = remaining.drop(champions_cluster)
    big_spenders_cluster = remaining['total_spend'].idxmax()
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

def generate_discount_code(customer_id: int):
    code = "WINBACK20-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Update customer record
    cursor.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, customer_id))
    
    # Log to promotion history
    today = datetime.now().strftime('%Y-%m-%d')
    cursor.execute(
        "INSERT INTO promotion_history (customer_id, promotion_type, date_issued) VALUES (?, ?, ?)",
        (customer_id, "20% Winback", today)
    )
    
    conn.commit()
    conn.close()
    return {"status": "success", "customer_id": customer_id, "code": code}

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
    """Causal Inference: Determine the causal impact of a discount."""
    # Heuristic based on recency and past behavior
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT recency, purchase_count FROM customers WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row: return {"error": "Customer not found"}
    recency, count = row
    
    # Causal Heuristic
    if recency > 90 and count < 3:
        quadrant = "Lost Causes"
        advice = "Low probability of retention. Do not waste budget."
    elif recency <= 30:
        quadrant = "Sure Things"
        advice = "Will stay anyway. Offering a discount reduces margins unnecessarily."
    elif 30 < recency <= 90:
        quadrant = "Persuadables"
        advice = "High Causal Uplift! A discount here is likely to prevent churn."
    else:
        quadrant = "Sleeping Dogs"
        advice = "Risky. Contacting them might remind them to cancel."
        
    return {"customer_id": customer_id, "uplift_quadrant": quadrant, "recommendation": advice}

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
    df = pd.read_sql_query("SELECT total_spend FROM customers WHERE segment = ?", conn, params=(segment,))
    conn.close()
    
    if df.empty:
        return {"error": f"No customers found in segment '{segment}'"}
    
    baseline = df['total_spend'].sum()
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
                        "name": "segment_customers",
                        "description": "Categorize customers into Champions, Big Spenders, At Risk, or Loyal",
                        "inputSchema": {"type": "object", "properties": {}}
                    },
                    {
                        "name": "generate_discount",
                        "description": "Generate a 20% win-back code for a specific customer",
                        "inputSchema": {
                            "type": "object",
                            "properties": {"customer_id": {"type": "integer"}},
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
        elif tool_name == "segment_customers":
            result = segment_customers_logic()
        elif tool_name == "generate_discount":
            result = generate_discount_code(args.get("customer_id"))
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