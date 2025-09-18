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
import math
import time
from typing import Dict, List, Tuple

# Try to import Ax (Service API as requested), fall back to mock implementation
try:
    from ax.service.ax_client import AxClient, ObjectiveProperties
    from ax.utils.measurement.synthetic_functions import branin
    AX_AVAILABLE = True
    print("✓ Ax Service API loaded successfully")
except ImportError:
    print("⚠ Ax not available, using mock implementation for development")
    AX_AVAILABLE = False

try:
    from prefect import flow, get_run_logger, settings, task
    from prefect.blocks.notifications import SlackWebhook
    from prefect.context import get_run_context
    from prefect.input import RunInput
    from prefect.flow_runs import pause_flow_run
    PREFECT_AVAILABLE = True
    print("✓ Prefect loaded successfully")
except ImportError:
    print("✗ Prefect not available - please install: pip install prefect prefect-slack")
    PREFECT_AVAILABLE = False
    exit(1)


# Mock Ax implementation for when the library is not available
class MockAxClient:
    """Mock implementation of AxClient using Service API pattern"""
    def __init__(self):
        self.trial_count = 0
        self.completed_trials = []
        self.experiment_name = None
        
    def create_experiment(self, name: str, parameters: List[Dict], objectives: Dict):
        """Mock experiment creation following Service API"""
        self.experiment_name = name
        self.parameters = parameters
        self.objectives = objectives
        print(f"Created mock experiment: {name}")
        print(f"Parameters: {[p['name'] for p in parameters]}")
        print(f"Objectives: {list(objectives.keys())}")
        
    def get_next_trial(self) -> Tuple[Dict, int]:
        """Mock trial generation using Service API pattern"""
        import random
        self.trial_count += 1
        
        # Generate parameters within the Branin function domain
        parameters = {
            "x1": random.uniform(-5.0, 10.0),
            "x2": random.uniform(0.0, 15.0)
        }
        return parameters, self.trial_count
        
    def complete_trial(self, trial_index: int, raw_data: float):
        """Mock trial completion using Service API pattern"""
        self.completed_trials.append((trial_index, raw_data))
        print(f"Completed trial {trial_index} with value {raw_data:.4f}")
        
    def get_best_parameters(self):
        """Get best parameters so far"""
        if not self.completed_trials:
            return None
        best_trial = min(self.completed_trials, key=lambda x: x[1])
        return {"trial_index": best_trial[0], "value": best_trial[1]}


def mock_branin(x1: float, x2: float) -> float:
    """
    Mock Branin function implementation
    Global minimum at (π, 2.275) and (-π, 12.275) and (9.42478, 2.475) with value 0.397887
    """
    a = 1
    b = 5.1 / (4 * math.pi**2)
    c = 5 / math.pi
    r = 6
    s = 10
    t = 1 / (8 * math.pi)
    
    return a * (x2 - b * x1**2 + c * x1 - r)**2 + s * (1 - t) * math.cos(x1) + s


class ExperimentInput(RunInput):
    """Input model for experiment evaluation"""
    objective_value: float
    notes: str = ""
    
    class Config:
        description = "Please evaluate the suggested experiment and enter the objective value"


@task
def setup_ax_client() -> MockAxClient if not AX_AVAILABLE else AxClient:
    """Initialize the Ax client with Branin function optimization setup using Service API"""
    logger = get_run_logger()
    
    if AX_AVAILABLE:
        ax_client = AxClient()
        logger.info("Using real Ax Service API")
    else:
        ax_client = MockAxClient()
        logger.info("Using mock Ax implementation")
    
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
        objectives={"branin": ObjectiveProperties(minimize=True)} if AX_AVAILABLE else {"branin": "minimize"}
    )
    
    logger.info("Initialized Ax client for Branin function optimization")
    return ax_client


@task 
def get_next_suggestion(ax_client) -> Tuple[Dict, int]:
    """Get the next experiment suggestion from Ax using Service API"""
    logger = get_run_logger()
    
    parameters, trial_index = ax_client.get_next_trial()
    logger.info(f"Generated trial {trial_index}: x1={parameters['x1']:.3f}, x2={parameters['x2']:.3f}")
    
    return parameters, trial_index


@task
def complete_experiment(ax_client, trial_index: int, objective_value: float):
    """Complete the experiment with the human-evaluated objective value using Service API"""
    logger = get_run_logger()
    
    ax_client.complete_trial(trial_index=trial_index, raw_data=objective_value)
    logger.info(f"Completed trial {trial_index} with objective value {objective_value:.4f}")


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
    try:
        slack_block = SlackWebhook.load("prefect-test")
        logger.info("✓ Slack webhook block loaded successfully")
    except Exception as e:
        logger.warning(f"Could not load Slack block: {e}")
        logger.info("Continue without Slack notifications - check Prefect UI for pauses")
        slack_block = None
    
    # Initialize the Ax client using Service API
    ax_client = await setup_ax_client()
    
    logger.info(f"🚀 Starting BO campaign with {n_iterations} iterations")
    logger.info("Following the minimal working example workflow:")
    logger.info("1. Script starts BO campaign via Ax")
    logger.info("2. Ax suggests → Slack message (HiTL)")
    logger.info("3. User evaluates via HuggingFace Branin")
    logger.info("4. User resumes via Prefect UI")
    logger.info("5. Loop continues 4-5 times")
    
    # Main optimization loop
    for iteration in range(n_iterations):
        logger.info(f"\n--- Iteration {iteration + 1}/{n_iterations} ---")
        
        # Get next experiment suggestion using Service API
        parameters, trial_index = await get_next_suggestion(ax_client)
        
        # Create message for human evaluator
        message = f"""
🧪 **Bayesian Optimization - Experiment {iteration + 1}/{n_iterations}**

**Suggested Parameters (via Ax Service API):**
• x1 = {parameters['x1']:.4f}
• x2 = {parameters['x2']:.4f}

**Your Task:**
1. Go to: https://huggingface.co/spaces/AccelerationConsortium/branin
2. Enter x1 = {parameters['x1']:.4f}, x2 = {parameters['x2']:.4f}
3. Record the Branin function value
4. Return to Prefect and click "Resume" to enter the result

**Branin Function Info:**
• Global minimum ≈ 0.398 at (π, 2.275), (-π, 12.275), or (9.42478, 2.475)
• We're trying to minimize this function
• Expected value: {mock_branin(parameters['x1'], parameters['x2']):.4f}

**Trial:** {trial_index}
        """.strip()
        
        # Send Slack notification if available
        if slack_block:
            flow_run = get_run_context().flow_run
            if flow_run and settings.PREFECT_UI_URL:
                flow_run_url = f"{settings.PREFECT_UI_URL.value()}/flow-runs/flow-run/{flow_run.id}"
                message += f"\n\n**Resume Flow:** <{flow_run_url}|Click here to resume>"
            
            try:
                await slack_block.notify(message)
                logger.info("📱 Sent Slack notification for experiment evaluation")
            except Exception as e:
                logger.warning(f"Failed to send Slack notification: {e}")
        
        # Pause for human input - this is the key HiTL step
        logger.info("⏸️ Pausing for human evaluation via Prefect UI...")
        experiment_result = await pause_flow_run(
            wait_for_input=ExperimentInput.with_initial_data(
                description=f"**Experiment {iteration + 1}/{n_iterations}**: Evaluate x1={parameters['x1']:.4f}, x2={parameters['x2']:.4f}",
                objective_value=0.0  # Default/placeholder value
            ),
            timeout=600  # 10 minutes timeout
        )
        
        # Complete the experiment using Service API
        await complete_experiment(ax_client, trial_index, experiment_result.objective_value)
        
        logger.info(f"✅ Completed iteration {iteration + 1} with value {experiment_result.objective_value:.4f}")
        
        if experiment_result.notes:
            logger.info(f"📝 User notes: {experiment_result.notes}")
    
    # Final summary
    logger.info("\n🎉 BO Campaign Completed!")
    logger.info(f"Ran {n_iterations} iterations with human-in-the-loop evaluation")
    
    # Show best result if using mock implementation
    if not AX_AVAILABLE and hasattr(ax_client, 'get_best_parameters'):
        best = ax_client.get_best_parameters()
        if best:
            logger.info(f"🏆 Best result: trial {best['trial_index']} with value {best['value']:.4f}")
    
    if slack_block:
        try:
            await slack_block.notify(f"✅ BO Campaign completed! Ran {n_iterations} iterations using Ax Service API.")
        except Exception as e:
            logger.warning(f"Failed to send completion notification: {e}")


if __name__ == "__main__":
    print("🚀 Bayesian Optimization Human-in-the-Loop Tutorial")
    print("=" * 60)
    print("This tutorial demonstrates the minimal working example:")
    print("1. User runs Python script starting BO campaign via Ax")
    print("2. Ax suggests experiment → triggers Prefect Slack message (HiTL)")  
    print("3. User evaluates experiment using HuggingFace Branin space")
    print("4. User resumes Prefect flow via UI with objective value")
    print("5. Loop continues for 4-5 iterations")
    print()
    print("Setup Requirements:")
    print("- Prefect server running: prefect server start")
    print("- SlackWebhook block named 'prefect-test' configured")
    print("- Access to https://huggingface.co/spaces/AccelerationConsortium/branin")
    print("- Dependencies: pip install ax-platform prefect prefect-slack")
    print("=" * 60)
    
    # Run the campaign
    asyncio.run(bo_hitl_slack_campaign())