# setup_work_pool.py - Script to create work pool and queues
"""
This script sets up the work pool and work queues for OT-2 device operations.
Run this once to initialize the infrastructure.
"""

from prefect import flow
from prefect.client import get_client


async def setup_work_pool():
    """
    Create work pool and work queues for OT-2 devices.
    This should be run with appropriate permissions (e.g., admin or deployment creator).
    """
    client = get_client()

    # Create work pool for OT-2 devices (process type for local execution)
    work_pool_name = "ot2-device-pool"
    try:
        await client.read_work_pool(work_pool_name)
        print(f"Work pool '{work_pool_name}' already exists")
    except Exception:
        await client.create_work_pool(
            name=work_pool_name,
            type="process",  # Use 'process' for local subprocess execution
            description="Work pool for OT-2 laboratory devices",
        )
        print(f"Created work pool '{work_pool_name}'")

    # Create work queues with different priorities for different device types
    queues = [
        {
            "name": "high-priority",
            "priority": 1,
            "description": "High priority queue for urgent measurements",
        },
        {
            "name": "standard",
            "priority": 2,
            "description": "Standard queue for regular operations",
        },
        {
            "name": "low-priority",
            "priority": 3,
            "description": "Low priority queue for background tasks",
        },
    ]

    for queue_config in queues:
        try:
            await client.read_work_queue(work_pool_name, queue_config["name"])
            print(f"Work queue '{queue_config['name']}' already exists")
        except Exception:
            await client.create_work_queue(
                work_pool_name=work_pool_name,
                name=queue_config["name"],
                priority=queue_config["priority"],
                description=queue_config["description"],
            )
            print(
                f"Created work queue '{queue_config['name']}' with priority {queue_config['priority']}"
            )


if __name__ == "__main__":
    import asyncio

    asyncio.run(setup_work_pool())
