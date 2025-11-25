#!/bin/bash
# A1 Mini Camera Setup Script
#
# This script automates the setup process described in README.md
# If this script and README diverge, README is authoritative.
#
# Usage: bash setup.sh

set -e  # Exit on any error

echo "======================================"
echo "A1 Mini Camera Setup"
echo "======================================"
echo ""

# Codebase section (see README.md ## Codebase)
echo "[1/6] Updating system packages..."
sudo apt update
sudo apt upgrade -y

echo "[2/6] Installing git..."
sudo apt-get install git -y

echo "[3/6] Cloning repository..."
if [ ! -d "/home/ac/ac-dev-lab" ]; then
    cd /home/ac
    git clone https://github.com/AccelerationConsortium/ac-dev-lab.git
    cd ac-dev-lab/src/ac_training_lab/a1_cam/
else
    echo "Repository already exists, skipping clone..."
    cd /home/ac/ac-dev-lab/src/ac_training_lab/a1_cam/
fi

# Secrets section (see README.md ## Secrets)
echo "[4/6] Setting up secrets file..."
if [ ! -f "my_secrets.py" ]; then
    cp my_secrets_example.py my_secrets.py
    echo "⚠️  IMPORTANT: Edit my_secrets.py with your AWS and MQTT credentials"
    echo "    Required values:"
    echo "    - AWS_ACCESS_KEY_ID"
    echo "    - AWS_SECRET_ACCESS_KEY"
    echo "    - AWS_REGION"
    echo "    - BUCKET_NAME"
    echo "    - MQTT_HOST, MQTT_USERNAME, MQTT_PASSWORD"
    echo "    - DEVICE_SERIAL"
    echo ""
    read -p "Press Enter after editing my_secrets.py to continue..."
else
    echo "my_secrets.py already exists, skipping..."
fi

# Dependencies section (see README.md ## Dependencies)
echo "[5/6] Installing dependencies..."
sudo apt install -y --no-install-recommends python3-picamera2 ffmpeg

# Virtual environment setup
echo "[6/6] Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv --system-site-packages venv
fi

source venv/bin/activate
pip install -r requirements.txt

echo ""
echo "======================================"
echo "✓ Setup complete!"
echo "======================================"
echo ""
echo "To run the camera device:"
echo "  cd /home/ac/ac-dev-lab/src/ac_training_lab/a1_cam/"
echo "  source venv/bin/activate"
echo "  python3 device.py"
echo ""
echo "To test from another machine, see test_camera.ipynb or run:"
echo "  cd _scripts"
echo "  python3 client.py"
