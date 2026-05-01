from google.cloud import bigquery
import os
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PROJECT_ID = os.environ.get("GOOGLE_CLOUD_PROJECT")
DATASET_ID = "retention_engine"

client = bigquery.Client(project=PROJECT_ID)

def init_bigquery():
    dataset_ref = client.dataset(DATASET_ID)
    
    # Create Dataset
    try:
        client.get_dataset(dataset_ref)
        print(f"Dataset {DATASET_ID} already exists.")
    except:
        dataset = bigquery.Dataset(dataset_ref)
        dataset.location = "US"
        client.create_dataset(dataset)
        print(f"Created dataset {DATASET_ID}")

    # Load Telco Churn Data if available
    csv_path = "ml/telco_churn.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path)
        table_id = f"{PROJECT_ID}.{DATASET_ID}.customers"
        
        job_config = bigquery.LoadJobConfig(
            write_disposition="WRITE_TRUNCATE",
        )
        
        job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
        job.result()
        print(f"Loaded {len(df)} rows into {table_id}")
    else:
        print("Telco churn CSV not found. Skipping data load.")

if __name__ == "__main__":
    if not PROJECT_ID:
        print("ERROR: GOOGLE_CLOUD_PROJECT environment variable not set.")
    else:
        init_bigquery()
