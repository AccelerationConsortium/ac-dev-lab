# 🐳 Containerized Bayesian Optimization HITL Workflow - Deployment Guide

This guide explains how to run the containerized Bayesian Optimization Human-in-the-Loop workflow on any machine.

## 📋 Prerequisites

### Required Software
- **Docker Desktop** (Windows/Mac) or **Docker Engine** (Linux)
- **Git** (to clone the repository)
- **Slack workspace** (for notifications)

### System Requirements
- **RAM:** 4GB+ available
- **Storage:** 2GB+ free space
- **Network:** Internet connection for Docker images and Slack

## 🚀 Step-by-Step Deployment

### Step 1: Clone the Repository
```bash
git clone https://github.com/Daniel0813/ac-dev-lab.git
cd ac-dev-lab/bo-containerized
```

### Step 2: Set Up Slack Integration

#### Option A: Use Your Own Slack Workspace
1. **Create Slack App:**
   - Go to https://api.slack.com/apps
   - Click "Create New App" → "From scratch"
   - Name: "BO Workflow Bot"
   - Choose your workspace

2. **Enable Incoming Webhooks:**
   - In your app settings, go to "Incoming Webhooks"
   - Toggle "Activate Incoming Webhooks" to On
   - Click "Add New Webhook to Workspace"
   - Choose the channel for notifications
   - Copy the webhook URL (looks like: `https://hooks.slack.com/services/...`)

#### Option B: Skip Slack (Test Mode)
If you don't want Slack notifications, you can skip them by commenting out the Slack code.

### Step 3: Configure Network Settings

#### Find Your Host IP Address

**Windows:**
```powershell
ipconfig | findstr IPv4
```

**Mac/Linux:**
```bash
ifconfig | grep "inet " | grep -v 127.0.0.1
```

You'll see something like: `192.168.1.100` - this is your HOST_IP.

### Step 4: Start Prefect Server

**IMPORTANT:** Start Prefect server in a separate terminal that stays open!

#### Windows:
```powershell
# Install Prefect (if not already installed)
pip install prefect==3.4.19 prefect-slack==0.3.1

# Start server in new window (keeps running)
Start-Process powershell -ArgumentList "-NoExit", "-Command", "prefect server start --host 0.0.0.0"
```

#### Mac/Linux:
```bash
# Install Prefect (if not already installed)
pip install prefect==3.4.19 prefect-slack==0.3.1

# Start server (in background or separate terminal)
prefect server start --host 0.0.0.0 &
```

**Wait 30 seconds** for server to fully start, then verify:
```bash
# Should show port 4200 listening
netstat -an | grep :4200
```

### Step 5: Build the Docker Image

```bash
# Navigate to the bo-containerized directory
cd bo-containerized

# Build the image (takes 20-30 minutes first time)
docker build -t bo-workflow .
```

### Step 6: Run the Containerized Workflow

#### Option A: With Custom Slack Webhook
```bash
docker run --rm \
  -e SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL" \
  -e PREFECT_API_URL="http://YOUR_HOST_IP:4200/api" \
  bo-workflow
```

#### Option B: Use Default Configuration
```bash
# Edit Dockerfile to set your values, then rebuild
docker build -t bo-workflow .
docker run --rm bo-workflow
```

#### Option C: Interactive Run (See Logs)
```bash
docker run --rm -it \
  -e PREFECT_API_URL="http://YOUR_HOST_IP:4200/api" \
  bo-workflow
```

## 🔧 Configuration Options

### Environment Variables You Can Override

| Variable | Description | Example |
|----------|-------------|---------|
| `PREFECT_API_URL` | Prefect server endpoint | `http://192.168.1.100:4200/api` |
| `SLACK_WEBHOOK_URL` | Slack webhook for notifications | `https://hooks.slack.com/services/...` |

### Example Commands

**Full Custom Configuration:**
```bash
docker run --rm \
  -e PREFECT_API_URL="http://192.168.1.100:4200/api" \
  -e SLACK_WEBHOOK_URL="https://hooks.slack.com/services/T123/B456/xyz789" \
  bo-workflow
```

**Run Specific Number of Iterations:**
```bash
# Modify the Python script parameters if needed
docker run --rm bo-workflow python complete_workflow/bo_hitl_slack_tutorial.py --iterations 10
```

## 🎯 What Happens When You Run It

1. **Container starts** → Loads Python 3.12 + all dependencies
2. **Connects to Prefect** → Registers the BO workflow
3. **Starts BO campaign** → Suggests parameter values using Ax platform
4. **Sends Slack notification** → With parameters and HuggingFace link
5. **Pauses for human input** → Waits for you to evaluate function
6. **Continues optimization** → Uses your feedback to improve suggestions
7. **Repeats 5 iterations** → Or until manually stopped

## 📱 Using the Workflow

### When You Get a Slack Notification:

1. **Copy the parameters** (x1, x2 values)
2. **Evaluate the function:**
   - Visit: https://huggingface.co/spaces/AccelerationConsortium/branin
   - Enter the x1 and x2 values
   - Get the result
3. **Resume the flow:**
   - Click the Prefect link in Slack
   - Enter the objective value
   - Workflow continues automatically

### Alternative - Use Python API:
```python
from gradio_client import Client

client = Client("AccelerationConsortium/branin")
result = client.predict(
    9.96,  # x1 value from Slack
    1.57,  # x2 value from Slack
    api_name="/predict"
)
print(result)
```

## 🔍 Troubleshooting

### Common Issues:

**"Can't connect to Prefect server"**
```bash
# Check server is running
netstat -an | grep :4200

# Check Docker can reach host
docker run --rm alpine ping -c 1 YOUR_HOST_IP
```

**"Slack notifications not working"**
- Verify webhook URL is correct
- Test webhook: `curl -X POST -H 'Content-type: application/json' --data '{"text":"Test"}' YOUR_WEBHOOK_URL`

**"Docker build fails"**
- Ensure stable internet connection (downloads ~2GB)
- Check available disk space (needs ~5GB)
- Try: `docker system prune` to free space

**"Flow doesn't resume"**
- Check Prefect UI is accessible at `http://YOUR_HOST_IP:4200`
- Ensure server started with `--host 0.0.0.0` flag

### Getting Help:

**Check logs:**
```bash
# See container logs
docker logs CONTAINER_ID

# See Prefect server logs
# Check the terminal where server is running
```

**Test components individually:**
```bash
# Test Prefect connection
docker run --rm bo-workflow python -c "from prefect import get_client; print('Connected!')"

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' --data '{"text":"Test message"}' YOUR_WEBHOOK_URL
```

## 🏆 Success Indicators

You know it's working when you see:
- ✅ "Starting Bayesian Optimization HITL campaign"
- ✅ "Slack notification sent"  
- ✅ "Pausing flow, execution will continue when resumed"
- ✅ Slack message with parameters and Prefect link
- ✅ Able to click link and resume workflow

## 🔒 Security Notes

- The default Slack webhook is public in this demo - replace with your own
- Prefect server runs without authentication - suitable for local/demo use
- Container runs as root - consider adding user security for production

## 📈 Next Steps

Once running successfully:
- Modify `complete_workflow/bo_hitl_slack_tutorial.py` for your use case
- Add database storage for experiment history
- Implement custom objective functions
- Scale to multiple parallel experiments

---

**Need help?** Open an issue in the repository or contact the development team.