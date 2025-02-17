#!/bin/bash

# Define virtual environment name
VENV_DIR="venv"

echo "Updating package lists..."
sudo apt update -y

echo "Installing required system packages..."
sudo apt install -y python3 python3-venv python3-pip libatlas-base-dev libjpeg-dev libopenblas-dev liblapack-dev libhdf5-dev

echo "Creating virtual environment ($VENV_DIR)..."
python3 -m venv $VENV_DIR

echo "Activating virtual environment..."
source $VENV_DIR/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing required Python packages..."
pip install flask numpy matplotlib opencv-python-headless

echo "Setup complete. To start the server, run ./start.sh"
