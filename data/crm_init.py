import sqlite3
import random
import os
from datetime import datetime

def init_db():
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(BASE_DIR, 'mock_crm.db')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS customers")
    cursor.execute("DROP TABLE IF EXISTS agent_logs")
    cursor.execute("CREATE TABLE agent_logs (timestamp TEXT, tool_name TEXT, arguments TEXT, result TEXT)")

    cursor.execute('''
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
        email TEXT,
        gender TEXT,
        SeniorCitizen INTEGER,
        Partner TEXT,
        Dependents TEXT,
        tenure INTEGER,
        PhoneService TEXT,
        MultipleLines TEXT,
        InternetService TEXT,
        OnlineSecurity TEXT,
        OnlineBackup TEXT,
        DeviceProtection TEXT,
        TechSupport TEXT,
        StreamingTV TEXT,
        StreamingMovies TEXT,
        Contract TEXT,
        PaperlessBilling TEXT,
        PaymentMethod TEXT,
        MonthlyCharges REAL,
        TotalCharges REAL,
        segment TEXT,
        vip_flag INTEGER DEFAULT 0,
        discount_code TEXT,
        churn_probability REAL DEFAULT 0.0
    )''')

    options = {
        'gender': ['Female', 'Male'],
        'Partner': ['Yes', 'No'],
        'Dependents': ['Yes', 'No'],
        'PhoneService': ['Yes', 'No'],
        'MultipleLines': ['No phone service', 'No', 'Yes'],
        'InternetService': ['DSL', 'Fiber optic', 'No'],
        'OnlineSecurity': ['No', 'Yes', 'No internet service'],
        'OnlineBackup': ['No', 'Yes', 'No internet service'],
        'DeviceProtection': ['No', 'Yes', 'No internet service'],
        'TechSupport': ['No', 'Yes', 'No internet service'],
        'StreamingTV': ['No', 'Yes', 'No internet service'],
        'StreamingMovies': ['No', 'Yes', 'No internet service'],
        'Contract': ['Month-to-month', 'One year', 'Two year'],
        'PaperlessBilling': ['Yes', 'No'],
        'PaymentMethod': ['Electronic check', 'Mailed check', 'Bank transfer (automatic)', 'Credit card (automatic)']
    }

    first_names = ["James", "Mary", "John", "Patricia", "Robert", "Jennifer",
                   "Michael", "Linda", "William", "Barbara", "David", "Jessica"]
    last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia",
                  "Miller", "Davis", "Wilson", "Anderson", "Taylor", "Thomas"]

    customers = []
    for i in range(1, 51):
        name = random.choice(first_names) + " " + random.choice(last_names)
        email = f"{name.lower().replace(' ', '.')}@email.com"
        gender = random.choice(options['gender'])
        senior = random.choice([0, 1])
        partner = random.choice(options['Partner'])
        dependents = random.choice(options['Dependents'])
        tenure = random.randint(1, 72)
        phone = random.choice(options['PhoneService'])
        multi = random.choice(options['MultipleLines'])
        internet = random.choice(options['InternetService'])
        sec = random.choice(options['OnlineSecurity'])
        backup = random.choice(options['OnlineBackup'])
        device = random.choice(options['DeviceProtection'])
        tech = random.choice(options['TechSupport'])
        tv = random.choice(options['StreamingTV'])
        movies = random.choice(options['StreamingMovies'])
        contract = random.choice(options['Contract'])
        billing = random.choice(options['PaperlessBilling'])
        payment = random.choice(options['PaymentMethod'])
        monthly = round(random.uniform(20, 120), 2)
        total = round(tenure * monthly, 2)

        customers.append((
            i, name, email, gender, senior, partner, dependents, tenure,
            phone, multi, internet, sec, backup, device, tech, tv, movies,
            contract, billing, payment, monthly, total, "Unassigned", 0, None, 0.0
        ))

    cursor.executemany('''
    INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', customers)

    conn.commit()
    conn.close()
    print("Database initialized with full Telco schema including churn_probability.")

if __name__ == "__main__":
    init_db()
