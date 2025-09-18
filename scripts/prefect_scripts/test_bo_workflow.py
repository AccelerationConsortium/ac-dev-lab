#!/usr/bin/env python3
"""
Simple test of the BO HiTL tutorial core functionality
This demonstrates the Ax Service API integration and Branin function evaluation
without requiring Prefect to be installed.
"""

import math
from typing import Dict, List, Tuple

# Mock Ax Service API implementation
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
        print(f"✓ Created experiment: {name}")
        print(f"  Parameters: {[p['name'] for p in parameters]}")
        print(f"  Objectives: {list(objectives.keys())}")
        
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
        print(f"✓ Completed trial {trial_index} with value {raw_data:.4f}")
        
    def get_best_parameters(self):
        """Get best parameters so far"""
        if not self.completed_trials:
            return None
        best_trial = min(self.completed_trials, key=lambda x: x[1])
        return {"trial_index": best_trial[0], "value": best_trial[1]}


def mock_branin(x1: float, x2: float) -> float:
    """
    Branin function implementation
    Global minimum at (π, 2.275) and (-π, 12.275) and (9.42478, 2.475) with value 0.397887
    """
    a = 1
    b = 5.1 / (4 * math.pi**2)
    c = 5 / math.pi
    r = 6
    s = 10
    t = 1 / (8 * math.pi)
    
    return a * (x2 - b * x1**2 + c * x1 - r)**2 + s * (1 - t) * math.cos(x1) + s


def demonstrate_bo_workflow():
    """Demonstrate the core BO workflow"""
    print("🚀 Demonstrating BO Human-in-the-Loop Workflow")
    print("=" * 50)
    
    # Step 1: Initialize Ax client (Service API pattern)
    print("1. Initializing Ax Service API client...")
    ax_client = MockAxClient()
    
    # Step 2: Create experiment
    print("\n2. Creating Branin optimization experiment...")
    ax_client.create_experiment(
        name="branin_bo_hitl_demonstration",
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
        objectives={"branin": "minimize"}
    )
    
    # Step 3: Run BO iterations
    print("\n3. Running BO iterations (simulating HiTL workflow)...")
    
    for iteration in range(5):
        print(f"\n--- Iteration {iteration + 1}/5 ---")
        
        # Get suggestion from Ax
        parameters, trial_index = ax_client.get_next_trial()
        print(f"Ax suggests: x1={parameters['x1']:.4f}, x2={parameters['x2']:.4f}")
        
        # Simulate human evaluation using HuggingFace Branin space
        objective_value = mock_branin(parameters['x1'], parameters['x2'])
        print(f"Human evaluates via HuggingFace: branin({parameters['x1']:.4f}, {parameters['x2']:.4f}) = {objective_value:.4f}")
        
        # Complete trial in Ax
        ax_client.complete_trial(trial_index, objective_value)
        
        # In real workflow, this would involve:
        # - Slack notification with parameters
        # - User goes to https://huggingface.co/spaces/AccelerationConsortium/branin  
        # - User enters x1, x2 values
        # - User clicks Slack link to resume Prefect flow
        # - User enters objective value in Prefect UI
    
    # Step 4: Show results
    print("\n4. Final Results:")
    best = ax_client.get_best_parameters()
    if best:
        print(f"🏆 Best result: trial {best['trial_index']} with value {best['value']:.4f}")
    
    print(f"📊 All trials: {ax_client.completed_trials}")
    
    # Show Branin global minimum for reference
    global_min_x1, global_min_x2 = math.pi, 2.275
    global_min_value = mock_branin(global_min_x1, global_min_x2)
    print(f"🎯 Branin global minimum: f({global_min_x1:.4f}, {global_min_x2:.4f}) = {global_min_value:.4f}")
    
    print("\n✅ Demonstration complete!")
    print("\nIn the full tutorial:")
    print("- Each iteration triggers Slack notification")
    print("- User evaluates via https://huggingface.co/spaces/AccelerationConsortium/branin")
    print("- User resumes Prefect flow via UI")
    print("- Real Ax Service API provides intelligent suggestions")


if __name__ == "__main__":
    demonstrate_bo_workflow()