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
    cursor.execute("SELECT name, discount_code FROM customers WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    
    name, code = row if row else ("Valued Customer", None)
    
    if segment == "At Risk":
        return f"Subject: We miss you, {name}! | Here is {code} for 20% off."
    elif segment == "Big Spenders":
        return f"Subject: VIP Access for {name} | Join our exclusive launch."
    return f"Subject: A special thanks to our {segment} customer!"

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