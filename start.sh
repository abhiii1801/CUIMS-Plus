#!/bin/bash

echo "Installing Playwright browsers..."
npx playwright install --with-deps

echo "Starting FastAPI server..."
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}