from fastapi import FastAPI, Body, Response, Request
from pydantic import BaseModel
import os
import sqlite3
import pandas as pd
import numpy as np
from datetime import datetime
import random
import string
import json
import pickle
import re
import sys
import math
import traceback
import warnings
from typing import Optional, Any
from dotenv import load_dotenv
from supabase import create_client
from google.cloud import bigquery
from google.cloud import logging as cloud_logging
from agent.boardroom import BoardroomDebate
from agent.decision_engine import DecisionEngine
import google.generativeai as genai

load_dotenv()

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")
ML_DIR = os.path.join(BASE_DIR, "ml")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

# Initialize Cloud Logging
try:
    logging_client = cloud_logging.Client()
    logging_client.setup_logging()
    print("📡 Cloud Logging Enabled")
except:
    print("⚠️ Cloud Logging skipped (Local mode)")

app = FastAPI(title="Perfect-Sync-MCP")

class MCPRequest(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    id: Optional[Any] = 0
    params: Optional[dict] = {}

def safe_json(obj):
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return obj.to_dict(orient="records")
    if isinstance(obj, (np.ndarray, np.generic)):
        return obj.tolist() if isinstance(obj, np.ndarray) else obj.item()
    if isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return 0.0
    return obj

# =========================
# DB
# =========================
class DB:
    _client = None
    @classmethod
    def get_client(cls):
        if cls._client is None and SUPABASE_URL and SUPABASE_KEY:
            try: cls._client = create_client(SUPABASE_URL, SUPABASE_KEY)
            except: pass
        return cls._client

    @staticmethod
    def query(sql: str, params: tuple = ()) -> pd.DataFrame:
        # Priority 1: Supabase
        client = DB.get_client()
        if client:
            table_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1)
                try:
                    res = client.table(table_name).select("*").execute()
                    df = pd.DataFrame(res.data)
                    if not df.empty:
                        expected = ["customer_id", "name", "email", "gender", "SeniorCitizen", "Partner", "Dependents", "tenure", "PhoneService", "MultipleLines", "InternetService", "OnlineSecurity", "OnlineBackup", "DeviceProtection", "TechSupport", "StreamingTV", "StreamingMovies", "Contract", "PaperlessBilling", "PaymentMethod", "MonthlyCharges", "TotalCharges", "segment", "vip_flag", "discount_code"]
                        mapping = {col.lower(): col for col in expected}
                        df.columns = [mapping.get(c.lower(), c) for c in df.columns]
                    return df
                except:
                    pass

        # Priority 2: BigQuery
        if GOOGLE_CLOUD_PROJECT:
            try:
                df = BQ.query(sql)
                if not df.empty: return df
            except:
                pass

        # Priority 3: Local SQLite
        if os.path.exists(DB_PATH):
            conn = sqlite3.connect(DB_PATH)
            df = pd.read_sql_query(sql, conn, params=params)
            conn.close()
            return df
        
        return pd.DataFrame()

    @staticmethod
    def execute(sql: str, params: tuple = ()) -> Any:
        client = DB.get_client()
        table_match = re.search(r"(UPDATE|INSERT INTO)\s+(\w+)", sql, re.IGNORECASE)
        table_name = table_match.group(2) if table_match else "unknown"
        op = table_match.group(1).upper() if table_match else "EXEC"
        if client:
            try:
                if op == "UPDATE":
                    col = re.search(r"SET\s+(\w+)", sql, re.IGNORECASE).group(1).lower()
                    id_col = re.search(r"WHERE\s+(\w+)", sql, re.IGNORECASE).group(1).lower()
                    res = client.table(table_name).update({col: params[0]}).eq(id_col, params[1]).execute()
                    sys.stdout.write(f"💾 SUPABASE UPDATE: {table_name}.{col}={params[0]} for ID {params[1]}\n")
                    sys.stdout.flush()
                    return params[1]
                elif op == "INSERT INTO":
                    cols = [c.strip().lower() for c in re.search(r"\((.*?)\)", sql).group(1).split(",")]
                    res = client.table(table_name).insert(dict(zip(cols, params))).execute()
                    sys.stdout.write(f"💾 SUPABASE INSERT: SUCCESS\n")
                    sys.stdout.flush()
                    return res.data[0].get('id') if res.data else None
            except Exception as e:
                sys.stdout.write(f"🚨 SUPABASE WRITE ERROR: {str(e)}\n")
                sys.stdout.flush()
        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        conn.close()
        return True

class BQ:
    _client = None
    @classmethod
    def get_client(cls):
        if cls._client is None and GOOGLE_CLOUD_PROJECT:
            try: cls._client = bigquery.Client(project=GOOGLE_CLOUD_PROJECT)
            except: pass
        return cls._client

    @staticmethod
    def query(sql: str) -> pd.DataFrame:
        client = BQ.get_client()
        if client:
            # Simple heuristic: if it's a raw SELECT from customers, point to BQ
            if "FROM customers" in sql.upper() and "retention_engine" not in sql.lower():
                sql = sql.replace("customers", f"`{GOOGLE_CLOUD_PROJECT}.retention_engine.customers`")
            return client.query(sql).to_dataframe()
        return pd.DataFrame()

# =========================
# ML
# =========================
CHURN_MODEL = None
ENCODERS = {}
FEATURE_NAMES = ['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure', 'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity', 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod', 'MonthlyCharges']

try:
    with open(os.path.join(ML_DIR, 'churn_model.pkl'), 'rb') as f: CHURN_MODEL = pickle.load(f)
    with open(os.path.join(ML_DIR, 'encoders.pkl'), 'rb') as f: ENCODERS = pickle.load(f)
except Exception as e: print(f"🚨 ML LOAD ERROR: {e}")

def safe_encode(le, value, col_name):
    val = str(value).strip()
    if hasattr(le, 'classes_'):
        classes_lower = [str(c).lower() for c in le.classes_]
        if val.lower() in classes_lower:
            idx = classes_lower.index(val.lower())
            return le.transform([le.classes_[idx]])[0]
    return 0

# =========================
# TOOLS
# =========================
def get_customers():
    df = DB.query("SELECT * FROM customers")
    return {"total_customers": len(df), "customers": df.to_dict("records")}

def segment_customers():
    df = DB.query("SELECT * FROM customers")
    if df.empty or CHURN_MODEL is None: return {"error": "Server not ready"}
    X = pd.DataFrame()
    for col in FEATURE_NAMES:
        if col in df.columns:
            if col in ENCODERS: X[col] = df[col].apply(lambda v: safe_encode(ENCODERS[col], v, col))
            else: X[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else: X[col] = 0
    
    warnings.filterwarnings('ignore')
    probs = CHURN_MODEL.predict_proba(X.values)[:, 1]
    df["churn_risk"] = probs
    
    def logic(row):
        if row["churn_risk"] > 0.15: return "At Risk"
        if row["MonthlyCharges"] > 100: return "Big Spender"
        if row["MonthlyCharges"] > 70: return "Champion"
        return "Loyal"
    
    df["segment"] = df.apply(logic, axis=1)
    
    client = DB.get_client()
    if client:
        sys.stdout.write(f"💾 SYNCING 50 SEGMENTS TO SUPABASE...\n")
        sys.stdout.flush()
        for idx, row in df.iterrows():
            # STRICT ID MAPPING
            target_id = int(row["customer_id"])
            client.table("customers").update({"segment": row["segment"]}).eq("customer_id", target_id).execute()
        sys.stdout.write(f"✅ SEGMENTS PERSISTED.\n")
        sys.stdout.flush()

    return {
        "summary": df["segment"].value_counts().to_dict(), 
        "at_risk_preview": df[df["segment"]=="At Risk"].head(10)[["customer_id","name","churn_risk"]].to_dict("records"),
        "big_spender_preview": df[df["segment"]=="Big Spender"].head(10)[["customer_id","name","MonthlyCharges"]].to_dict("records")
    }

def generate_discount(customer_id: Any = None):
    if customer_id is None: return {"status": "error", "message": "MISSING customer_id"}
    c_id = int(str(customer_id).split('-')[0]) if '-' in str(customer_id) else int(customer_id)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    DB.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, c_id))
    DB.execute("INSERT INTO promotion_history (customer_id, promotion_type, date_issued) VALUES (?, ?, ?)", 
               (c_id, f"Discount: {code}", datetime.now().strftime("%Y-%m-%d")))
    return {"status": "success", "msg": f"Discount {code} SAVED to customers and history for ID {c_id}"}

def flag_vip(customer_id: Any = None):
    if customer_id is None: return {"status": "error", "message": "MISSING customer_id"}
    c_id = int(str(customer_id).split('-')[0]) if '-' in str(customer_id) else int(customer_id)
    DB.execute("UPDATE customers SET vip_flag = ? WHERE customer_id = ?", (1, c_id))
    return {"status": "success", "msg": f"Customer {c_id} is now flagged as VIP in the database."}

def initiate_boardroom_debate(customer_id: Any):
    # Fetch customer details
    df = DB.query(f"SELECT name, churn_probability, TotalCharges FROM customers WHERE customer_id = {int(customer_id)}")
    if df.empty: return {"error": "Customer not found"}
    
    row = df.iloc[0]
    debate_engine = BoardroomDebate()
    result = debate_engine.run_debate(row['name'], f"{row['churn_probability']}%", row['TotalCharges'])
    
    # Log the debate to Supabase/Logging
    sys.stdout.write(f"🎭 DEBATE COMPLETE for {row['name']}: {result['discount']}% approved.\n")
    sys.stdout.flush()
    
    return result

def draft_empathy_email(customer_id: Any, tone: str = "empathetic"):
    # Vertex AI Safety Settings
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_MEDIUM_AND_ABOVE"},
    ]
    
    model = genai.GenerativeModel('gemini-1.5-pro', safety_settings=safety_settings)
    
    df = DB.query(f"SELECT name FROM customers WHERE customer_id = {int(customer_id)}")
    name = df.iloc[0]['name'] if not df.empty else "Valued Customer"
    
    prompt = f"Write a professional and {tone} email to {name} offering a special retention discount. Do not use generic placeholders. Mention our appreciation for their loyalty."
    
    response = model.generate_content(prompt)
    return {"email_body": response.text, "safety_checked": True}

def trigger_macro_optimization(budget: float = 5000):
    df = DB.query("SELECT customer_id, churn_probability, TotalCharges FROM customers")
    if df.empty: return {"error": "No customers found for optimization."}
    
    # Use the SciPy engine
    allocated, total_spend = DecisionEngine.optimize_cohort_discounts(df, budget=budget)
    
    # Persist the new discount codes to the DB (simulated)
    for c_id, data in allocated.items():
        code = f"MACRO-{random.randint(100, 999)}"
        DB.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, c_id))
    
    return {
        "status": "success",
        "budget_used": total_spend,
        "customers_saved": len(allocated),
        "avg_discount": np.mean([v['rate'] for v in allocated.values()]) if allocated else 0
    }

TOOLS_MAP = {
    "get_customers": get_customers, 
    "segment_customers": segment_customers, 
    "generate_discount": generate_discount, 
    "flag_vip": flag_vip,
    "initiate_boardroom_debate": initiate_boardroom_debate,
    "draft_empathy_email": draft_empathy_email,
    "trigger_macro_optimization": trigger_macro_optimization
}

# =========================
# HUB
# =========================
@app.post("/")
async def mcp_hub(req: MCPRequest = Body(...)):
    try:
        if req.method == "initialize":
            return {"jsonrpc": "2.0", "id": req.id, "result": {"protocolVersion": "2024-11-05", "capabilities": {"tools": {}}, "serverInfo": {"name": "Retention-Server", "version": "1.12.0"}}}
        if req.method.startswith("notifications/"): return Response(status_code=204)
        if req.method == "tools/list":
            tools_list = [
                {"name": "get_customers", "description": "Fetch customer list to see IDs.", "inputSchema": {"type": "object"}},
                {"name": "segment_customers", "description": "REQUIRED: Updates segments in the cloud database.", "inputSchema": {"type": "object"}},
                {"name": "generate_discount", "description": "Saves a promo code for a customer ID.", "inputSchema": {"type": "object", "properties": {"customer_id": {"type": ["string", "integer"]}}, "required": ["customer_id"]}},
                {"name": "flag_vip", "description": "Flags a customer as VIP in Supabase.", "inputSchema": {"type": "object", "properties": {"customer_id": {"type": ["string", "integer"]}}, "required": ["customer_id"]}},
                {"name": "initiate_boardroom_debate", "description": "Triggers a multi-agent debate (CFO vs Success) for a customer ID.", "inputSchema": {"type": "object", "properties": {"customer_id": {"type": "integer"}}, "required": ["customer_id"]}},
                {"name": "draft_empathy_email", "description": "Generates a safety-filtered email for a customer.", "inputSchema": {"type": "object", "properties": {"customer_id": {"type": "integer"}, "tone": {"type": "string"}}, "required": ["customer_id"]}},
                {"name": "trigger_macro_optimization", "description": "Solves SLSQP optimization for the entire cohort based on a budget.", "inputSchema": {"type": "object", "properties": {"budget": {"type": "number"}}, "required": ["budget"]}}
            ]
            return {"jsonrpc": "2.0", "id": req.id, "result": {"tools": tools_list}}
        if req.method == "tools/call":
            name = req.params.get("name")
            args = req.params.get("arguments", {})
            if name in TOOLS_MAP:
                sys.stdout.write(f"🛠️ EXECUTING TOOL: {name}...\n")
                sys.stdout.flush()
                res = TOOLS_MAP[name](**args)
                return {"jsonrpc": "2.0", "id": req.id, "result": {"content": [{"type": "text", "text": json.dumps(safe_json(res))}], "isError": False}}
        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32601, "message": "Method not found"}}
    except Exception as e:
        sys.stdout.write(f"🚨 HUB CRASH: {str(e)}\n")
        sys.stdout.flush()
        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32000, "message": str(e)}}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)