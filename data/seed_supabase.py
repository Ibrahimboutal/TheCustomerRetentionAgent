import sqlite3
import pandas as pd
import os
from supabase import create_client
from dotenv import load_dotenv
import sys

load_dotenv()

# =========================
# CONFIG
# =========================
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "mock_crm.db")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

def migrate():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("🚨 Error: SUPABASE_URL and SUPABASE_KEY must be set in .env")
        return

    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    # 1. Load Local Data
    if not os.path.exists(DB_PATH):
        print(f"🚨 Error: Local database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()

    print(f"🔄 Found {len(df)} customers locally. Cleaning Supabase for fresh seed...")

    # 2. CLEAN SUPABASE
    try:
        supabase.table("promotion_history").delete().neq("id", 0).execute()
        supabase.table("agent_logs").delete().neq("id", 0).execute()
        supabase.table("approvals").delete().neq("id", 0).execute()
        supabase.table("support_logs").delete().neq("id", 0).execute()
        supabase.table("customers").delete().neq("customer_id", 0).execute()
        print("✅ Supabase cleared.")
    except Exception as e:
        print(f"⚠️ Clean Warning: {e}")

    # 3. NORMALIZE FOR SUPABASE
    # Lowercase all column names (Supabase/Postgres standard)
    df.columns = [c.lower() for c in df.columns]
    
    # Ensure IDs are clean
    df['customer_id'] = range(1, len(df) + 1)
    df['vip_flag'] = 0
    df['discount_code'] = None
    df['segment'] = 'Unassigned'

    # Convert to records
    records = df.to_dict(orient="records")
    
    print(f"🚀 Seeding {len(records)} customers to Supabase (Lowercase Mapping)...")
    try:
        res = supabase.table("customers").insert(records).execute()
        if res.data:
            print(f"🎉 Success! Migrated {len(res.data)} records to Supabase.")
        else:
            print(f"🚨 Migration Failed: {res}")
    except Exception as e:
        print(f"🚨 Supabase Insert Error: {e}")

if __name__ == "__main__":
    migrate()
