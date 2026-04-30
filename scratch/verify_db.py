import sqlite3
import pandas as pd
import sys
import os

# Add api directory to sys.path
sys.path.append(os.path.join(os.getcwd(), 'api'))

from server import DB

# Ensure the database exists
db_path = "mock_crm.db"
if not os.path.exists(db_path):
    print("Creating mock database...")
    # The server initialization logic will handle table creation if DB is accessed
    pass

print("--- Testing DB Abstraction (SQLite Mode) ---")
try:
    # Test query
    df = DB.query("SELECT * FROM customers LIMIT 5")
    print(f"Successfully queried {len(df)} customers.")
    if not df.empty:
        print(df[['customer_id', 'name', 'segment']].to_string())
    else:
        print("Customers table is empty.")

    # Test log
    DB.execute("INSERT INTO agent_logs (tool_name, arguments, result) VALUES (?, ?, ?)", 
               ("test_tool", "{'arg': 1}", "{'status': 'success'}"))
    print("Successfully logged a dummy action.")

    logs = DB.query("SELECT * FROM agent_logs ORDER BY timestamp DESC LIMIT 1")
    print("Latest log entry:")
    print(logs.to_dict(orient='records'))

except Exception as e:
    print(f"DB Test Failed: {e}")
