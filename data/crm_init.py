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
    cursor.execute("DROP TABLE IF EXISTS agent_logs") # Clean up old logs too
    cursor.execute("CREATE TABLE agent_logs (timestamp TEXT, tool_name TEXT, arguments TEXT, result TEXT)")

    # Complete Telco Schema
    cursor.execute('''
    CREATE TABLE customers (
        customer_id INTEGER PRIMARY KEY,
        name TEXT,
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
        discount_code TEXT
    )''')

    # Categories from the dataset
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
    
    customers = []
    for i in range(1, 51):
        name = random.choice(["James", "Mary", "John", "Patricia", "Robert", "Jennifer"]) + " " + \
               random.choice(["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia"])
        
        tenure = random.randint(1, 72)
        monthly = round(random.uniform(20, 120), 2)
        total = round(tenure * monthly, 2)
        
        cust_row = [i, name]
        for key in ['gender', 'SeniorCitizen', 'Partner', 'Dependents']:
            if key == 'SeniorCitizen':
                cust_row.append(random.choice([0, 1]))
            else:
                cust_row.append(random.choice(options[key]))
        
        cust_row.append(tenure)
        
        for key in ['PhoneService', 'MultipleLines', 'InternetService', 'OnlineSecurity', 
                    'OnlineBackup', 'DeviceProtection', 'TechSupport', 'StreamingTV', 'StreamingMovies',
                    'Contract', 'PaperlessBilling', 'PaymentMethod']:
            cust_row.append(random.choice(options[key]))
            
        cust_row.extend([monthly, total, "Unassigned", 0, None])
        customers.append(tuple(cust_row))

    cursor.executemany('''
    INSERT INTO customers VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    ''', customers)

    conn.commit()
    conn.close()
    print("Database initialized with 100% Telco feature compatibility.")

if __name__ == "__main__":
    init_db()
