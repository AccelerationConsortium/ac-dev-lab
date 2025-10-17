# Bayesian Optimization Human-in-the-Loop Slack Integration Tutorial

This tutorial demonstrates a complete Bayesian Optimization workflow with human evaluation via Slack and Prefect for evaluating the Branin function.

## Overview

The minimal working example implements this exact workflow:

1. **User runs Python script** starting BO campaign via Ax
2. **Ax suggests parameters** → sends notification to Slack with parameter values 
3. **User evaluates Branin function** using HuggingFace space or API
4. **User resumes Prefect flow** via Slack link and enters the objective value
5. **Loop continues** for 5 iterations, finding optimal parameters
6. **Final results** are posted to Slack with the best parameters found

## Setup Instructions

### 1. Install Dependencies

```bash
# For Windows PowerShell
pip install ax-platform prefect prefect-slack gradio_client

# For Unix/Linux
# export PIP_TIMEOUT=600
# export PIP_RETRIES=2
# pip install ax-platform prefect prefect-slack gradio_client
```

### 2. Register and Configure Slack Block

```bash
# Register the Slack block 
prefect block register -m prefect_slack

# Check available blocks
prefect block ls
```

You need to create a SlackWebhook block named "prefect-test" via the Prefect UI:

```python
from prefect.blocks.notifications import SlackWebhook

# Create the webhook block
slack_webhook_block = SlackWebhook(
    url="YOUR_SLACK_WEBHOOK_URL"  # Get this from Slack Apps
)

# Save it with the name expected by the tutorial
slack_webhook_block.save("prefect-test")
```

### 3. Start Prefect Server

```bash
prefect server start
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

### Optimization Problem

The tutorial optimizes the Branin function, a common benchmark in Bayesian Optimization:

- **Function**: Branin function (to be minimized)
- **Parameters**:
  - x1 ∈ [-5.0, 10.0]
  - x2 ∈ [0.0, 15.0]
- **Goal**: Find parameter values that minimize the function

### Workflow Steps

1. **Script starts** - Initializes Ax Service API client with proper parameter bounds
2. **Ax suggests parameters** - Using Bayesian Optimization algorithms
3. **Slack notification** - Sends parameter values and API instructions to Slack
4. **Human evaluation** - User evaluates the function via:
   - HuggingFace Space UI: https://huggingface.co/spaces/AccelerationConsortium/branin
   - OR using the provided Python code snippet with gradio_client
5. **Resume in Prefect** - User clicks the link in Slack message to open Prefect UI
6. **Enter result** - User inputs the objective value from HuggingFace in Prefect UI
7. **Optimization continues** - Ax uses the result to suggest better parameters
8. **Repeat** - Process continues for 5 iterations
9. **Final results** - Best parameters and value are displayed and sent to Slack

## Expected Output

The tutorial will:
- Generate 5 experiment suggestions using Bayesian Optimization
- Send Slack messages with parameters and detailed API instructions
- Include a direct link in the Slack message to resume the Prefect flow
- Pause execution waiting for human input via the Prefect UI
- Resume when user provides objective values and optional notes
- Show optimization progress in the terminal logs
- Send a final summary to Slack with the best parameters found

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

- **Prefect server not running**: Start with `prefect server start`
- **Slack block missing**: Configure SlackWebhook block named "prefect-test"
- **Dependencies missing**: Install with `pip install ax-platform prefect prefect-slack gradio_client`
- **PREFECT_UI_URL not set**: Set with `prefect config set PREFECT_API_URL=http://127.0.0.1:4200/api`
- **HuggingFace API errors**: Ensure parameters are within bounds (x1: [-5.0, 10.0], x2: [0.0, 15.0])

## Technical Details

### Ax Configuration

The script uses the Ax Service API to set up the optimization problem:

```python
ax_client.create_experiment(
    name="branin_bo_experiment",
    parameters=[
        {
            "name": "x1",
            "type": "range", 
            "bounds": [-5.0, 10.0],
            "value_type": "float",
        },
        {
            "name": "x2",
            "type": "range",
            "bounds": [0.0, 15.0],
            "value_type": "float", 
        },
    ],
    objectives={"branin": ObjectiveProperties(minimize=True)}
)
```

### Prefect-Slack Integration

The workflow uses the Prefect pause functionality combined with Slack notifications:
- Prefect pause_flow_run waits for user input
- Slack notification contains a link to resume the flow
- User input is captured using a custom ExperimentInput model

## References

- [Ax Documentation](https://ax.dev/)
- [Prefect Interactive Workflows](https://docs.prefect.io/latest/guides/creating-interactive-workflows/)
- [HuggingFace Branin Space](https://huggingface.co/spaces/AccelerationConsortium/branin)
- [Prefect Slack Integration](https://docs.prefect.io/latest/integrations/notifications/)