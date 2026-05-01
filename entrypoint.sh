#!/bin/bash
set -e

if [ "$SERVICE_TYPE" = "ui" ]; then
    echo "🚀 Starting Streamlit UI on port $PORT..."
    streamlit run ui/app.py --server.port=$PORT --server.address=0.0.0.0
else
    echo "🛠️ Starting FastAPI Server on port $PORT..."
    uvicorn api.server:app --host 0.0.0.0 --port $PORT
fi
