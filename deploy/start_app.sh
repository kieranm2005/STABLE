#!/bin/bash
cd /home/pi/your-repo

git pull origin main

# Create venv if it doesn't exist
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate venv and install requirements
source venv/bin/activate
pip install -r requirements.txt

# Run app using the venv's python
python3 src/main.py