import requests
import json

URL = "http://127.0.0.1:8000/"
HEADERS = {"X-API-Key": "HACKATHON_SECRET_123"}

def call_tool(name, args={}):
    payload = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": name,
            "arguments": args
        }
    }
    response = requests.post(URL, json=payload, headers=HEADERS)
    return response.json()

print("--- Testing Segmentation ---")
print(json.dumps(call_tool("segment_customers"), indent=2))

print("\n--- Testing Campaign Optimization ---")
print(json.dumps(call_tool("run_campaign_optimization"), indent=2))

print("\n--- Testing Discount Generation (with RAG/Sentiment) ---")
# Assuming customer 1 exists and has some logs
print(json.dumps(call_tool("generate_discount", {"customer_id": 1, "requested_rate": 0.1}), indent=2))
