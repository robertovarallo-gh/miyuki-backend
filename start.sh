#!/bin/bash
# Railway environment setup

# Add pip packages to PATH
export PATH="$HOME/.local/bin:$PATH"
export PYTHONUNBUFFERED=1

# Install dependencies with break-system-packages
pip install -r requirements.txt --break-system-packages

# Start gunicorn
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 300
