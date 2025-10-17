# 🐳 Containerized BO HITL Workflow

A containerized Bayesian Optimization Human-in-the-Loop workflow using Docker, Prefect, Ax, and Slack for easy deployment across different environments.

## 🚀 Quick Start

### 1. Build the Container
```bash
docker build -t bo-hitl-workflow .
```

### 2. Start Prefect Server (in separate terminal)
```bash
prefect server start
```

### 3. Run the BO Workflow
```bash
docker run --rm -it \
  --network host \
  -e SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK \
  bo-hitl-workflow
```

## 📋 What's Included

- **BO Workflow**: `bo_hitl_slack_tutorial.py` - Your complete Bayesian Optimization workflow
- **Deployment Script**: `create_bo_hitl_deployment.py` - Prefect deployment configuration
- **Auto Setup**: Automatic Slack webhook configuration
- **Dependencies**: All required packages with compatible versions

## 🔧 Environment Variables

- `SLACK_WEBHOOK_URL`: Your Slack webhook URL (already configured)
- `PREFECT_API_URL`: Prefect server URL (default: http://host.docker.internal:4200/api)

## 🏃‍♂️ Usage Options

### Option 1: Run with Setup (Recommended)
```bash
# Setup Slack webhook and run workflow
docker run --rm -it --network host bo-hitl-workflow python setup.py
```

### Option 2: Custom Parameters
```bash
# Run with custom campaign settings
docker run --rm -it --network host bo-hitl-workflow \
  python complete_workflow/bo_hitl_slack_tutorial.py
```

### Option 3: Interactive Shell
```bash
# Get shell access to explore
docker run --rm -it --network host bo-hitl-workflow bash
```

## 📦 Dependencies

- Python 3.12
- ax-platform (Bayesian Optimization)
- prefect 3.0.x (Workflow orchestration - compatible version)
- prefect-slack (Slack notifications)
- numpy (Scientific computing)

**Note**: gradio-client excluded due to websockets version conflict. Install separately if needed for HuggingFace API access.

## 🤝 Collaboration Benefits

- ✅ **Consistent Environment**: Same Python/package versions everywhere
- ✅ **Easy Setup**: One `docker run` command to start
- ✅ **No Installation Hassles**: All dependencies included
- ✅ **Cross-Platform**: Works on Windows, Mac, Linux

## 🔍 Troubleshooting

**Prefect Connection Issues:**
- Make sure Prefect server is running: `prefect server start`
- Check the Prefect UI at: http://localhost:4200

**Slack Notifications Not Working:**
- Verify webhook URL is correct
- Test webhook with: `python setup.py`

**Container Won't Start:**
- Check Docker is running: `docker --version`
- Rebuild image: `docker build -t bo-hitl-workflow . --no-cache`