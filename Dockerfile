# Use official Python runtime as a parent image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker cache
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Make entrypoint executable
RUN chmod +x entrypoint.sh

# Default Cloud Run port
ENV PORT 8080
ENV SERVICE_TYPE api

# Expose port
EXPOSE 8080

# Use the entrypoint script
ENTRYPOINT ["./entrypoint.sh"]
