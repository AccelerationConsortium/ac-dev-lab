#!/usr/bin/env python3
"""
Human-in-the-Loop Bayesian Optimization Campaign with Ax, Prefect and Slack

This script demonstrates a human-in-the-loop Bayesian Optimization campaign using Ax,
with Prefect for workflow management and Slack for notifications.

Requirements:
- Dependencies: 
  pip install ax-platform prefect prefect-slack gradio_client

Setup:
1. Register the Slack block:
   prefect block register -m prefect_slack

2. Create a Slack webhook block named 'prefect-test':
   - Create a Slack app with an incoming webhook
   - In the Prefect UI, create a new Slack Webhook block
   - Name it 'prefect-test'
   - Add your Slack webhook URL
   
3. Start the Prefect server if not running:
   prefect server start

Usage:
    python bo_hitl_slack_tutorial.py
"""

import sys
import os
import numpy as np
from typing import Dict, Tuple

# Ensure we can import Ax
try:
    from ax.service.ax_client import AxClient, ObjectiveProperties
except ImportError:
    print("Installing required packages...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "ax-platform"])
    from ax.service.ax_client import AxClient, ObjectiveProperties

# Define our own Branin function since ax.utils.measurement.synthetic_functions might not be available
def branin(x1, x2):
    """Branin synthetic benchmark function"""
    a = 1
    b = 5.1 / (4 * np.pi**2)
    c = 5 / np.pi
    r = 6
    s = 10
    t = 1 / (8 * np.pi)
    
    return a * (x2 - b * x1**2 + c * x1 - r)**2 + s * (1 - t) * np.cos(x1) + s

# Import Prefect and Slack for HITL workflow
import asyncio
from prefect import flow, get_run_logger, settings, task
from prefect.blocks.notifications import SlackWebhook
from prefect.context import get_run_context
from prefect.input import RunInput
from prefect.flow_runs import pause_flow_run

class ExperimentInput(RunInput):
    """Input model for experiment evaluation"""
    objective_value: float
    notes: str = ""


def setup_ax_client(random_seed: int = 42) -> AxClient:
    """Initialize the Ax client with Branin function optimization setup using Service API"""
    ax_client = AxClient(random_seed=random_seed)
    
    # Define the optimization problem for the Branin function using Service API pattern
    # Standard bounds for the Branin function are x1 ∈ [-5, 10] and x2 ∈ [0, 15]
    # Make sure these bounds match what's expected by the HuggingFace model
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
    
    return ax_client


def get_next_suggestion(ax_client: AxClient) -> Tuple[Dict, int]:
    """Get the next experiment suggestion from Ax using Service API"""
    return ax_client.get_next_trial()


def complete_experiment(ax_client: AxClient, trial_index: int, objective_value: float):
    """Complete the experiment with the human-evaluated objective value using Service API"""
    ax_client.complete_trial(trial_index=trial_index, raw_data=objective_value)


def evaluate_branin(parameters: Dict) -> float:
    """Evaluate the Branin function for the given parameters (automated evaluation)"""
    return float(branin(x1=parameters["x1"], x2=parameters["x2"]))

def generate_api_instructions(parameters: Dict) -> str:
    """Generate instructions for using the HuggingFace API to evaluate Branin function"""
    x1_value = parameters['x1']
    x2_value = parameters['x2']
    
    # Create a properly formatted Python code snippet with the values directly inserted
    code_snippet = f"""from gradio_client import Client

client = Client("AccelerationConsortium/branin")
result = client.predict(
    {x1_value},  # x1 value
    {x2_value},  # x2 value
    api_name="/predict"
)
print(result)"""
    
    instructions = f"""
Please evaluate the Branin function with the following parameters:
• x1 = {x1_value} (should be in range [-5.0, 10.0])
• x2 = {x2_value} (should be in range [0.0, 15.0])

If these values are outside the allowed range of the HuggingFace model, please:
1. Clip x1 to be within [-5.0, 10.0]
2. Clip x2 to be within [0.0, 15.0]

Use the HuggingFace API by running this code:
```python
{code_snippet}
```

Or visit: https://huggingface.co/spaces/AccelerationConsortium/branin
Enter the x1 and x2 values in the interface, and submit the objective value below.
"""
    return instructions


@flow(name="bo-hitl-slack-campaign")
def run_bo_campaign(n_iterations: int = 5, random_seed: int = 42):
    """
    Main Bayesian Optimization campaign with human-in-the-loop evaluation via Slack
    
    This implements a human-in-the-loop workflow:
    1. User runs Python script starting BO campaign with Ax
    2. For each iteration:
       a. System suggests parameters
       b. System sends message to Slack
       c. Human evaluates function via HuggingFace API
       d. Human provides value back to system
       e. System continues optimization
    
    Args:
        n_iterations: Number of BO iterations to run
        random_seed: Seed for Ax reproducibility
    """
    logger = get_run_logger()
    logger.info(f"Starting BO campaign with {n_iterations} iterations")
    
    # Load or create the Slack webhook block
    try:
        slack_block = SlackWebhook.load("prefect-test")
        logger.info("Successfully loaded existing Slack webhook block")
    except ValueError:
        logger.info("Slack webhook block 'prefect-test' not found, creating it now...")
        # Get webhook URL from Prefect Variable
        from prefect.variables import Variable
        try:
            webhook_url = Variable.get("slack-webhook-url")
            slack_block = SlackWebhook(url=webhook_url)
            slack_block.save("prefect-test")
            logger.info("Successfully created Slack webhook block 'prefect-test'")
        except ValueError as e:
            logger.error(f"slack-webhook-url variable not found. Please set it with: prefect variable set slack-webhook-url 'your-webhook-url'")
            logger.info("Skipping Slack notifications for this run.")
            slack_block = None
    
    # Initialize the Ax client using Service API with seed
    ax_client = setup_ax_client(random_seed=random_seed)
    
    # Store all results for analysis
    results = []
    
    # Main optimization loop
    for iteration in range(n_iterations):
        logger.info(f"Iteration {iteration + 1}/{n_iterations}")
        
        # Get next experiment suggestion using Service API
        parameters, trial_index = get_next_suggestion(ax_client)
        
        logger.info(f"Suggested Parameters (via Ax Service API):")
        logger.info(f"• x1 = {parameters['x1']}")
        logger.info(f"• x2 = {parameters['x2']}")
        
        # Generate API instructions message
        api_instructions = generate_api_instructions(parameters)
        
        # Prepare Slack message
        flow_run = get_run_context().flow_run
        flow_run_url = ""
        if flow_run and settings.PREFECT_UI_URL:
            flow_run_url = f"{settings.PREFECT_UI_URL.value()}/flow-runs/flow-run/{flow_run.id}"
            
        message = f"""
*Bayesian Optimization - Iteration {iteration + 1}/{n_iterations}*

{api_instructions}

When you've evaluated the function, please <{flow_run_url}|click here to resume the flow> and enter the objective value.
"""
        
        # Send message to Slack (if configured)
        if slack_block:
            slack_block.notify(message)
        else:
            logger.info("Slack webhook not configured, skipping notification")
        
        # Pause flow and wait for human input
        logger.info("Pausing flow, execution will continue when this flow run is resumed.")
        user_input = pause_flow_run(
            wait_for_input=ExperimentInput.with_initial_data(
                description=f"Please enter the objective value for parameters: x1={parameters['x1']}, x2={parameters['x2']}"
            )
        )
        
        # Extract objective value from user input
        objective_value = user_input.objective_value
        logger.info(f"Received objective value: {objective_value}")
        
        # Complete the experiment using Service API
        complete_experiment(ax_client, trial_index, objective_value)
        
        # Store results
        results.append({
            "iteration": iteration + 1,
            "trial_index": trial_index,
            "parameters": parameters,
            "objective_value": objective_value,
            "notes": user_input.notes
        })
        
        logger.info(f"Completed iteration {iteration + 1} with value {objective_value}")
    
    # Get best parameters found
    best_parameters, best_values = ax_client.get_best_parameters()
    
    logger.info("\nBO Campaign Completed!")
    logger.info(f"Best parameters found: {best_parameters}")
    logger.info(f"Best objective value: {best_values}")
    
    # Send final results to Slack
    final_message = f"""
*Bayesian Optimization Campaign Completed!*

*Best parameters found:*
• x1 = {best_parameters['x1']}
• x2 = {best_parameters['x2']}

*Best objective value:* {best_values['branin']}

Thank you for participating in this human-in-the-loop optimization!
"""
    # Send final notification to Slack (if configured)
    if slack_block:
        slack_block.notify(final_message)
    else:
        logger.info("Slack webhook not configured, skipping final notification")
    
    return ax_client, results

if __name__ == "__main__":
    # Run the Prefect flow
    print("Starting Bayesian Optimization HITL campaign with Slack integration")
    print("Make sure you have set up your Slack webhook block named 'prefect-test'")
    print("You will receive Slack notifications for each iteration")
    
    # Run the flow
    ax_client, results = run_bo_campaign()