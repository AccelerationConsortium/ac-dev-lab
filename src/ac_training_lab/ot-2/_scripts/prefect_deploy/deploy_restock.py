"""
deploy_restock.py - Deploy restock maintenance flows

This script deploys the restock maintenance flows to Prefect work pools.
Run this when setting up deployments or when flow schemas change.
"""

import sys
from pathlib import Path

from prefect.runner.storage import GitRepository

# Add the scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent  # Go up to _scripts directory
sys.path.insert(0, str(scripts_dir))

from restock_flow import (
    check_inventory_status_flow,
    initialize_inventory_flow,
    restock_maintenance_flow,
)

if __name__ == "__main__":
    print("Deploying restock maintenance flows...")
    
    # Deploy restock_maintenance_flow to maintenance queue
    print("\n1. Deploying restock-maintenance flow...")
    restock_maintenance_flow.from_source(
        source=GitRepository(
            "https://github.com/AccelerationConsortium/ac-training-lab.git"
        ),
        entrypoint="src/ac_training_lab/ot-2/_scripts/restock_flow.py:restock_maintenance_flow",
    ).deploy(
        name="restock-maintenance",
        work_pool_name="ot2-device-pool",
        work_queue_name="maintenance",
        description="Manual restock operation for OT-2 paint inventory",
        tags=["ot2", "maintenance", "restock", "inventory"],
    )
    
    # Deploy initialize_inventory_flow to maintenance queue
    print("\n2. Deploying initialize-inventory flow...")
    initialize_inventory_flow.from_source(
        source=GitRepository(
            "https://github.com/AccelerationConsortium/ac-training-lab.git"
        ),
        entrypoint="src/ac_training_lab/ot-2/_scripts/restock_flow.py:initialize_inventory_flow",
    ).deploy(
        name="initialize-inventory",
        work_pool_name="ot2-device-pool",
        work_queue_name="maintenance",
        description="Initialize or reset OT-2 paint inventory system",
        tags=["ot2", "maintenance", "inventory", "setup"],
    )
    
    # Deploy check_inventory_status_flow to monitoring queue
    print("\n3. Deploying check-inventory-status flow...")
    check_inventory_status_flow.from_source(
        source=GitRepository(
            "https://github.com/AccelerationConsortium/ac-training-lab.git"
        ),
        entrypoint="src/ac_training_lab/ot-2/_scripts/restock_flow.py:check_inventory_status_flow",
    ).deploy(
        name="check-inventory-status",
        work_pool_name="ot2-device-pool",
        work_queue_name="monitoring",
        description="Check current inventory status and identify colors needing restock",
        tags=["ot2", "monitoring", "inventory", "status"],
    )
    
    print("\n✓ All restock maintenance flows deployed successfully!")
    print("\nAvailable deployments:")
    print("  1. restock-maintenance/restock-maintenance")
    print("  2. initialize-inventory/initialize-inventory")
    print("  3. check-inventory-status/check-inventory-status")
    print("\nWork queues:")
    print("  - maintenance: For restock and initialization operations")
    print("  - monitoring: For inventory status checks")
