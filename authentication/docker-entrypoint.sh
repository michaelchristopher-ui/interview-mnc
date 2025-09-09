#!/bin/bash

echo "Starting FastAPI app..."
exec python -m uvicorn src.main:app --host 0.0.0.0 --port 8001
