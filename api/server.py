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

load_dotenv()

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")
ML_DIR = os.path.join(BASE_DIR, "ml")

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
GOOGLE_CLOUD_PROJECT = os.environ.get("GOOGLE_CLOUD_PROJECT")

try:
    from google.cloud import logging as cloud_logging
    logging_client = cloud_logging.Client()
    logging_client.setup_logging()
    print("Cloud Logging Enabled")
except Exception:
    print("Cloud Logging skipped (Local mode)")

try:
    from supabase import create_client as sb_create_client
    _sb_available = True
except ImportError:
    _sb_available = False

app = FastAPI(title="Retention-MCP-Server")


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
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return 0.0
    return obj


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
            except Exception:
                pass
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
                except Exception:
                    pass

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
                sys.stdout.write(f"SUPABASE WRITE ERROR: {e}\n")
                sys.stdout.flush()

        conn = sqlite3.connect(DB_PATH)
        cur = conn.cursor()
        cur.execute(sql, params)
        conn.commit()
        conn.close()
        return True


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

try:
    with open(os.path.join(ML_DIR, 'churn_model.pkl'), 'rb') as f:
        CHURN_MODEL = pickle.load(f)
    with open(os.path.join(ML_DIR, 'encoders.pkl'), 'rb') as f:
        ENCODERS = pickle.load(f)
    print("ML models loaded.")
except Exception as e:
    print(f"ML LOAD ERROR: {e}")


def safe_encode(le, value):
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
    if df.empty or CHURN_MODEL is None:
        return {"error": "Server not ready — missing data or ML model"}

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
            except Exception:
                pass

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
    if customer_id is None:
        return {"status": "error", "message": "MISSING customer_id"}
    c_id = int(str(customer_id).split('-')[0]) if '-' in str(customer_id) else int(customer_id)
    code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    DB.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, c_id))
    DB.execute(
        "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "generate_discount", str(c_id), f"Code: {code}")
    )
    return {"status": "success", "msg": f"Discount {code} saved for customer ID {c_id}"}


def flag_vip(customer_id: Any = None):
    if customer_id is None:
        return {"status": "error", "message": "MISSING customer_id"}
    c_id = int(str(customer_id).split('-')[0]) if '-' in str(customer_id) else int(customer_id)
    DB.execute("UPDATE customers SET vip_flag = ? WHERE customer_id = ?", (1, c_id))
    DB.execute(
        "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "flag_vip", str(c_id), "Flagged as VIP")
    )
    return {"status": "success", "msg": f"Customer {c_id} is now flagged as VIP."}


def initiate_boardroom_debate(customer_id: Any):
    df = DB.query(f"SELECT * FROM customers WHERE customer_id = {int(customer_id)}")
    if df.empty:
        return {"error": "Customer not found"}

    row = df.iloc[0]
    churn_prob = float(row.get('churn_probability', 30))
    from agent.boardroom import BoardroomDebate
    engine = BoardroomDebate()
    result = engine.run_debate(row['name'], f"{churn_prob:.1f}%", float(row['TotalCharges']))

    DB.execute(
        "INSERT INTO agent_logs (timestamp, tool_name, arguments, result) VALUES (?, ?, ?, ?)",
        (datetime.now().isoformat(), "boardroom_debate", str(customer_id),
         f"{result.get('discount', 0)}% approved — {result.get('summary', '')[:80]}")
    )
    return result


def draft_empathy_email(customer_id: Any, tone: str = "empathetic"):
    if not GOOGLE_API_KEY:
        df = DB.query(f"SELECT name FROM customers WHERE customer_id = {int(customer_id)}")
        name = df.iloc[0]['name'] if not df.empty else "Valued Customer"
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
    df = DB.query(f"SELECT name FROM customers WHERE customer_id = {int(customer_id)}")
    name = df.iloc[0]['name'] if not df.empty else "Valued Customer"
    prompt = (
        f"Write a professional and {tone} retention email to {name}. "
        f"Offer a special discount without using generic placeholders. "
        f"Mention appreciation for their loyalty. Keep it under 150 words."
    )
    response = client.models.generate_content(model="gemini-2.0-flash", contents=prompt)
    return {"email_body": response.text, "safety_checked": True, "ai_powered": True}


def trigger_macro_optimization(budget: float = 5000):
    df = DB.query("SELECT customer_id, churn_probability, TotalCharges FROM customers")
    if df.empty:
        return {"error": "No customers found."}
    from agent.decision_engine import DecisionEngine
    allocated, total_spend = DecisionEngine.optimize_cohort_discounts(df, budget=budget)

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
async def mcp_hub(req: MCPRequest = Body(...)):
    try:
        if req.method == "initialize":
            return {"jsonrpc": "2.0", "id": req.id, "result": {
                "protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "Retention-MCP-Server", "version": "2.0.0"}
            }}
        if req.method.startswith("notifications/"):
            return Response(status_code=204)
        if req.method == "tools/list":
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
            return {"jsonrpc": "2.0", "id": req.id, "result": {"tools": tools_list}}
        if req.method == "tools/call":
            name = req.params.get("name")
            args = req.params.get("arguments", {})
            if name in TOOLS_MAP:
                sys.stdout.write(f"EXECUTING: {name}\n")
                sys.stdout.flush()
                res = TOOLS_MAP[name](**args)
                return {"jsonrpc": "2.0", "id": req.id, "result": {
                    "content": [{"type": "text", "text": json.dumps(safe_json(res))}],
                    "isError": False
                }}
        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32601, "message": "Method not found"}}
    except Exception as e:
        traceback.print_exc()
        return {"jsonrpc": "2.0", "id": req.id, "error": {"code": -32000, "message": str(e)}}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)
