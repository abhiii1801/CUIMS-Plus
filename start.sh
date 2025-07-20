#!/bin/bash
echo "Installing Playwright..."
playwright install

# Then start the app
uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000}