#!/bin/bash
set -e

echo "Setting up ResAI Linux/macOS environment..."

if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

source .venv/bin/activate
pip install -r backend/requirements.txt

cd frontend
npm install
cd ..

echo "ResAI setup completed successfully!"
