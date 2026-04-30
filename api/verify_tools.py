import requests
import json

URL = "http://127.0.0.1:8000/"
HEADERS = {"X-API-Key": "HACKATHON_SECRET_123"}

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/list"
}
response = requests.post(URL, json=payload, headers=HEADERS)
print(json.dumps(response.json(), indent=2))
