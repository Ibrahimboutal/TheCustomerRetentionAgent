#!/bin/bash
# Start the FastAPI backend (MCP server) on port 8000
uvicorn api.server:app --host 127.0.0.1 --port 8000 &
BACKEND_PID=$!

# Start the Streamlit UI on port 5000, bound to 0.0.0.0
streamlit run ui/app.py \
    --server.port 5000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableCORS false \
    --server.enableXsrfProtection false

# If streamlit exits, kill backend too
kill $BACKEND_PID 2>/dev/null
