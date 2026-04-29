# Use official Python runtime as a parent image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for SciPy, Numpy, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Expose ports for both the FastAPI server and Streamlit
EXPOSE 8000
EXPOSE 8501

# Provide a script to run both services, but realistically for Cloud Run 
# you should deploy two separate services or use a process manager.
# For simplicity, we'll start the FastAPI server by default.
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
