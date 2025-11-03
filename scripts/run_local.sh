#!/bin/bash

# Run the NIM RAG Agent locally

# Check if .env exists
if [ ! -f .env ]; then
    echo "Error: .env file not found. Please create one from .env.example"
    exit 1
fi

# Load environment variables
export $(cat .env | xargs)

# Run the application
echo "Starting NIM RAG Agent..."
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload
