# Bayesian Optimization Human-in-the-Loop Slack Integration Tutorial

This tutorial demonstrates a complete Bayesian Optimization workflow with human evaluation via Slack and Prefect.

## Overview

The minimal working example implements this exact workflow:

1. **User runs Python script** starting BO campaign via Ax
2. **Ax suggests experiment** → triggers Prefect Slack message (HiTL)  
3. **User evaluates experiment** using HuggingFace Branin space
4. **User resumes Prefect flow** via UI with objective value
5. **Loop continues** for 4-5 iterations

## Setup Instructions

### 1. Install Dependencies

```bash
# Set environment variables as per copilot-instructions.md
export PIP_TIMEOUT=600
export PIP_RETRIES=2

# Install required packages
pip install ax-platform prefect prefect-slack
```

### 2. Start Prefect Server

```bash
prefect server start
```

### 3. Configure Slack Webhook Block

You need to create a SlackWebhook block named "prefect-test":

```python
from prefect.blocks.notifications import SlackWebhook

# Create the webhook block
slack_webhook_block = SlackWebhook(
    url="YOUR_SLACK_WEBHOOK_URL"  # Get this from Slack Apps
)

# Save it with the name expected by the tutorial
slack_webhook_block.save("prefect-test")
```

To get a Slack webhook URL:
1. Go to https://api.slack.com/apps
2. Create a new app or select existing
3. Enable "Incoming Webhooks" 
4. Create webhook for your channel
5. Copy the webhook URL

### 4. Run the Tutorial

```bash
cd scripts/prefect_scripts
python bo_hitl_slack_tutorial.py
```

## How It Works

1. **Script starts** - Initializes Ax Service API client
2. **Slack notification** - Sends experiment parameters to Slack
3. **Human evaluation** - User goes to HuggingFace space:
   - Visit: https://huggingface.co/spaces/AccelerationConsortium/branin
   - Enter the suggested x1, x2 values
   - Record the Branin function result
4. **Resume in Prefect** - Click the link in Slack to resume flow
5. **Enter result** - Input the objective value in Prefect UI
6. **Repeat** - Process continues for 4-5 iterations

## Expected Output

The tutorial will:
- Generate 5 experiment suggestions using Bayesian Optimization
- Send Slack messages with parameters and HuggingFace link
- Pause execution waiting for human input
- Resume when user provides objective values
- Show optimization progress and final results

## Demo Video Recording

For the video demonstration, show:
1. Running the Python script
2. Receiving Slack notification
3. Evaluating experiment on HuggingFace Branin space
4. Clicking Slack link to Prefect UI
5. Entering objective value and resuming
6. Repeating loop 4-5 times

## Files

- `bo_hitl_slack_tutorial.py` - Main tutorial script
- `README.md` - This setup guide

## Troubleshooting

- **Ax not installed**: Script will use mock implementation for development
- **Slack block missing**: Script continues without Slack notifications
- **Prefect server not running**: Start with `prefect server start`
- **Dependencies missing**: Install with pip using timeout/retry settings

## References

- [Ax Documentation](https://ax.dev/)
- [Prefect Interactive Workflows](https://docs.prefect.io/latest/guides/creating-interactive-workflows/)
- [HuggingFace Branin Space](https://huggingface.co/spaces/AccelerationConsortium/branin)