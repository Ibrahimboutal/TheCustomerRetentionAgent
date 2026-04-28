import sqlite3
import random
from datetime import datetime, timedelta

def init_db():
    conn = sqlite3.connect('mock_crm.db')
    cursor = conn.cursor()

    # Create Customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        last_purchase_date TEXT,
        purchase_count INTEGER,
        total_spend REAL,
        segment TEXT,
        vip_flag INTEGER DEFAULT 0,
        discount_code TEXT
    )
    ''')

    # Create Agent Logs table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agent_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        tool_name TEXT,
        arguments TEXT,
        result TEXT
    )
    ''')

    # Clear logs for a clean demo slate
    cursor.execute("DELETE FROM agent_logs")

    # Sample Names
    first_names = ["James", "Mary", "Robert", "Patricia", "John", "Jennifer", "Michael", "Linda", "William", "Elizabeth"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis", "Rodriguez", "Martinez"]

    customers = []
    today = datetime.now()

    for i in range(1, 51):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        email = f"{name.lower().replace(' ', '.')}@example.com"
        
        # Randomize purchase behavior
        # Champions: Recent, Frequent, High Spend
        # Loyal: Regular
        # Big Spenders: High Spend, Low Frequency
        # At Risk: Old Purchase Date
        
        r = random.random()
        if r < 0.2: # Potential Champions
            last_purchase = today - timedelta(days=random.randint(1, 10))
            count = random.randint(10, 30)
            spend = random.uniform(500, 2000)
        elif r < 0.5: # Potential Loyal
            last_purchase = today - timedelta(days=random.randint(11, 40))
            count = random.randint(5, 15)
            spend = random.uniform(200, 800)
        elif r < 0.7: # Potential Big Spenders
            last_purchase = today - timedelta(days=random.randint(20, 60))
            count = random.randint(1, 5)
            spend = random.uniform(1000, 3000)
        else: # Potential At Risk
            last_purchase = today - timedelta(days=random.randint(90, 200))
            count = random.randint(2, 10)
            spend = random.uniform(100, 1000)
            # Inject "Poison Pill": Missing email for first At Risk customer
            if not any(c[2] is None for c in customers):
                email = None

        customers.append((
            i, name, email, 
            last_purchase.strftime('%Y-%m-%d'), 
            count, round(spend, 2),
            "Unassigned", 0, None
        ))

    cursor.executemany('''
    INSERT OR REPLACE INTO customers 
    (customer_id, name, email, last_purchase_date, purchase_count, total_spend, segment, vip_flag, discount_code)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', customers)

    conn.commit()
    conn.close()
    print("Database initialized successfully with 50 mock customers.")

if __name__ == "__main__":
    init_db()
