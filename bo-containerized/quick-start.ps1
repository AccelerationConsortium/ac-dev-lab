# Quick Start Script for BO Containerized Workflow (Windows PowerShell)
# This script automates the most common deployment scenario

Write-Host "🐳 BO Containerized Workflow - Quick Start" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Check if Docker is running
try {
    docker info | Out-Null
    Write-Host "✅ Docker is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Docker is not running. Please start Docker Desktop first." -ForegroundColor Red
    exit 1
}

# Get host IP address
$HOST_IP = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.PrefixOrigin -eq 'Dhcp' } | Select-Object -First 1).IPAddress
Write-Host "🌐 Detected host IP: $HOST_IP" -ForegroundColor Yellow

# Check if Prefect server is running
Write-Host "🔍 Checking for Prefect server..." -ForegroundColor Yellow
$prefectRunning = netstat -ano | Select-String ":4200"
if ($prefectRunning) {
    Write-Host "✅ Prefect server is running on port 4200" -ForegroundColor Green
} else {
    Write-Host "❌ Prefect server not detected on port 4200" -ForegroundColor Red
    Write-Host "Please start Prefect server first:" -ForegroundColor Yellow
    Write-Host "  Start-Process powershell -ArgumentList '-NoExit', '-Command', 'prefect server start --host 0.0.0.0'" -ForegroundColor Yellow
    exit 1
}

# Ask for Slack webhook (optional)
Write-Host ""
Write-Host "📱 Slack Integration Setup (optional):" -ForegroundColor Cyan
$SLACK_URL = Read-Host "Enter your Slack webhook URL, or press Enter to skip"

if ([string]::IsNullOrEmpty($SLACK_URL)) {
    Write-Host "⏭️  Skipping Slack integration" -ForegroundColor Yellow
    $SLACK_URL = "https://hooks.slack.com/services/DEMO/WEBHOOK/URL"
}

# Build Docker image if it doesn't exist
Write-Host ""
Write-Host "🔨 Checking Docker image..." -ForegroundColor Yellow
try {
    docker image inspect bo-workflow | Out-Null
    Write-Host "✅ Docker image 'bo-workflow' already exists" -ForegroundColor Green
    $rebuild = Read-Host "Rebuild image? (y/N)"
    if ($rebuild -match "^[Yy]$") {
        docker build -t bo-workflow .
    }
} catch {
    Write-Host "Building Docker image (this may take 20-30 minutes)..." -ForegroundColor Yellow
    docker build -t bo-workflow .
}

# Run the workflow
Write-Host ""
Write-Host "🚀 Starting BO Workflow Container..." -ForegroundColor Cyan
Write-Host "Monitor Slack for notifications and Prefect UI at: http://$HOST_IP:4200" -ForegroundColor Yellow
Write-Host ""

docker run --rm `
    -e PREFECT_API_URL="http://$HOST_IP:4200/api" `
    -e SLACK_WEBHOOK_URL="$SLACK_URL" `
    bo-workflow

Write-Host ""
Write-Host "✅ Workflow completed!" -ForegroundColor Green