"""
Prefect flows for Zaber linear rail control.

Provides workflow orchestration using Prefect for remote rail control.
"""

from prefect import flow, task
from prefect.logging import get_run_logger

from ac_training_lab.zaber_linear_rail.rail_controller import (
    connect,
    disconnect,
    get_device_info,
    get_position,
    home_axis,
    move_relative,
    move_to_position,
    stop_movement,
)

# Wrap core functions as tasks
connect_task = task(connect)
disconnect_task = task(disconnect)
home_axis_task = task(home_axis)
move_to_position_task = task(move_to_position)
move_relative_task = task(move_relative)
get_position_task = task(get_position)
stop_movement_task = task(stop_movement)
get_device_info_task = task(get_device_info)


@flow
def move_to_position_flow(
    target_position: float,
    serial_port: str = None,
    velocity: float = None,
    home_first: bool = False,
) -> dict:
    """
    Prefect flow for moving rail to a specific position.

    Args:
        target_position: Target position in mm
        serial_port: Optional serial port override
        velocity: Optional velocity in mm/s
        home_first: Whether to home before moving

    Returns:
        dict with movement results
    """
    logger = get_run_logger()
    logger.info("=== MOVE TO POSITION FLOW ===")
    logger.info(f"Target: {target_position} mm")

    # Connect to device
    connection_info = connect_task(serial_port=serial_port)
    logger.info(f"Connected to: {connection_info['device_name']}")

    try:
        # Home if requested
        if home_first:
            logger.info("Homing axis first...")
            home_result = home_axis_task()
            logger.info(f"Homed. Current position: {home_result['position']:.2f} mm")

        # Get initial position
        initial = get_position_task()
        logger.info(f"Initial position: {initial['position']:.2f} mm")

        # Execute movement
        result = move_to_position_task(target_position, velocity=velocity)

        start = result["start_position"]
        final = result["final_position"]
        logger.info(f"Movement complete: {start:.2f} -> {final:.2f} mm")
        logger.info(f"Distance moved: {result['distance']:.2f} mm")

        return {
            "success": True,
            "movement": result,
            "connection": connection_info,
        }

    finally:
        # Always disconnect
        disconnect_task()
        logger.info("Disconnected")


@flow
def move_relative_flow(
    distance: float,
    serial_port: str = None,
    velocity: float = None,
) -> dict:
    """
    Prefect flow for moving rail by a relative distance.

    Args:
        distance: Distance to move in mm (positive or negative)
        serial_port: Optional serial port override
        velocity: Optional velocity in mm/s

    Returns:
        dict with movement results
    """
    logger = get_run_logger()
    logger.info("=== MOVE RELATIVE FLOW ===")
    logger.info(f"Distance: {distance:+.2f} mm")

    # Connect to device
    connection_info = connect_task(serial_port=serial_port)
    logger.info(f"Connected to: {connection_info['device_name']}")

    try:
        # Get initial position
        initial = get_position_task()
        logger.info(f"Initial position: {initial['position']:.2f} mm")

        # Execute movement
        result = move_relative_task(distance, velocity=velocity)

        start = result["start_position"]
        final = result["final_position"]
        logger.info(f"Movement complete: {start:.2f} -> {final:.2f} mm")
        logger.info(f"Actual distance: {result['actual_distance']:.2f} mm")

        return {
            "success": True,
            "movement": result,
            "connection": connection_info,
        }

    finally:
        disconnect_task()
        logger.info("Disconnected")


@flow
def home_flow(serial_port: str = None) -> dict:
    """
    Prefect flow for homing the rail.

    Args:
        serial_port: Optional serial port override

    Returns:
        dict with homing results
    """
    logger = get_run_logger()
    logger.info("=== HOME FLOW ===")

    # Connect to device
    connection_info = connect_task(serial_port=serial_port)
    logger.info(f"Connected to: {connection_info['device_name']}")

    try:
        # Home the axis
        result = home_axis_task()
        logger.info(f"Homing complete. Position: {result['position']:.2f} mm")

        return {
            "success": True,
            "homing": result,
            "connection": connection_info,
        }

    finally:
        disconnect_task()
        logger.info("Disconnected")


@flow
def get_status_flow(serial_port: str = None) -> dict:
    """
    Prefect flow for getting rail status.

    Args:
        serial_port: Optional serial port override

    Returns:
        dict with status info
    """
    logger = get_run_logger()
    logger.info("=== STATUS FLOW ===")

    # Connect to device
    connection_info = connect_task(serial_port=serial_port)
    logger.info(f"Connected to: {connection_info['device_name']}")

    try:
        # Get device info
        device_info = get_device_info_task()

        logger.info(f"Device: {device_info['device_name']}")
        logger.info(f"Position: {device_info['current_position']:.2f} mm")
        logger.info(f"Max speed: {device_info['max_speed']:.2f} mm/s")
        logger.info(f"Acceleration: {device_info['acceleration']:.2f} mm/s²")

        return {
            "success": True,
            "device_info": device_info,
            "connection": connection_info,
        }

    finally:
        disconnect_task()
        logger.info("Disconnected")


@flow
def sequence_flow(
    positions: list[float],
    serial_port: str = None,
    velocity: float = None,
    home_first: bool = True,
) -> dict:
    """
    Prefect flow for moving through a sequence of positions.

    Args:
        positions: List of positions to visit in mm
        serial_port: Optional serial port override
        velocity: Optional velocity in mm/s
        home_first: Whether to home before starting sequence

    Returns:
        dict with sequence results
    """
    logger = get_run_logger()
    logger.info("=== SEQUENCE FLOW ===")
    logger.info(f"Positions: {positions}")

    # Connect to device
    connection_info = connect_task(serial_port=serial_port)
    logger.info(f"Connected to: {connection_info['device_name']}")

    results = []

    try:
        # Home if requested
        if home_first:
            logger.info("Homing axis first...")
            home_result = home_axis_task()
            logger.info(f"Homed. Position: {home_result['position']:.2f} mm")

        # Execute sequence
        for i, position in enumerate(positions):
            logger.info(f"Step {i+1}/{len(positions)}: Moving to {position} mm")
            result = move_to_position_task(position, velocity=velocity)
            results.append(result)
            logger.info(f"  Reached: {result['final_position']:.2f} mm")

        logger.info(f"Sequence complete. Visited {len(results)} positions.")

        return {
            "success": True,
            "steps_completed": len(results),
            "results": results,
            "connection": connection_info,
        }

    finally:
        disconnect_task()
        logger.info("Disconnected")


# =============================================================================
# DEPLOYMENT FUNCTIONS
# =============================================================================


def deploy_move_to_position(
    work_pool_name: str = "zaber-linear-rail-pool",
    deployment_name: str = "move-to-position",
) -> str:
    """Deploy the move-to-position flow."""
    from pathlib import Path

    source_dir = Path(__file__).parent.parent.parent

    entrypoint = (
        "ac_training_lab/zaber_linear_rail/prefect_flows.py:move_to_position_flow"
    )
    move_to_position_flow.from_source(
        source=str(source_dir),
        entrypoint=entrypoint,
    ).deploy(
        name=deployment_name,
        work_pool_name=work_pool_name,
        description="Move Zaber linear rail to an absolute position",
    )

    print(f"✅ Deployed '{deployment_name}'")
    run_cmd = f"prefect deployment run 'move-to-position-flow/{deployment_name}'"
    print(f"Run: {run_cmd} --param target_position=100.0")
    return deployment_name


def deploy_home(
    work_pool_name: str = "zaber-linear-rail-pool",
    deployment_name: str = "home",
) -> str:
    """Deploy the home flow."""
    from pathlib import Path

    source_dir = Path(__file__).parent.parent.parent

    home_flow.from_source(
        source=str(source_dir),
        entrypoint="ac_training_lab/zaber_linear_rail/prefect_flows.py:home_flow",
    ).deploy(
        name=deployment_name,
        work_pool_name=work_pool_name,
        description="Home Zaber linear rail axis",
    )

    print(f"✅ Deployed '{deployment_name}'")
    print(f"Run: prefect deployment run 'home-flow/{deployment_name}'")
    return deployment_name


def deploy_sequence(
    work_pool_name: str = "zaber-linear-rail-pool",
    deployment_name: str = "sequence",
) -> str:
    """Deploy the sequence flow."""
    from pathlib import Path

    source_dir = Path(__file__).parent.parent.parent

    sequence_flow.from_source(
        source=str(source_dir),
        entrypoint="ac_training_lab/zaber_linear_rail/prefect_flows.py:sequence_flow",
    ).deploy(
        name=deployment_name,
        work_pool_name=work_pool_name,
        description="Execute a sequence of positions on Zaber linear rail",
    )

    print(f"✅ Deployed '{deployment_name}'")
    run_cmd = f"prefect deployment run 'sequence-flow/{deployment_name}'"
    print(f"Run: {run_cmd} --param positions='[0, 100, 200, 100, 0]'")
    return deployment_name


def deploy_all_flows(work_pool_name: str = "zaber-linear-rail-pool") -> bool:
    """Deploy all Zaber linear rail flows."""
    print("=== DEPLOYING ZABER LINEAR RAIL FLOWS ===")
    print(f"Work pool: {work_pool_name}")

    deploy_move_to_position(work_pool_name)
    deploy_home(work_pool_name)
    deploy_sequence(work_pool_name)

    print("\n🎉 All deployments created!")
    print("\nAvailable flows:")
    print("  1. move-to-position - Move to absolute position")
    print("  2. home - Home the axis")
    print("  3. sequence - Execute position sequence")
    print(f"\nStart worker: prefect worker start --pool {work_pool_name}")

    return True


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]
        if cmd == "deploy":
            pool = sys.argv[2] if len(sys.argv) > 2 else "zaber-linear-rail-pool"
            deploy_all_flows(pool)
        elif cmd == "status":
            get_status_flow()
        elif cmd == "home":
            home_flow()
        elif cmd == "move":
            if len(sys.argv) < 3:
                print("Usage: python prefect_flows.py move <position_mm>")
                sys.exit(1)
            position = float(sys.argv[2])
            move_to_position_flow(position)
        else:
            print("Usage: python prefect_flows.py [deploy|status|home|move <position>]")
    else:
        print("Usage: python prefect_flows.py [deploy|status|home|move <position>]")
        print("\nExamples:")
        print("  python prefect_flows.py deploy              # Deploy all flows")
        print("  python prefect_flows.py deploy my-pool      # Deploy with custom pool")
        print("  python prefect_flows.py status              # Get device status")
        print("  python prefect_flows.py home                # Home the axis")
        print("  python prefect_flows.py move 100            # Move to 100mm")
