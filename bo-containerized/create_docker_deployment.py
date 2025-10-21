#!/usr/bin/env python3
"""
Docker Deployment Script for BO HITL Workflow

This creates a deployment that uses Docker workers instead of local process workers.
"""

from prefect import flow
from prefect.runner.storage import GitRepository

if __name__ == "__main__":
    # Create deployment for Docker workers
    flow.from_source(
        source=GitRepository(
            url="https://github.com/AccelerationConsortium/ac-dev-lab.git",
            branch="copilot/fix-382"
        ),
        entrypoint="bo-containerized/complete_workflow/bo_hitl_slack_tutorial.py:run_bo_campaign",
    ).deploy(
        name="bo-hitl-slack-docker-deployment",
        description="Bayesian Optimization HITL workflow with Slack integration (Docker)",
        tags=["bayesian-optimization", "hitl", "slack", "docker"],
        work_pool_name="docker-pool",
        parameters={
            "n_iterations": 5,
            "random_seed": 42
        },
    )