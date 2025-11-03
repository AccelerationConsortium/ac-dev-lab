"""
device_with_inventory.py - OT-2 Device Operations with Inventory Tracking

This file defines Prefect flows for OT-2 device operations with integrated
inventory management. It tracks paint stock levels, checks availability before
mixing, and subtracts used volumes after each operation.

NOTE: This file uses a mock implementation for demonstration/testing purposes.
For production use on a real OT-2, replace MockProtocol with opentrons.execute API.
"""

import os
import sys
import time
from pathlib import Path

from prefect import flow, task
from prefect.runner.storage import GitRepository

# Add the scripts directory to path for imports
scripts_dir = Path(__file__).parent.parent  # Go up to _scripts directory
sys.path.insert(0, str(scripts_dir))

from inventory_utils import (
    check_stock_availability,
    get_current_inventory,
    subtract_stock,
)

# ------------------- OT-2 Setup -------------------
# Determine if we're running on a real OT-2 or in simulation mode
USE_REAL_OPENTRONS = os.getenv("USE_REAL_OPENTRONS", "false").lower() == "true"

if USE_REAL_OPENTRONS:
    try:
        import opentrons.execute
        protocol = opentrons.execute.get_protocol_api("2.16")
        protocol.home()
        print("Using real Opentrons API")
    except ImportError:
        print("Warning: opentrons module not available, falling back to mock")
        USE_REAL_OPENTRONS = False


# Mock implementation for testing/demonstration
class MockProtocol:
    """Mock OT-2 protocol for testing when opentrons library is not available."""
    def home(self):
        print("Homing OT-2 robot")

    def load_labware(self, definition, location):
        print(f"Loading labware at location {location}")
        return MockLabware()

    def load_instrument(self, name, mount, tip_racks):
        print(f"Loading instrument {name} on {mount}")
        return MockInstrument()


class MockLabware:
    def __getitem__(self, well):
        return MockWell(well)


class MockWell:
    def __init__(self, well_id):
        self.well_id = well_id

    def top(self, z=0):
        return f"Position {self.well_id} top z={z}"


class MockInstrument:
    def pick_up_tip(self, tip_rack_well):
        print(f"Picking up tip from {tip_rack_well.well_id}")

    def aspirate(self, volume, source):
        print(f"Aspirating {volume}ul from {source}")

    def dispense(self, volume, destination):
        print(f"Dispensing {volume}ul to {destination}")

    def blow_out(self, location):
        print(f"Blowing out to {location}")

    def drop_tip(self, tip_rack_well):
        print(f"Dropping tip to {tip_rack_well.well_id}")

    def move_to(self, position):
        print(f"Moving to {position}")


# Initialize protocol based on environment
if not USE_REAL_OPENTRONS:
    print("Using mock Opentrons implementation for testing")
    protocol = MockProtocol()
    protocol.home()
    
    # Load mock labware
    tiprack_2 = protocol.load_labware("mock_definition", 10)
    reservoir = protocol.load_labware("mock_definition", 3)
    plate = protocol.load_labware("mock_definition", 1)
    tiprack_1 = protocol.load_labware("mock_definition", 9)
    
    p300 = protocol.load_instrument("p300_single_gen2", "right", [tiprack_1])
else:
    # For real OT-2, load actual labware definitions
    # This would need to be adapted based on your actual setup
    # See OT2mqtt.py for reference
    import json
    
    with open("/var/lib/jupyter/notebooks/ac_color_sensor_charging_port.json") as labware_file1:
        labware_def1 = json.load(labware_file1)
        tiprack_2 = protocol.load_labware_from_definition(labware_def1, 10)
    
    with open("/var/lib/jupyter/notebooks/ac_6_tuberack_15000ul.json") as labware_file2:
        labware_def2 = json.load(labware_file2)
        reservoir = protocol.load_labware_from_definition(labware_def2, 3)
    
    plate = protocol.load_labware(load_name="corning_96_wellplate_360ul_flat", location=1)
    tiprack_1 = protocol.load_labware(load_name="opentrons_96_tiprack_300ul", location=9)
    
    p300 = protocol.load_instrument(
        instrument_name="p300_single_gen2", mount="right", tip_racks=[tiprack_1]
    )
    p300.well_bottom_clearance.dispense = 8


@flow(name="mix-color-with-inventory")
def mix_color_with_inventory(R: int, Y: int, B: int, G: int, mix_well: str):
    """
    Mix colors with specified RGB values into a well, with inventory tracking.

    This flow checks stock availability before mixing, performs the mixing
    operation, and updates the inventory to reflect used volumes.

    Parameters:
    - R, Y, B, G: Volumes of Red, Yellow, Blue, Green colors (0-300 ul total)
    - mix_well: Well identifier (e.g., "B2")
    
    Returns:
    - Dictionary with mixing results and updated inventory
    
    Raises:
    - ValueError if total volume exceeds 300 ul
    - ValueError if insufficient stock for any color
    """
    total = R + Y + B + G
    if total > 300:
        raise ValueError("The sum of the proportions must be <= 300")

    # Check stock availability before proceeding
    print("Checking stock availability...")
    try:
        availability = check_stock_availability(
            red_volume=R,
            yellow_volume=Y,
            blue_volume=B,
        )
        print(f"Stock check passed: {availability}")
    except ValueError as e:
        print(f"Stock check failed: {e}")
        raise

    # Perform mixing operation
    position = ["B1", "B2", "B3"]  # Color reservoirs
    portion = {"B1": R, "B2": Y, "B3": B}
    color_volume = {"B1": R, "B2": Y, "B3": B}

    for pos in position:
        if float(portion[pos]) != 0.0:
            p300.pick_up_tip(tiprack_1[pos])
            p300.aspirate(color_volume[pos], reservoir[pos])
            p300.dispense(color_volume[pos], plate[mix_well])
            p300.blow_out(reservoir["A1"].top(z=-5))
            p300.drop_tip(tiprack_1[pos])

    print(f"Mixed R:{R}, Y:{Y}, B:{B} in well {mix_well}")
    
    # Update inventory after successful mixing
    print("Updating inventory...")
    updated_inventory = subtract_stock(
        red_volume=R,
        yellow_volume=Y,
        blue_volume=B,
    )
    print(f"Inventory updated: {updated_inventory}")
    
    result = {
        "status": "success",
        "mix_well": mix_well,
        "volumes_used": {"R": R, "Y": Y, "B": B},
        "updated_inventory": updated_inventory,
    }
    
    return result


@flow(name="mix-color")
def mix_color(R: int, Y: int, B: int, G: int, mix_well: str):
    """
    Mix colors with specified RGB values into a well (without inventory tracking).

    This is the original flow without inventory management.
    Use mix_color_with_inventory for operations that track stock levels.

    Parameters:
    - R, Y, B, G: Volumes of Red, Yellow, Blue, Green colors (0-300 ul total)
    - mix_well: Well identifier (e.g., "B2")
    """
    total = R + Y + B + G
    if total > 300:
        raise ValueError("The sum of the proportions must be <= 300")

    position = ["B1", "B2", "B3"]  # Color reservoirs
    portion = {"B1": R, "B2": Y, "B3": B}
    color_volume = {"B1": R, "B2": Y, "B3": B}

    for pos in position:
        if float(portion[pos]) != 0.0:
            p300.pick_up_tip(tiprack_1[pos])
            p300.aspirate(color_volume[pos], reservoir[pos])
            p300.dispense(color_volume[pos], plate[mix_well])
            p300.blow_out(reservoir["A1"].top(z=-5))
            p300.drop_tip(tiprack_1[pos])

    print(f"Mixed R:{R}, Y:{Y}, B:{B} in well {mix_well}")
    return f"Color mixed in {mix_well}"


@flow(name="move-sensor-to-measurement-position")
def move_sensor_to_measurement_position(mix_well: str):
    """
    Move sensor to measurement position above the specified well.

    Parameters:
    - mix_well: Well identifier (e.g., "B2")
    """
    p300.pick_up_tip(tiprack_2["A2"])
    p300.move_to(plate[mix_well].top(z=-1))
    print("Sensor is now in position for measurement")
    return "Sensor positioned"


@flow(name="move-sensor-back")
def move_sensor_back():
    """
    Move sensor back to charging position.
    """
    p300.drop_tip(tiprack_2["A2"].top(z=-80))
    print("Sensor moved back to charging position")
    return "Sensor charged"


# Deployment configuration - Run this section when setting up deployments
if __name__ == "__main__":
    # Deploy mix_color_with_inventory flow to high-priority queue
    mix_color_with_inventory.from_source(
        source=GitRepository(
            "https://github.com/AccelerationConsortium/ac-training-lab.git"
        ),
        entrypoint="src/ac_training_lab/ot-2/_scripts/prefect_deploy/device_with_inventory.py:mix_color_with_inventory",
    ).deploy(
        name="mix-color-with-inventory",
        work_pool_name="ot2-device-pool",
        work_queue_name="high-priority",
        description="Deployment for mixing colors on OT-2 device with inventory tracking",
        tags=["ot2", "color-mixing", "inventory", "high-priority"],
    )

    # Deploy original mix_color flow (for backward compatibility)
    mix_color.from_source(
        source=GitRepository(
            "https://github.com/AccelerationConsortium/ac-training-lab.git"
        ),
        entrypoint="src/ac_training_lab/ot-2/_scripts/prefect_deploy/device_with_inventory.py:mix_color",
    ).deploy(
        name="mix-color",
        work_pool_name="ot2-device-pool",
        work_queue_name="high-priority",
        description="Deployment for mixing colors on OT-2 device (no inventory tracking)",
        tags=["ot2", "color-mixing", "high-priority"],
    )

    print("Deployments created successfully!")
