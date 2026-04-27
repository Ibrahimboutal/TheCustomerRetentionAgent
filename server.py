import sqlite3
import pandas as pd
from datetime import datetime
from mcp.server.fastmcp import FastMCP
import random
import string

# Initialize FastMCP server
mcp = FastMCP("RetentionAgent")

DB_PATH = "mock_crm.db"

def get_db_connection():
    return sqlite3.connect(DB_PATH)

@mcp.tool()
def get_customers() -> str:
    """Fetch all customer records from the mock CRM."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    conn.close()
    return df.to_json(orient="records")

@mcp.tool()
def calculate_rfm_scores() -> str:
    """Calculate RFM (Recency, Frequency, Monetary) scores for all customers."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT customer_id, last_purchase_date, purchase_count, total_spend FROM customers", conn)
    conn.close()

    today = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    
    # Recency: Days since last purchase
    df['recency'] = (today - df['last_purchase_date']).dt.days
    # Frequency: purchase_count
    df['frequency'] = df['purchase_count']
    # Monetary: total_spend
    df['monetary'] = df['total_spend']

    return df[['customer_id', 'recency', 'frequency', 'monetary']].to_json(orient="records")

@mcp.tool()
def segment_customers() -> str:
    """Classify customers into four segments: Champions, Loyal, Big Spenders, and At Risk based on RFM."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM customers", conn)
    
    today = datetime.now()
    df['last_purchase_date'] = pd.to_datetime(df['last_purchase_date'])
    df['recency'] = (today - df['last_purchase_date']).dt.days

    segments = []
    for _, row in df.iterrows():
        # Logic for segments
        if row['recency'] <= 30 and row['purchase_count'] >= 10 and row['total_spend'] >= 1000:
            segment = "Champions"
        elif row['purchase_count'] >= 5 and row['recency'] <= 60:
            segment = "Loyal"
        elif row['total_spend'] >= 1500:
            segment = "Big Spenders"
        elif row['recency'] > 90:
            segment = "At Risk"
        else:
            segment = "Standard" # Default for those who don't fit the hackathon categories perfectly

        segments.append(segment)
        
        # Update database
        cursor = conn.cursor()
        cursor.execute("UPDATE customers SET segment = ? WHERE customer_id = ?", (segment, row['customer_id']))
    
    conn.commit()
    conn.close()
    
    return f"Successfully segmented {len(df)} customers."

@mcp.tool()
def generate_discount_code(customer_id: int) -> str:
    """Generate a unique 20% win-back discount code for an At Risk customer."""
    code = "WINBACK20-" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET discount_code = ? WHERE customer_id = ?", (code, customer_id))
    conn.commit()
    conn.close()
    
    return f"Generated code {code} for Customer ID {customer_id}."

@mcp.tool()
def flag_vip_customer(customer_id: int) -> str:
    """Flag a Big Spender for the upcoming VIP product launch preview."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE customers SET vip_flag = 1 WHERE customer_id = ?", (customer_id,))
    conn.commit()
    conn.close()
    
    return f"Customer ID {customer_id} has been flagged as VIP."

@mcp.tool()
def draft_personalized_email(customer_id: int, segment: str) -> str:
    """Draft a personalized email based on the customer's segment."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name, discount_code FROM customers WHERE customer_id = ?", (customer_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return "Customer not found."
    
    name, code = row
    
    if segment == "At Risk":
        return f"Subject: We Miss You, {name}!\n\nHi {name},\nIt's been a while! Use code {code} for 20% off your next order."
    elif segment == "Big Spenders":
        return f"Subject: Exclusive VIP Invite for {name}\n\nHi {name},\nAs one of our top customers, we're giving you early access to our next launch!"
    else:
        return f"Subject: Thank you for being a customer, {name}!"

if __name__ == "__main__":
    mcp.run()
