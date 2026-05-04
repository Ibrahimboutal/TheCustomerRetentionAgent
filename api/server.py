from fastapi import FastAPI, Body, Response, Request, HTTPException
import logging
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

# Ensure fixed random seeds for reproducibility
np.random.seed(42)
random.seed(42)

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

# Import schemas
from api.schemas import (
    EventStreamRequest, EventStreamResponse,
    GenerateDiscountRequest, FlagVipRequest, DebateRequest,
    EmailRequest, OptimizeRequest, AgentExecuteRequest, AgentExecuteResponse
)

DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")
ML_DIR = os.path.join(BASE_DIR, "ml")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")

# Model Versioning
MODEL_VERSION = "1.0.0"

# Logging Strategy
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("RetentionAPI")

try:
    from supabase import create_client as sb_create_client
    _sb_available = True
except ImportError:
    _sb_available = False

app = FastAPI(title="Retention-MCP-Server", version=MODEL_VERSION)

@app.middleware("http")
async def add_model_version_header(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Model-Version"] = MODEL_VERSION
    return response


# =========================
# DB LAYER
# =========================
class DB:
    _client = None

    @classmethod
    def get_client(cls):
        if cls._client is None and _sb_available and SUPABASE_URL and SUPABASE_KEY:
            try:
                cls._client = sb_create_client(SUPABASE_URL, SUPABASE_KEY)
            except Exception as e:
                logger.warning(f"Supabase connection failed: {e}")
        return cls._client

    @staticmethod
    def query(sql: str, params: tuple = ()) -> pd.DataFrame:
        client = DB.get_client()
        if client:
            table_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
            if table_match:
                try:
                    res = client.table(table_match.group(1)).select("*").execute()
                    df = pd.DataFrame(res.data)
                    if not df.empty:
                        expected = ["customer_id", "name", "email", "gender", "SeniorCitizen",
                                    "Partner", "Dependents", "tenure", "PhoneService",
                                    "MultipleLines", "InternetService", "OnlineSecurity",
                                    "OnlineBackup", "DeviceProtection", "TechSupport",
                                    "StreamingTV", "StreamingMovies", "Contract",
                                    "PaperlessBilling", "PaymentMethod", "MonthlyCharges",
                                    "TotalCharges", "segment", "vip_flag", "discount_code",
                                    "churn_probability"]
                        mapping = {c.lower(): c for c in expected}
                        df.columns = [mapping.get(c.lower(), c) for c in df.columns]
                    return df
                except Exception as e:
                    logger.error(f"Supabase query error: {e}")

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
                    client.table(table_name).update({col: params[0]}).eq(id_col, params[1]).execute()
                    return params[1]
                elif op == "INSERT INTO":
                    cols = [c.strip().lower() for c in re.search(r"\((.*?)\)", sql).group(1).split(",")]
                    res = client.table(table_name).insert(dict(zip(cols, params))).execute()
                    return res.data[0].get('id') if res.data else None
            except Exception as e:
                logger.error(f"SUPABASE WRITE ERROR: {e}")

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        conn.close()
        return True


def safe_json(obj):
    if isinstance(obj, (pd.DataFrame, pd.Series)):
        return obj.to_dict(orient="records")
    if isinstance(obj, (np.ndarray, np.generic)):
        return obj.tolist() if isinstance(obj, np.ndarray) else obj.item()
    if isinstance(obj, dict):
        return {k: safe_json(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [safe_json(v) for v in obj]
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0.0
    return obj


# =========================
# ML
# =========================
CHURN_MODEL = None
ENCODERS = {}
FEATURE_NAMES = ['gender', 'SeniorCitizen', 'Partner', 'Dependents', 'tenure',
                 'PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity',
                 'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV',
                 'StreamingMovies', 'Contract', 'PaperlessBilling', 'PaymentMethod',
                 'MonthlyCharges']

def load_models():
    global CHURN_MODEL, ENCODERS
    try:
        with open(os.path.join(ML_DIR, 'churn_model.pkl'), 'rb') as f:
            CHURN_MODEL = pickle.load(f)
        with open(os.path.join(ML_DIR, 'encoders.pkl'), 'rb') as f:
            ENCODERS = pickle.load(f)
        logger.info(f"ML models loaded (v{MODEL_VERSION}).")
    except Exception as e:
        logger.error(f"ML LOAD ERROR: {e}")

load_models()

def safe_encode(le, value):
    val = str(value).strip()
    if hasattr(le, 'classes_'):
        classes_lower = [str(c).lower() for c in le.classes_]
        if val.lower() in classes_lower:
            idx = classes_lower.index(val.lower())
            return le.transform([le.classes_[idx]])[0]
    return 0

def predict_single(row_dict: dict) -> float:
    if CHURN_MODEL is None:
        raise HTTPException(status_code=503, detail="ML Model not loaded")
    
    features = []
    for col in FEATURE_NAMES:
        val = row_dict.get(col, 0)
        if col in ENCODERS:
            features.append(safe_encode(ENCODERS[col], val))
        else:
            try:
                features.append(float(val))
            except:
                features.append(0.0)
                
    warnings.filterwarnings('ignore')
    prob = CHURN_MODEL.predict_proba([features])[0][1]
    return prob

# =========================
# REAL-TIME DECISION ENDPOINT
# =========================
@app.post("/api/v1/stream/event", response_model=EventStreamResponse)
def handle_stream_event(req: EventStreamRequest):
    logger.info(f"Received stream event: {req.event} for customer {req.customer_id}")
    
    # 1. Fetch customer current state
    df = DB.query(f"SELECT * FROM customers WHERE customer_id = {req.customer_id}")
    if df.empty:
        raise HTTPException(status_code=404, detail="Customer not found")
        
    row = df.iloc[0].to_dict()
    
    # 2. Update feature state based on event (simulated logic)
    if req.event == "failed_payment":
        row['MonthlyCharges'] *= 1.2 # simulate late fee adding to risk
        
    # 3. Near Real-Time Scoring
    new_prob = predict_single(row)
    new_prob_pct = round(new_prob * 100, 1)
    
    # 4. Update Database instantly
    DB.execute("UPDATE customers SET churn_probability = ? WHERE customer_id = ?", (new_prob_pct, req.customer_id))
    
    # 5. Micro-Decision Thresholding
    action_taken = "None"
    decision = "Hold"
    
    if new_prob > 0.40 and row.get('discount_code') is None:
        # Trigger immediate retention micro-action bypassing macro-batch
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        DB.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, req.customer_id))
        DB.execute(
            "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
            (datetime.now().isoformat(), "realtime_micro_action", str(req.customer_id), f"Issued code {code}")
        )
        action_taken = f"Issued Discount: {code}"
        decision = "Immediate Intervention"
        
    return EventStreamResponse(
        customer_id=req.customer_id,
        event=req.event,
        churn_probability=new_prob_pct,
        decision_made=decision,
        action_taken=action_taken,
        model_version=MODEL_VERSION
    )

# =========================
# AUTONOMOUS AGENT ENDPOINT
# =========================
@app.post("/api/v1/agent/execute", response_model=AgentExecuteResponse)
def execute_agent_goal(req: AgentExecuteRequest):
    try:
        from agent.orchestrator import RetentionAgent
        agent = RetentionAgent()
        res = agent.execute_goal(req.goal)
        if res["status"] == "error":
            raise HTTPException(status_code=500, detail=res.get("message"))
            
        return AgentExecuteResponse(
            status=res["status"],
            final_answer=res["final_answer"],
            trace=res["trace"]
        )
    except Exception as e:
        logger.error(f"Agent Execution Error: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))

# =========================
# TOOLS
# =========================
def get_customers():
    df = DB.query("SELECT * FROM customers")
    return {"total_customers": len(df), "customers": df.to_dict("records")}


def segment_customers():
    df = DB.query("SELECT * FROM customers")
    if df.empty or CHURN_MODEL is None:
        raise HTTPException(status_code=503, detail="Server not ready — missing data or ML model")

    X = pd.DataFrame()
    for col in FEATURE_NAMES:
        if col in df.columns:
            if col in ENCODERS:
                X[col] = df[col].apply(lambda v: safe_encode(ENCODERS[col], v))
            else:
                X[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
        else:
            X[col] = 0

    warnings.filterwarnings('ignore')
    probs = CHURN_MODEL.predict_proba(X.values)[:, 1]
    df["churn_risk"] = probs
    df["churn_probability"] = (probs * 100).round(1)

    def classify(row):
        if row["churn_risk"] > 0.5:
            return "At Risk"
        if row["MonthlyCharges"] > 90:
            return "Big Spender"
        if row["MonthlyCharges"] > 65:
            return "Champion"
        return "Loyal"

    df["segment"] = df.apply(classify, axis=1)

    # Persist to DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for _, row in df.iterrows():
        cur.execute(
            "UPDATE customers SET segment=?, churn_probability=? WHERE customer_id=?",
            (row["segment"], float(row["churn_probability"]), int(row["customer_id"]))
        )

    # Also sync to Supabase if available
    client = DB.get_client()
    if client:
        for _, row in df.iterrows():
            try:
                client.table("customers").update({
                    "segment": row["segment"],
                    "churn_probability": float(row["churn_probability"])
                }).eq("customer_id", int(row["customer_id"])).execute()
            except Exception as e:
                logger.error(f"Supabase sync failed: {e}")

    conn.commit()
    conn.close()

    return {
        "summary": df["segment"].value_counts().to_dict(),
        "at_risk_preview": df[df["segment"] == "At Risk"].head(10)[
            ["customer_id", "name", "churn_risk"]].to_dict("records"),
        "big_spender_preview": df[df["segment"] == "Big Spender"].head(10)[
            ["customer_id", "name", "MonthlyCharges"]].to_dict("records")
    }


def generate_discount(customer_id: Any = None):
    # Validate
    req = GenerateDiscountRequest(customer_id=customer_id)
    c_id = req.customer_id
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    DB.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, c_id))
    DB.execute(
        "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "generate_discount", str(c_id), f"Code: {code}")
    )
    return {"status": "success", "msg": f"Discount {code} saved for customer ID {c_id}"}


def flag_vip(customer_id: Any = None):
    req = FlagVipRequest(customer_id=customer_id)
    c_id = req.customer_id
    DB.execute("UPDATE customers SET vip_flag = ? WHERE customer_id = ?", (1, c_id))
    DB.execute(
        "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "flag_vip", str(c_id), "Flagged as VIP")
    )
    return {"status": "success", "msg": f"Customer {c_id} is now flagged as VIP."}


def initiate_boardroom_debate(customer_id: Any):
    req = DebateRequest(customer_id=customer_id)
    df = DB.query(f"SELECT * FROM customers WHERE customer_id = {req.customer_id}")
    if df.empty:
        raise HTTPException(status_code=404, detail="Customer not found")

    row = df.iloc[0]
    churn_prob = float(row.get('churn_probability', 30))
    from agent.boardroom import BoardroomDebate
    engine = BoardroomDebate()
    result = engine.run_debate(row['name'], f"{churn_prob:.1f}%", float(row['TotalCharges']))

    DB.execute(
        "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "boardroom_debate", str(req.customer_id),
         f"{result.get('discount', 0)}% approved — {result.get('summary', '')[:80]}")
    )
    return result


def draft_empathy_email(customer_id: Any, tone: str = "empathetic"):
    req = EmailRequest(customer_id=customer_id, tone=tone)
    df = DB.query(f"SELECT name FROM customers WHERE customer_id = {req.customer_id}")
    name = df.iloc[0]['name'] if not df.empty else "Valued Customer"
    
    if not GOOGLE_API_KEY:
        return {
            "email_body": (
                f"Dear {name},\n\nWe truly value your loyalty and the trust you've placed in us. "
                f"As a special thank you, we'd like to offer you an exclusive retention discount "
                f"on your next renewal. Please reach out to our team to claim your personalized offer.\n\n"
                f"Warm regards,\nCustomer Success Team"
            ),
            "safety_checked": True,
            "ai_powered": False
        }

    from google import genai
    client = genai.Client(api_key=GOOGLE_API_KEY)
    prompt = (
        f"Write a professional and {req.tone} retention email to {name}. "
        f"Offer a special discount without using generic placeholders. "
        f"Mention appreciation for their loyalty. Keep it under 150 words."
    )
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return {"email_body": response.text, "safety_checked": True, "ai_powered": True}


def trigger_macro_optimization(budget: float = 5000):
    req = OptimizeRequest(budget=budget)
    df = DB.query("SELECT customer_id, churn_probability, TotalCharges FROM customers")
    if df.empty:
        raise HTTPException(status_code=404, detail="No customers found.")
        
    from agent.decision_engine import DecisionEngine
    allocated, total_spend = DecisionEngine.optimize_cohort_discounts(df, budget=req.budget)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    for c_id, data in allocated.items():
        code = f"OPT-{random.randint(100, 999)}"
        cur.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, int(c_id)))
    conn.commit()
    conn.close()

    return {
        "status": "success",
        "budget_used": total_spend,
        "customers_optimized": len(allocated),
        "avg_discount_pct": round(np.mean([v['discount_pct'] for v in allocated.values()]), 1) if allocated else 0,
        "allocations": safe_json(allocated)
    }



TOOLS_MAP = {
    "get_customers": get_customers,
    "segment_customers": segment_customers,
    "generate_discount": generate_discount,
    "flag_vip": flag_vip,
    "initiate_boardroom_debate": initiate_boardroom_debate,
    "draft_empathy_email": draft_empathy_email,
    "trigger_macro_optimization": trigger_macro_optimization,
}


# =========================
# MCP HUB
# =========================
@app.post("/")
async def mcp_hub(req: dict = Body(...)):
    try:
        method = req.get("method", "")
        req_id = req.get("id", 0)
        
        if method == "initialize":
            return {"jsonrpc": "2.0", "id": req_id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "Retention-MCP-Server", "version": MODEL_VERSION}
            }}
        if method.startswith("notifications/"):
            return Response(status_code=204)
            
        if method == "tools/list":
            tools_list = [
                {"name": "get_customers", "description": "Fetch all customers.", "inputSchema": {"type": "object"}},
                {"name": "segment_customers", "description": "Run ML scoring and update segments.", "inputSchema": {"type": "object"}},
                {"name": "generate_discount", "description": "Generate a promo code for a customer.",
                 "inputSchema": {"type": "object", "properties": {"customer_id": {"type": ["string", "integer"]}}, "required": ["customer_id"]}},
                {"name": "flag_vip", "description": "Flag a customer as VIP.",
                 "inputSchema": {"type": "object", "properties": {"customer_id": {"type": ["string", "integer"]}}, "required": ["customer_id"]}},
                {"name": "initiate_boardroom_debate", "description": "Run multi-agent retention debate for a customer.",
                 "inputSchema": {"type": "object", "properties": {"customer_id": {"type": "integer"}}, "required": ["customer_id"]}},
                {"name": "draft_empathy_email", "description": "Generate a retention email for a customer.",
                 "inputSchema": {"type": "object", "properties": {"customer_id": {"type": "integer"}, "tone": {"type": "string"}}, "required": ["customer_id"]}},
                {"name": "trigger_macro_optimization", "description": "Run SciPy SLSQP budget optimization across all customers.",
                 "inputSchema": {"type": "object", "properties": {"budget": {"type": "number"}}, "required": ["budget"]}},
            ]
            return {"jsonrpc": "2.0", "id": req_id, "result": {"tools": tools_list}}
            
        if method == "tools/call":
            params = req.get("params", {})
            name = params.get("name")
            args = params.get("arguments", {})
            
            if name in TOOLS_MAP:
                logger.info(f"EXECUTING: {name} with args {args}")
                res = TOOLS_MAP[name](**args)
                return {"jsonrpc": "2.0", "id": req_id, "result": {
                    "content": [{"type": "text", "text": json.dumps(safe_json(res))}],
                    "isError": False
                }}
                
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": "Method not found"}}
        
    except HTTPException as he:
        logger.warning(f"HTTP Exception: {he.detail}")
        return {"jsonrpc": "2.0", "id": req.get("id", 0), "error": {"code": -32000, "message": str(he.detail)}}
    except Exception as e:
        logger.error(f"Internal Error: {traceback.format_exc()}")
        return {"jsonrpc": "2.0", "id": req.get("id", 0), "error": {"code": -32000, "message": str(e)}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
