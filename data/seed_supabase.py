import sqlite3
import os
import pandas as pd
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def seed_to_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("❌ Error: SUPABASE_URL or SUPABASE_KEY not found in .env file.")
        return

    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # 1. Connect to local SQLite
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'mock_crm.db')
    
    if not os.path.exists(db_path):
        print(f"❌ Error: Local database not found at {db_path}. Run crm_init.py first.")
        return
        
    conn = sqlite3.connect(db_path)
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()

    # PostgreSQL is case-sensitive for identifiers. 
    # Lowercase everything to match standard Supabase table creation.
    df.columns = [c.lower() for c in df.columns]

    print(f"🔄 Found {len(df)} customers in local database. Migrating to Supabase...")

    # 2. Push to Supabase (in batches of 50 to avoid payload limits)
    # Convert dataframe to list of dicts
    records = df.to_dict(orient='records')
    
    # Supabase uses snake_case for consistency usually, but we'll stick to the provided schema
    # which has some PascalCase from Telco dataset
    
    try:
        # Clear existing customers to avoid primary key conflicts
        supabase.table("customers").delete().neq("customer_id", -1).execute()
        
        # Batch upload
        for i in range(0, len(records), 50):
            batch = records[i:i+50]
            supabase.table("customers").insert(batch).execute()
            print(f"✅ Uploaded batch {i//50 + 1}")

        print("\n🚀 Migration Complete! Your Supabase instance is now seeded.")
        
    except Exception as e:
        print(f"❌ Migration Failed: {e}")

if __name__ == "__main__":
    seed_to_supabase()
