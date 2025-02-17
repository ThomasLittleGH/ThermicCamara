#!/bin/bash

# Define virtual environment name
VENV_DIR="venv"

# Check if the virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Error: Virtual environment ($VENV_DIR) not found!"
    echo "Run ./setup.sh first."
    exit 1
fi

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "Starting Flask server..."
python3 script.py
