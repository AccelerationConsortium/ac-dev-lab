"""
Prefect flows for Zaber linear rail control.

Simple wrappers around Zaber API calls with Prefect task/flow decorators.
"""

from typing import Optional

from prefect import flow, task

from ac_training_lab.zaber_linear_rail.rail_controller import (
    connect,
    disconnect,
    get_position,
    home,
    move_absolute,
    move_relative,
    stop,
)

# Wrap functions as tasks
connect_task = task(connect)
disconnect_task = task(disconnect)
home_task = task(home)
move_absolute_task = task(move_absolute)
move_relative_task = task(move_relative)
get_position_task = task(get_position)
stop_task = task(stop)


@flow
def home_flow(serial_port: Optional[str] = None) -> float:
    """Home the axis. Returns position in mm."""
    connect_task(serial_port=serial_port)
    try:
        return home_task()
    finally:
        disconnect_task()


@flow
def move_absolute_flow(
    position: float, unit: str = "mm", serial_port: Optional[str] = None
) -> float:
    """Move to absolute position. Returns final position."""
    connect_task(serial_port=serial_port)
    try:
        return move_absolute_task(position, unit)
    finally:
        disconnect_task()


@flow
def move_relative_flow(
    distance: float, unit: str = "mm", serial_port: Optional[str] = None
) -> float:
    """Move by relative distance. Returns final position."""
    connect_task(serial_port=serial_port)
    try:
        return move_relative_task(distance, unit)
    finally:
        disconnect_task()


@flow
def get_position_flow(unit: str = "mm", serial_port: Optional[str] = None) -> float:
    """Get current position."""
    connect_task(serial_port=serial_port)
    try:
        return get_position_task(unit)
    finally:
        disconnect_task()


@flow
def sequence_flow(
    positions: list[float],
    unit: str = "mm",
    serial_port: Optional[str] = None,
    home_first: bool = True,
) -> list[float]:
    """Move through sequence of positions. Returns list of final positions."""
    connect_task(serial_port=serial_port)
    try:
        if home_first:
            home_task()
        results = []
        for pos in positions:
            results.append(move_absolute_task(pos, unit))
        return results
    finally:
        disconnect_task()


# Deployment functions
def deploy_all_flows(work_pool_name: str = "zaber-linear-rail-pool") -> None:
    """Deploy all flows to Prefect."""
    from pathlib import Path

    source_dir = Path(__file__).parent.parent.parent
    base = "ac_training_lab/zaber_linear_rail/prefect_flows.py"

    home_flow.from_source(
        source=str(source_dir), entrypoint=f"{base}:home_flow"
    ).deploy(name="home", work_pool_name=work_pool_name)

    move_absolute_flow.from_source(
        source=str(source_dir), entrypoint=f"{base}:move_absolute_flow"
    ).deploy(name="move-absolute", work_pool_name=work_pool_name)

    move_relative_flow.from_source(
        source=str(source_dir), entrypoint=f"{base}:move_relative_flow"
    ).deploy(name="move-relative", work_pool_name=work_pool_name)

    get_position_flow.from_source(
        source=str(source_dir), entrypoint=f"{base}:get_position_flow"
    ).deploy(name="get-position", work_pool_name=work_pool_name)

    sequence_flow.from_source(
        source=str(source_dir), entrypoint=f"{base}:sequence_flow"
    ).deploy(name="sequence", work_pool_name=work_pool_name)

    print(f"Deployed all flows to work pool: {work_pool_name}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "deploy":
        pool = sys.argv[2] if len(sys.argv) > 2 else "zaber-linear-rail-pool"
        deploy_all_flows(pool)
