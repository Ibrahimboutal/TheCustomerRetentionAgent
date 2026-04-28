import sqlite3
import random
import os
from datetime import datetime, timedelta

def init_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'mock_crm.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop tables for a clean production reset
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS approvals")
    cursor.execute("DROP TABLE IF EXISTS promotion_history")
    cursor.execute("DROP TABLE IF EXISTS support_logs")

    # Create Customers table with Telco Features
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        tenure INTEGER,
        MonthlyCharges REAL,
        TotalCharges REAL,
        SeniorCitizen INTEGER,
        Contract TEXT,
        PaperlessBilling TEXT,
        InternetService TEXT,
        segment TEXT,
        vip_flag INTEGER DEFAULT 0,
        discount_code TEXT
    )''')

    # Create Support Logs
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        log_text TEXT,
        timestamp TEXT
    )''')
    
    # Create Approvals
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        requested_amount REAL,
        status TEXT DEFAULT 'pending',
        timestamp TEXT
    )''')

    # Create Promotion History
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS promotion_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        promotion_type TEXT,
        date_issued TEXT
    )''')

    # Generate mock data
    contracts = ['Month-to-month', 'One year', 'Two year']
    internet = ['DSL', 'Fiber optic', 'No']
    yes_no = ['Yes', 'No']
    
    customers = []
    for i in range(1, 51):
        name = random.choice(["James", "Mary", "John", "Patricia", "Robert", "Jennifer"]) + " " + \
               random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"])
        email = name.lower().replace(" ", ".") + "@example.com"
        
        tenure = random.randint(1, 72)
        monthly = round(random.uniform(20, 120), 2)
        total = round(tenure * monthly, 2)
        
        customers.append((
            i, name, email, 
            tenure, monthly, total,
            random.choice([0, 1]),
            random.choice(contracts),
            random.choice(yes_no),
            random.choice(internet),
            "Unassigned", 0, None
        ))

    cursor.executemany('''
    INSERT INTO customers 
    (customer_id, name, email, tenure, MonthlyCharges, TotalCharges, SeniorCitizen, 
     Contract, PaperlessBilling, InternetService, segment, vip_flag, discount_code)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', customers)

    # Add sample support logs
    cursor.execute("INSERT INTO support_logs (customer_id, log_text, timestamp) VALUES (1, 'Delayed shipping on last order.', '2026-04-25')")
    cursor.execute("INSERT INTO support_logs (customer_id, log_text, timestamp) VALUES (2, 'Website login issues.', '2026-04-26')")

    conn.commit()
    conn.close()
    print("Database initialized successfully with Telco Features.")

if __name__ == "__main__":
    init_db()
