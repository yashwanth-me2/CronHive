#!/bin/bash
set -e
PORT="${PORT:-8000}"
echo "Starting FastAPI server on port $PORT..."
exec fastapi run src/main.py --host 0.0.0.0 --port $PORT
