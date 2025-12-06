"""
Human-in-the-Loop Bayesian Optimization with Ax, Prefect and Slack

Demonstrates a BO campaign where:
1. Ax suggests parameters via Service API
2. Slack notification sent with parameters
3. Human evaluates via HuggingFace Branin space
4. Human enters objective value in Prefect UI
5. Loop continues for n iterations
"""

import os
import json
from datetime import datetime
from pymongo import MongoClient
from ax.service.ax_client import AxClient, ObjectiveProperties
from prefect import flow, get_run_logger
from prefect.blocks.notifications import SlackWebhook
from prefect.context import get_run_context
from prefect.input import RunInput
from prefect.flow_runs import pause_flow_run
from prefect.blocks.system import Secret


class ExperimentInput(RunInput):
    """Input model for experiment evaluation"""
    objective_value: float
    notes: str = ""


@flow(name="bo-hitl-slack-campaign")
def run_bo_campaign(n_iterations: int = 5, random_seed: int = 42, slack_block_name: str = "tutorial-slack-webhook-url", mongodb_block_name: str = "tutorial-mongodb-uri"):
    """
    Bayesian Optimization campaign with human-in-the-loop evaluation via Slack
    
    Args:
        n_iterations: Number of BO iterations to run
        random_seed: Seed for Ax reproducibility
        slack_block_name: Name of the Prefect Slack webhook block
        mongodb_block_name: Name of the Prefect Secret block containing MongoDB URI
    """
    logger = get_run_logger()
    logger.info(f"Starting BO campaign with {n_iterations} iterations")
    
    # Initialize Ax client with Service API
    ax_client = AxClient(random_seed=random_seed)
    ax_client.create_experiment(
        name="branin_bo_experiment",
        parameters=[
            {"name": "x1", "type": "range", "bounds": [-5.0, 10.0], "value_type": "float"},
            {"name": "x2", "type": "range", "bounds": [0.0, 15.0], "value_type": "float"},
        ],
        objectives={"branin": ObjectiveProperties(minimize=True)}
    )
    
    # Load Slack webhook
    slack_block = SlackWebhook.load(slack_block_name)
    
    # Connect to MongoDB Atlas for storage using Prefect Secret block
    mongodb_secret = Secret.load(mongodb_block_name)
    mongodb_uri = mongodb_secret.get()
    mongo_client = MongoClient(mongodb_uri) if mongodb_uri else None
    logger.info(f"Connected to MongoDB using block '{mongodb_block_name}'")
    
    db = mongo_client["bo_experiments"] if mongo_client else None
    
    # Create experiment record
    experiment_id = f"exp_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
    if db is not None:
        db.experiments.insert_one({
            "experiment_id": experiment_id,
            "created_at": datetime.utcnow(),
            "n_iterations": n_iterations,
            "random_seed": random_seed,
            "status": "running"
        })
    
    results = []
    
    for iteration in range(n_iterations):
        logger.info(f"Iteration {iteration + 1}/{n_iterations}")
        
        # Get next suggestion from Ax
        parameters, trial_index = ax_client.get_next_trial()
        x1, x2 = parameters['x1'], parameters['x2']
        
        logger.info(f"Suggested: x1={x1}, x2={x2}")
        
        # Build Prefect Cloud UI URL - use workspace ID format
        flow_run = get_run_context().flow_run
        # Default to generic dashboard URL that will handle authentication and routing
        account_id = os.getenv("PREFECT_ACCOUNT_ID", "5b838504-64cf-4297-9b35-b881ac6169b3")
        workspace_id = os.getenv("PREFECT_WORKSPACE_ID", "d2718b4c-b49a-43ce-83c2-baf6fb3b9665")
        base_url = os.getenv("PREFECT_UI_URL", "https://app.prefect.cloud")
        flow_run_url = f"{base_url}/account/{account_id}/workspace/{workspace_id}/flow-runs/flow-run/{flow_run.id}" if flow_run else ""
        
        # Send Slack notification
        message = f"""*BO Iteration {iteration + 1}/{n_iterations}*

        Evaluate Branin function at:
        - x1 = {x1}
        - x2 = {x2}

        Use: https://huggingface.co/spaces/AccelerationConsortium/branin

        <{flow_run_url}|Click here to resume> and enter the objective value."""
        
        slack_block.notify(message)
        
        # Pause for human input
        logger.info("Waiting for human evaluation...")
        user_input = pause_flow_run(
            wait_for_input=ExperimentInput.with_initial_data(
                description=f"Enter objective value for x1={x1}, x2={x2}"
            )
        )
        
        objective_value = user_input.objective_value
        logger.info(f"Received: {objective_value}")
        
        # Complete trial in Ax
        ax_client.complete_trial(trial_index=trial_index, raw_data=objective_value)
        
        # Store trial result
        trial_result = {
            "iteration": iteration + 1,
            "trial_index": trial_index,
            "parameters": parameters,
            "objective_value": objective_value,
            "notes": user_input.notes,
            "timestamp": datetime.utcnow()
        }
        results.append(trial_result)
        
        # Save to MongoDB
        if db is not None:
            db.trials.insert_one({
                "experiment_id": experiment_id,
                **trial_result
            })
        
        logger.info(f"Completed iteration {iteration + 1}")
    
    # Get best parameters
    best_parameters, best_values = ax_client.get_best_parameters()
    
    # Update experiment status
    if db is not None:
        db.experiments.update_one(
            {"experiment_id": experiment_id},
            {"$set": {"status": "completed", "completed_at": datetime.utcnow(), 
                      "best_parameters": best_parameters, "best_value": best_values[0]['branin']}}
        )
    
    # Send completion notification
    slack_block.notify(f"""*BO Campaign Completed*

Best parameters: x1={best_parameters['x1']}, x2={best_parameters['x2']}
Best value: {best_values[0]['branin']}
Experiment ID: {experiment_id}""")
    
    logger.info(f"Campaign complete. Best: {best_parameters}, Value: {best_values}")
    
    # Export data to JSON files
    if db is not None:
        # Create experiment_data folder if it doesn't exist
        os.makedirs('experiment_data', exist_ok=True)
        
        logger.info("Exporting experiments...")
        experiments = list(db.experiments.find())
        with open('experiment_data/bo_experiments.json', 'w') as f:
            json.dump(experiments, f, indent=2, default=str)
        
        logger.info("Exporting trials...")
        trials = list(db.trials.find())
        with open('experiment_data/bo_trials.json', 'w') as f:
            json.dump(trials, f, indent=2, default=str)
            
        summary = {"experiments": experiments, "trials": trials}
        with open('experiment_data/bo_data_complete.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
    
    if mongo_client:
        mongo_client.close()
    
    return ax_client, results, experiment_id


run_bo_campaign(n_iterations=5, random_seed=42)