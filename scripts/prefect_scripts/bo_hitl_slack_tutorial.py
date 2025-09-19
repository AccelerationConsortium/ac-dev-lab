#!/usr/bin/env python3
"""
Bayesian Optimization with Prefect Human-in-the-Loop Slack Integration Tutorial

This script demonstrates a complete BO campaign with human evaluation via Slack.
The user receives Slack notifications with experiment suggestions, evaluates them
using the Branin function (via HuggingFace space), and resumes the workflow.

This is the minimal working example described in the issue requirements:
1. User runs Python script starting BO campaign with Ax
2. Ax suggests experiment → triggers Prefect Slack message (HiTL)  
3. User evaluates experiment using HuggingFace Branin space
4. User resumes Prefect flow via UI with objective value
5. Loop continues for 4-5 iterations

Requirements:
- Prefect server running: prefect server start
- Slack webhook configured as "prefect-test" block
- Internet access to HuggingFace spaces
- Dependencies: pip install ax-platform prefect prefect-slack

Setup Instructions:
1. Start Prefect server: prefect server start
2. Configure Slack webhook block (see README for details)
3. Run: python bo_hitl_slack_tutorial.py

Usage:
    python bo_hitl_slack_tutorial.py
"""

import asyncio
from typing import Dict, Tuple

from ax.service.ax_client import AxClient, ObjectiveProperties
from prefect import flow, get_run_logger, settings, task
from prefect.blocks.notifications import SlackWebhook
from prefect.context import get_run_context
from prefect.input import RunInput
from prefect.flow_runs import pause_flow_run

class ExperimentInput(RunInput):
    """Input model for experiment evaluation"""
    objective_value: float
    notes: str = ""


def setup_ax_client() -> AxClient:
    """Initialize the Ax client with Branin function optimization setup using Service API"""
    ax_client = AxClient()
    
    # Define the optimization problem for the Branin function using Service API pattern
    ax_client.create_experiment(
        name="branin_bo_hitl_experiment",
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


@flow(name="bo-hitl-slack-campaign")
async def bo_hitl_slack_campaign(n_iterations: int = 5):
    """
    Main BO campaign with human-in-the-loop evaluation via Slack
    
    This implements the exact workflow described in the issue:
    1. User runs Python script starting BO campaign with Ax
    2. Ax suggests experiment → triggers Prefect Slack message (HiTL)  
    3. User evaluates experiment using HuggingFace Branin space
    4. User resumes Prefect flow via UI with objective value
    5. Loop continues for 4-5 iterations
    
    Args:
        n_iterations: Number of BO iterations to run
    """
    logger = get_run_logger()
    
    # Load the Slack webhook block
    slack_block = SlackWebhook.load("prefect-test")
    
    # Initialize the Ax client using Service API
    ax_client = setup_ax_client()
    
    logger.info(f"Starting BO campaign with {n_iterations} iterations")
    
    # Main optimization loop
    for iteration in range(n_iterations):
        logger.info(f"Iteration {iteration + 1}/{n_iterations}")
        
        # Get next experiment suggestion using Service API
        parameters, trial_index = get_next_suggestion(ax_client)
        
        # Create message for human evaluator
        message = f"""
Bayesian Optimization - Experiment {iteration + 1}/{n_iterations}

Suggested Parameters (via Ax Service API):
• x1 = {parameters['x1']}
• x2 = {parameters['x2']}

Your Task:
1. Go to: https://huggingface.co/spaces/AccelerationConsortium/branin
2. Enter x1 = {parameters['x1']}, x2 = {parameters['x2']}
3. Record the Branin function value
4. Return to Prefect and click "Resume" to enter the result

Trial: {trial_index}
        """.strip()
        
        # Send Slack notification
        flow_run = get_run_context().flow_run
        if flow_run and settings.PREFECT_UI_URL:
            flow_run_url = f"{settings.PREFECT_UI_URL.value()}/flow-runs/flow-run/{flow_run.id}"
            message += f"\n\nResume Flow: <{flow_run_url}|Click here to resume>"
        
        await slack_block.notify(message)
        
        # Pause for human input
        experiment_result = await pause_flow_run(
            wait_for_input=ExperimentInput,
            timeout=600  # 10 minutes timeout
        )
        
        # Complete the experiment using Service API
        complete_experiment(ax_client, trial_index, experiment_result.objective_value)
        
        logger.info(f"Completed iteration {iteration + 1} with value {experiment_result.objective_value}")
    
    logger.info("BO Campaign Completed!")
    await slack_block.notify(f"BO Campaign completed! Ran {n_iterations} iterations using Ax Service API.")

if __name__ == "__main__":
    asyncio.run(bo_hitl_slack_campaign())