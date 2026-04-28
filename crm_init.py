import sqlite3
import random
from datetime import datetime, timedelta

def init_db():
    import os
    db_path = os.path.join(os.path.dirname(__file__), 'mock_crm.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Drop tables for a clean production reset
    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS approvals")
    cursor.execute("DROP TABLE IF EXISTS promotion_history")
    cursor.execute("DROP TABLE IF EXISTS support_logs")

    # Create Customers table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        last_purchase_date TEXT,
        purchase_count INTEGER,
        total_spend REAL,
        tenure_days INTEGER,
        support_tickets_30d INTEGER,
        login_frequency INTEGER,
        payment_failures INTEGER,
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

    # Create Promotion History table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS promotion_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        promotion_type TEXT,
        date_issued TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')

    # Create Approvals table (HITL)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS approvals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        requested_amount REAL,
        status TEXT DEFAULT 'pending',
        timestamp TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')

    # Create Support Logs table (RAG)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS support_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        transcript TEXT,
        date TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (customer_id)
    )
    ''')

    # Seed some fake support complaints
    complaints = [
        (1, "The shipping was delayed by 2 weeks and nobody notified me.", "2024-04-20"),
        (2, "My app keeps crashing when I try to add a new card.", "2024-04-22"),
        (3, "I was double charged for my last subscription renewal.", "2024-04-18"),
        (5, "The product I received was damaged during transit.", "2024-04-25"),
        (8, "I want to cancel my subscription but the button isn't working.", "2024-04-26")
    ]
    cursor.executemany("INSERT INTO support_logs (customer_id, transcript, date) VALUES (?, ?, ?)", complaints)

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
            random.randint(30, 730), # tenure_days
            random.randint(0, 5),    # support_tickets_30d
            random.randint(1, 30),   # login_frequency
            random.choice([0, 1, 2]),# payment_failures
            "Unassigned", 0, None
        ))

    cursor.executemany('''
    INSERT OR REPLACE INTO customers 
    (customer_id, name, email, last_purchase_date, purchase_count, total_spend, 
     tenure_days, support_tickets_30d, login_frequency, payment_failures,
     segment, vip_flag, discount_code)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', customers)

    conn.commit()
    conn.close()
    print("Database initialized successfully with 50 mock customers.")

if __name__ == "__main__":
    init_db()
