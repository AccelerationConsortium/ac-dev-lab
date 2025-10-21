#!/usr/bin/env python3
"""
Deployment Script for Bayesian Optimization HITL Workflow

This script creates a Prefect deployment for the bo_hitl_slack_tutorial.py flow 
using the modern flow.from_source() approach.

Requirements:
- Same dependencies as bo_hitl_slack_tutorial.py
- A configured Prefect server and work pool

Usage:
    python create_bo_hitl_deployment.py

Benefits of using flow.from_source() over local execution:
1. Git Integration: Automatically pulls code from your repository
2. Infrastructure: Runs code in specified work pools (local, k8s, docker)
3. Scheduling: Run flows on schedules (cron, intervals)
4. Remote execution: Run flows on remote workers/agents
5. UI monitoring: Track flow runs, logs, and results via UI
6. Parameterization: Pass different parameters to each run
7. Notifications: Configure notifications for flow status
8. Human-in-the-Loop: Better UI experience for HITL workflows
9. Versioning: Keep track of deployment versions
10. Team collaboration: Share flows with team members
"""

from prefect import flow
from prefect.runner.storage import GitRepository

if __name__ == "__main__":
    # Create and deploy the flow using GitRepository with branch specification
    flow.from_source(
        source=GitRepository(
            url="https://github.com/AccelerationConsortium/ac-dev-lab.git",
            branch="copilot/fix-382"  # Specify your branch explicitly
        ),
        entrypoint="scripts/prefect_scripts/bo_hitl_slack_tutorial.py:run_bo_campaign",
    ).deploy(
        name="bo-hitl-slack-deployment",
        description="Bayesian Optimization HITL workflow with Slack integration",
        tags=["bayesian-optimization", "hitl", "slack"],
        work_pool_name="my-managed-pool",  
        # Uncomment to schedule the flow (e.g., once a day at 9am)
        # cron="0 9 * * *",
        parameters={
            "n_iterations": 5,  # Default number of BO iterations
            "random_seed": 42   # Default random seed for reproducibility
        },
    )
    
    print("Deployment 'bo-hitl-slack-deployment' created successfully!")
    print("You can now start the flow from the Prefect UI or using the CLI:")
    print("prefect deployment run 'bo-hitl-slack-campaign/bo-hitl-slack-deployment'")
    
    # Note: You can customize the work_pool_name based on your Prefect setup
    # Common work pools include:
    # - "process" for local process execution
    # - "kubernetes" for k8s clusters
    # - "docker" for container-based execution
    # Run 'prefect work-pool ls' to see available work pools