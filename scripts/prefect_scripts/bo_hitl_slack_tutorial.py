#!/usr/bin/env python3
"""
Human-in-the-Loop Bayesian Optimization Campaign with Ax, Prefect and Slack

This script demonstrates a human-in-the-loop Bayesian Optimization campaign using Ax,
with Prefect for workflow management and Slack for notifications.


"""

import sys
import os
import numpy as np
from typing import Dict, Tuple, List, Optional
from datetime import datetime
from pathlib import Path
import json
import time

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
    # Initialization strategy (also called "exploration phase")
    # by default is Sobol sampling, which suggests the two parameters
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
        # name the objective "branin" which labels the output user gets from the api after entering the two parameters
        objectives={"branin": ObjectiveProperties(minimize=True)}
    )
    
    return ax_client


def get_next_suggestion(ax_client: AxClient) -> Tuple[Dict, int]:
    """Get the next experiment suggestion from Ax using Service API"""
    return ax_client.get_next_trial()


def complete_current_iteration(ax_client: AxClient, trial_index: int, objective_value: float):
    """Complete the current iteration by sending the human-evaluated objective value to Ax"""
    ax_client.complete_trial(trial_index=trial_index, raw_data=objective_value)


def evaluate_branin(parameters: Dict) -> float:
    """Evaluate the Branin function for the given parameters (automated evaluation)"""
    return float(branin(x1=parameters["x1"], x2=parameters["x2"]))

def setup_slack_webhook(logger, block_name: str = "prefect-test") -> SlackWebhook:
    """
    Load or create the Slack webhook block
    
    Args:
        logger: Prefect logger instance
        block_name: Name of the Slack webhook block to load/create
        
    Returns:
        SlackWebhook block or None if configuration failed
    """
    try:
        # Try to load existing block
        slack_block = SlackWebhook.load(block_name)
        logger.info(f"Successfully loaded existing Slack webhook block '{block_name}'")
        return slack_block
        
    except ValueError:
        # Block doesn't exist, create it from Prefect variable
        logger.info(f"Slack webhook block '{block_name}' not found, creating it now...")
        
        from prefect.variables import Variable
        try:
            # Get webhook URL from Prefect Variable (created during deployment)
            webhook_url = Variable.get("slack-webhook-url")
            slack_block = SlackWebhook(url=webhook_url)
            slack_block.save(block_name)
            logger.info(f"Successfully created Slack webhook block '{block_name}'")
            return slack_block
            
        except ValueError as e:
            logger.error(f"slack-webhook-url variable not found. Please set it with: prefect variable set slack-webhook-url 'your-webhook-url'")
            logger.info("Skipping Slack notifications for this run.")
            return None


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


# ================================================================================
# EXPERIMENT DATA STORAGE FUNCTIONS WITH ERROR HANDLING
# ================================================================================

def generate_experiment_id() -> str:
    """Generate unique experiment ID with timestamp and validation"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        experiment_id = f"exp_{timestamp}_bo_branin"
        
        # Validate ID doesn't contain invalid characters for filesystem
        import re
        if not re.match(r'^[a-zA-Z0-9_\-]+$', experiment_id):
            raise ValueError(f"Generated experiment ID contains invalid characters: {experiment_id}")
            
        return experiment_id
    except Exception as e:
        # Fallback to basic timestamp if anything fails
        fallback_id = f"exp_{int(time.time())}_bo_branin"
        print(f"Warning: Failed to generate standard experiment ID ({e}), using fallback: {fallback_id}")
        return fallback_id


def setup_local_storage(experiment_id: str, max_retries: int = 3) -> Optional[Path]:
    """
    Create local storage directory with comprehensive error handling
    
    Args:
        experiment_id: Unique experiment identifier
        max_retries: Maximum attempts to create directory
        
    Returns:
        Path to storage directory or None if failed
    """
    for attempt in range(max_retries):
        try:
            # Validate experiment_id
            if not experiment_id or len(experiment_id.strip()) == 0:
                raise ValueError("Experiment ID cannot be empty")
                
            # Create base experiment_data directory
            base_dir = Path("experiment_data")
            
            # Check if we have write permissions for the current directory
            test_file = Path("test_write_permissions.tmp")
            try:
                test_file.touch()
                test_file.unlink()
            except PermissionError:
                raise PermissionError("No write permissions in current directory")
            
            base_dir.mkdir(exist_ok=True)
            
            # Create experiment-specific directory
            experiment_dir = base_dir / experiment_id
            experiment_dir.mkdir(exist_ok=True)
            
            # Test write access to the created directory
            test_file = experiment_dir / "test_write.tmp"
            test_file.write_text("test")
            test_file.unlink()
            
            return experiment_dir
            
        except PermissionError as e:
            print(f"Permission error creating storage directory (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print("ERROR: Cannot create storage directory due to permissions")
                return None
                
        except OSError as e:
            if "No space left on device" in str(e) or "disk full" in str(e).lower():
                print(f"ERROR: Disk full, cannot create storage directory: {e}")
                return None
            else:
                print(f"OS error creating storage directory (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt == max_retries - 1:
                    print("ERROR: Failed to create storage directory after maximum retries")
                    return None
                    
        except Exception as e:
            print(f"Unexpected error creating storage directory (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt == max_retries - 1:
                print("ERROR: Failed to create storage directory due to unexpected error")
                return None
                
        # Wait before retry
        if attempt < max_retries - 1:
            time.sleep(0.1 * (attempt + 1))  # Progressive backoff
    
    return None


def create_experiment_metadata(experiment_id: str, n_iterations: int, random_seed: int) -> Dict:
    """Create experiment metadata object"""
    from prefect.context import get_run_context
    
    # Get flow run context if available
    flow_run = get_run_context().flow_run if get_run_context() else None
    flow_run_id = flow_run.id if flow_run else "local-execution"
    
    return {
        "experiment": {
            "experiment_id": experiment_id,
            "name": "branin_bo_experiment",
            "description": "Human-in-the-loop BO campaign with Slack integration",
            "created_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,  # Will be set when experiment completes
            "status": "running",
            "metadata": {
                "random_seed": random_seed,
                "n_iterations": n_iterations,
                "objective": "branin",
                "minimize": True,
                "bounds": {
                    "x1": [-5.0, 10.0],
                    "x2": [0.0, 15.0]
                },
                "prefect_flow_run_id": str(flow_run_id),
                "user": os.getenv("USER", os.getenv("USERNAME", "unknown")),
                "environment": "local",
                "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
            }
        },
        "trials": [],
        "summary": {
            "total_trials": 0,
            "best_trial": None,
            "convergence": {},
            "timing": {
                "total_duration_seconds": None,
                "avg_evaluation_time_seconds": None
            }
        }
    }


def save_experiment_to_json(experiment_data: Dict, storage_path: Path) -> bool:
    """
    Save experiment metadata to local JSON file with comprehensive error handling
    
    Args:
        experiment_data: Experiment metadata dictionary
        storage_path: Directory path to save file
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not storage_path or not storage_path.exists():
        print(f"ERROR: Storage path does not exist: {storage_path}")
        return False
        
    try:
        # Validate experiment data
        if not experiment_data or not isinstance(experiment_data, dict):
            raise ValueError("Experiment data must be a non-empty dictionary")
            
        # Check required fields
        required_fields = ['experiment', 'trials', 'summary']
        for field in required_fields:
            if field not in experiment_data:
                raise ValueError(f"Missing required field: {field}")
        
        # Clean data for JSON serialization (handle NaN, infinity, etc.)
        cleaned_data = _clean_data_for_json(experiment_data)
        
        # Create temporary file for atomic write
        json_file = storage_path / "experiment.json"
        temp_file = storage_path / "experiment.json.tmp"
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            # Verify the file was written correctly by reading it back
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)  # This will raise exception if JSON is malformed
            
            # Atomic move (rename) to final location
            temp_file.replace(json_file)
            
            return True
            
        except Exception as e:
            # Clean up temporary file on failure
            if temp_file.exists():
                temp_file.unlink()
            raise e
            
    except PermissionError as e:
        print(f"Permission error saving experiment to JSON: {e}")
        return False
    except json.JSONEncodeError as e:
        print(f"JSON encoding error: {e}")
        return False
    except ValueError as e:
        print(f"Data validation error: {e}")
        return False
    except OSError as e:
        if "No space left on device" in str(e):
            print(f"Disk full error: {e}")
        else:
            print(f"File system error saving experiment: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error saving experiment to JSON: {e}")
        return False


def save_trial_to_json(trial_data: Dict, storage_path: Path, experiment_id: str = None) -> bool:
    """
    Save individual trial data to separate JSON file with error handling
    
    Args:
        trial_data: Trial data dictionary
        storage_path: Directory path to save file
        experiment_id: Optional experiment ID for filename
        
    Returns:
        bool: True if successful, False otherwise
    """
    if not storage_path or not storage_path.exists():
        print(f"ERROR: Storage path does not exist: {storage_path}")
        return False
        
    try:
        # Validate trial data
        if not trial_data or not isinstance(trial_data, dict):
            raise ValueError("Trial data must be a non-empty dictionary")
            
        # Check required fields
        required_fields = ['iteration', 'trial_index', 'parameters', 'objective_value']
        for field in required_fields:
            if field not in trial_data:
                raise ValueError(f"Missing required field in trial data: {field}")
        
        # Clean data for JSON serialization
        cleaned_data = _clean_data_for_json(trial_data)
        
        # Create filename with timestamp for individual trial
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        iteration = trial_data.get("iteration", "unknown")
        trial_filename = f"trial_{iteration}_{timestamp}.json"
        trial_file = storage_path / trial_filename
        temp_file = storage_path / f"{trial_filename}.tmp"
        
        try:
            # Write to temporary file first
            with open(temp_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, indent=2, ensure_ascii=False)
            
            # Verify the file was written correctly
            with open(temp_file, 'r', encoding='utf-8') as f:
                json.load(f)
            
            # Atomic move to final location
            temp_file.replace(trial_file)
            
            return True
            
        except Exception as e:
            # Clean up temporary file on failure
            if temp_file.exists():
                temp_file.unlink()
            raise e
            
    except PermissionError as e:
        print(f"Permission error saving trial to JSON: {e}")
        return False
    except json.JSONEncodeError as e:
        print(f"JSON encoding error for trial: {e}")
        return False
    except ValueError as e:
        print(f"Trial data validation error: {e}")
        return False
    except OSError as e:
        if "No space left on device" in str(e):
            print(f"Disk full error saving trial: {e}")
        else:
            print(f"File system error saving trial: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error saving trial to JSON: {e}")
        return False


def _clean_data_for_json(data):
    """
    Clean data for JSON serialization by handling NaN, infinity, and other problematic values
    
    Args:
        data: Data structure to clean
        
    Returns:
        Cleaned data structure safe for JSON serialization
    """
    import math
    
    if isinstance(data, dict):
        return {key: _clean_data_for_json(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [_clean_data_for_json(item) for item in data]
    elif isinstance(data, float):
        if math.isnan(data):
            return None  # or "NaN" if you prefer string representation
        elif math.isinf(data):
            return "Infinity" if data > 0 else "-Infinity"
        else:
            return data
    elif isinstance(data, (int, str, bool, type(None))):
        return data
    else:
        # Convert other types to string representation
        try:
            # Try to convert to basic type
            return str(data)
        except Exception:
            return None


# ================================================================================
# STORAGE MANAGEMENT FUNCTIONS
# ================================================================================

def initialize_experiment_storage(random_seed: int, n_iterations: int, logger=None) -> Tuple[Optional[str], Optional[Path], Optional[Dict]]:
    """
    Initialize complete storage system for a new experiment with error handling
    
    Returns:
        Tuple of (experiment_id, storage_path, experiment_data) or (None, None, None) on failure
    """
    try:
        # Generate unique experiment ID and setup storage
        experiment_id = generate_experiment_id()
        if logger:
            logger.info(f"Generated experiment ID: {experiment_id}")
        
        # Setup local storage directory
        storage_path = setup_local_storage(experiment_id)
        if storage_path is None:
            if logger:
                logger.error("Failed to create storage directory - experiment will run without local storage")
            return None, None, None
            
        if logger:
            logger.info(f"Created storage directory: {storage_path}")
        
        # Create experiment metadata
        experiment_data = create_experiment_metadata(experiment_id, random_seed, n_iterations)
        
        # Save initial experiment metadata
        if save_experiment_to_json(experiment_data, storage_path):
            if logger:
                logger.info(f"Saved initial experiment metadata to {storage_path}")
        else:
            if logger:
                logger.error("Failed to save initial experiment metadata - continuing without storage")
            return None, None, None
        
        return experiment_id, storage_path, experiment_data
        
    except Exception as e:
        if logger:
            logger.error(f"Critical error initializing storage system: {e}")
        print(f"ERROR: Storage initialization failed: {e}")
        return None, None, None


def save_trial_and_update_experiment(trial_result: Dict, experiment_data: Optional[Dict], 
                                   storage_path: Optional[Path], experiment_id: Optional[str], 
                                   iteration: int, logger=None) -> Optional[Dict]:
    """
    Save individual trial and update experiment metadata with error handling
    
    Args:
        trial_result: Trial data dictionary
        experiment_data: Current experiment metadata (can be None if storage failed)
        storage_path: Storage directory path (can be None if storage failed)
        experiment_id: Unique experiment identifier (can be None if storage failed)
        iteration: Current iteration number
        logger: Optional logger instance
        
    Returns:
        Updated experiment_data dictionary or None if storage unavailable
    """
    # If storage system is not available, just return None
    if storage_path is None or experiment_data is None:
        if logger:
            logger.warning(f"Storage system unavailable - skipping trial {iteration} storage")
        return None
    
    try:
        # Save individual trial to JSON
        if save_trial_to_json(trial_result, storage_path):
            if logger:
                logger.info(f"Saved trial {iteration} data to JSON")
        else:
            if logger:
                logger.warning(f"Failed to save trial {iteration} data to JSON")
        
        # Update experiment metadata with trial
        experiment_data["trials"].append(trial_result)
        experiment_data["summary"]["total_trials"] = len(experiment_data["trials"])
        
        # Update best trial if this is better (assuming minimization)
        try:
            objective_value = float(trial_result["objective_value"])
            current_best = experiment_data["summary"]["best_trial"]
            
            if (current_best is None or 
                objective_value < float(current_best["objective_value"])):
                experiment_data["summary"]["best_trial"] = trial_result.copy()
        except (ValueError, TypeError, KeyError) as e:
            if logger:
                logger.warning(f"Could not update best trial due to data issue: {e}")
        
        # Save updated experiment data
        if save_experiment_to_json(experiment_data, storage_path):
            if logger:
                logger.info(f"Updated experiment metadata after trial {iteration}")
        else:
            if logger:
                logger.warning(f"Failed to update experiment metadata after trial {iteration}")
        
        return experiment_data
        
    except Exception as e:
        if logger:
            logger.error(f"Error in trial storage for iteration {iteration}: {e}")
        print(f"ERROR: Trial storage failed: {e}")
        return experiment_data  # Return existing data even if update failed


def finalize_experiment_storage(experiment_data: Optional[Dict], storage_path: Optional[Path], 
                              n_iterations: int, experiment_id: Optional[str], logger=None) -> Optional[Dict]:
    """
    Finalize experiment storage with completion metadata and error handling
    
    Args:
        experiment_data: Current experiment metadata (can be None if storage failed)
        storage_path: Storage directory path (can be None if storage failed)
        n_iterations: Total number of iterations
        experiment_id: Unique experiment identifier (can be None if storage failed)
        logger: Optional logger instance
        
    Returns:
        Finalized experiment_data dictionary or None if storage unavailable
    """
    # If storage system is not available, just return None
    if storage_path is None or experiment_data is None:
        if logger:
            logger.warning("Storage system unavailable - skipping experiment finalization")
        return None
    
    try:
        # Mark experiment as completed
        experiment_data["experiment"]["completed_at"] = datetime.utcnow().isoformat() + "Z"
        experiment_data["experiment"]["status"] = "completed"
        
        # Calculate final timing
        try:
            start_time = datetime.fromisoformat(experiment_data["experiment"]["created_at"].replace("Z", ""))
            end_time = datetime.fromisoformat(experiment_data["experiment"]["completed_at"].replace("Z", ""))
            total_duration = (end_time - start_time).total_seconds()
            experiment_data["summary"]["timing"]["total_duration_seconds"] = total_duration
            experiment_data["summary"]["timing"]["avg_evaluation_time_seconds"] = total_duration / max(n_iterations, 1)
        except Exception as e:
            if logger:
                logger.warning(f"Could not calculate timing metrics: {e}")
        
        # Save final experiment data
        if save_experiment_to_json(experiment_data, storage_path):
            if logger:
                logger.info(f"Saved final experiment results to {storage_path}")
                logger.info(f"Complete results stored in: {storage_path / 'experiment.json'}")
                logger.info(f"Experiment ID: {experiment_id}")
                logger.info(f"Storage Location: {storage_path}")
        else:
            if logger:
                logger.error("Failed to save final experiment results")
        
        return experiment_data
        
    except Exception as e:
        if logger:
            logger.error(f"Error finalizing experiment storage: {e}")
        print(f"ERROR: Experiment finalization failed: {e}")
        return experiment_data  # Return existing data even if finalization failed


# ================================================================================

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
    
    # === INITIALIZE STORAGE SYSTEM ===
    experiment_id, storage_path, experiment_data = initialize_experiment_storage(
        random_seed, n_iterations, logger
    )
    
    # Setup Slack webhook
    slack_block = setup_slack_webhook(logger)
    
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
        if flow_run:
            # Get base URL from environment variable or fallback to localhost for development
            base_url = os.getenv("PREFECT_UI_URL", "http://127.0.0.1:4200")
            flow_run_url = f"{base_url}/flow-runs/flow-run/{flow_run.id}"
            
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
        
        # Complete the current iteration by sending objective value to Ax
        complete_current_iteration(ax_client, trial_index, objective_value)
        
        # Store results
        trial_result = {
            "iteration": iteration + 1,
            "trial_index": trial_index,
            "parameters": parameters,
            "objective_value": objective_value,
            "notes": user_input.notes
        }
        results.append(trial_result)
        
        # === SAVE TRIAL DATA ===
        experiment_data = save_trial_and_update_experiment(
            trial_result, experiment_data, storage_path, 
            experiment_id, iteration + 1, logger
        )
        
        logger.info(f"Completed iteration {iteration + 1} with value {objective_value}")
    
    # Get best parameters found
    best_parameters, best_values = ax_client.get_best_parameters()
    
    # === FINALIZE EXPERIMENT ===
    experiment_data = finalize_experiment_storage(
        experiment_data, storage_path, n_iterations, experiment_id, logger
    )
    
    logger.info("\nBO Campaign Completed!")
    logger.info(f"Best parameters found: {best_parameters}")
    logger.info(f"Best objective value: {best_values}")
    
    # Send final results to Slack
    # Build experiment details section (handle cases where storage failed)
    experiment_details = f"• Total trials: {n_iterations}"
    
    if experiment_id:
        experiment_details += f"\n    • Experiment ID: {experiment_id}"
    
    if experiment_data and "summary" in experiment_data and "timing" in experiment_data["summary"]:
        duration = experiment_data["summary"]["timing"].get("total_duration_seconds")
        if duration:
            experiment_details += f"\n    • Duration: {duration:.1f} seconds"
    
    if storage_path:
        experiment_details += f"\n    • Results saved to: `{storage_path.name}/`"
    else:
        experiment_details += f"\n    • Storage: Not available (experiment ran without local storage)"
    
    final_message = f"""
    *Bayesian Optimization Campaign Completed!*

    *Best parameters found:*
    • x1 = {best_parameters['x1']}
    • x2 = {best_parameters['x2']}

    *Best objective value:* {best_values[0]['branin']}
    
    *Experiment Details:*
    {experiment_details}

    Thank you for participating in this human-in-the-loop optimization!
    """
    # Send final notification to Slack (if configured)
    if slack_block:
        slack_block.notify(final_message)
    else:
        logger.info("Slack webhook not configured, skipping final notification")
    
    return ax_client, results, experiment_id, storage_path
if __name__ == "__main__":
    # Run the Prefect flow
    print("Starting Bayesian Optimization HITL campaign with Slack integration")
    print("Make sure you have set up your Slack webhook block named 'prefect-test'")
    print("You will receive Slack notifications for each iteration")
    
    # Run the flow
    ax_client, results, experiment_id, storage_path = run_bo_campaign()