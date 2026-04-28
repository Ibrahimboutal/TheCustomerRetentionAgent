from fastapi import FastAPI, Response, Request
import sqlite3
import pandas as pd
from datetime import datetime
import random
import string

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
    return df.to_dict(orient="records")

def segment_customers_logic():
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    today = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    df['recency'] = (today - df['last_purchase_date']).dt.days

    results = []
    for _, row in df.iterrows():
        # Applying your strict 4-segment rules
        if row['recency'] <= 30 and row['purchase_count'] >= 10 and row['total_spend'] >= 1000:
            segment = "Champions"
        elif row['total_spend'] >= 1500:
            segment = "Big Spenders"
        elif row['recency'] > 60:
            segment = "At Risk"
        else:
            segment = "Loyal"
        
        cursor = conn.cursor()
        cursor.execute("UPDATE customers SET segment = ? WHERE customer_id = ?", (segment, row['customer_id']))
        results.append({"id": row['customer_id'], "name": row['name'], "segment": segment})
    
    conn.commit()
    conn.close()
    return {"status": "success", "processed": len(results), "data": results}

def generate_discount_code(customer_id: int):
    code = "WINBACK20-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, customer_id))
    conn.commit()
    conn.close()
    return {"status": "success", "customer_id": customer_id, "code": code}

def flag_vip_customer(customer_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET vip_flag = 1 WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return {"status": "success", "customer_id": customer_id, "message": "Flagged as VIP"}

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