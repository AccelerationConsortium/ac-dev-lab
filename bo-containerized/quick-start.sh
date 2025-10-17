#!/bin/bash
# Quick Start Script for BO Containerized Workflow
# This script automates the most common deployment scenario

set -e  # Exit on any error

echo "🐳 BO Containerized Workflow - Quick Start"
echo "=========================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Error: Docker is not running. Please start Docker Desktop/Engine first."
    exit 1
fi

echo "✅ Docker is running"

# Get host IP address
if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
    # Windows
    HOST_IP=$(ipconfig | grep "IPv4 Address" | head -1 | awk '{print $14}')
else
    # Mac/Linux  
    HOST_IP=$(ifconfig | grep "inet " | grep -v 127.0.0.1 | head -1 | awk '{print $2}')
fi

echo "🌐 Detected host IP: $HOST_IP"

# Check if Prefect server is running
echo "🔍 Checking for Prefect server..."
if netstat -an 2>/dev/null | grep -q ":4200"; then
    echo "✅ Prefect server is running on port 4200"
else
    echo "❌ Prefect server not detected on port 4200"
    echo "Please start Prefect server first:"
    echo "  prefect server start --host 0.0.0.0"
    exit 1
fi

# Ask for Slack webhook (optional)
echo ""
echo "📱 Slack Integration Setup (optional):"
echo "Enter your Slack webhook URL, or press Enter to skip:"
read -p "Slack webhook URL: " SLACK_URL

if [ -z "$SLACK_URL" ]; then
    echo "⏭️  Skipping Slack integration"
    SLACK_URL="https://hooks.slack.com/services/DEMO/WEBHOOK/URL"
fi

# Build Docker image if it doesn't exist
echo ""
echo "🔨 Building Docker image..."
if docker image inspect bo-workflow > /dev/null 2>&1; then
    echo "✅ Docker image 'bo-workflow' already exists"
    read -p "Rebuild image? (y/N): " rebuild
    if [[ $rebuild =~ ^[Yy]$ ]]; then
        docker build -t bo-workflow .
    fi
else
    echo "Building Docker image (this may take 20-30 minutes)..."
    docker build -t bo-workflow .
fi

# Run the workflow
echo ""
echo "🚀 Starting BO Workflow Container..."
echo "Monitor Slack for notifications and Prefect UI at: http://$HOST_IP:4200"
echo ""

docker run --rm \
    -e PREFECT_API_URL="http://$HOST_IP:4200/api" \
    -e SLACK_WEBHOOK_URL="$SLACK_URL" \
    bo-workflow

echo ""
echo "✅ Workflow completed!"