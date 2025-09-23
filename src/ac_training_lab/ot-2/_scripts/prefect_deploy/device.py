"""
device.py - OT-2 Device Operations with Prefect Deployments
This file defines Prefect flows for OT-2 device operations and creates deployments
to work pools and work queues. Run this when setting up deployments or when flow
schemas change.
"""

from prefect import flow, task
import opentrons
from prefect.runner.storage import GitRepository
import time  # Simulating OT-2 operations


# ------------------- OT-2 Setup -------------------
protocol = opentrons.simulate.get_protocol_api("2.12")
protocol.home()


# Simulate OT-2 protocol API (in real implementation, this would be opentrons.simulate)
class MockProtocol:
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


# Initialize mock protocol (replace with real opentrons.simulate in production)
protocol = MockProtocol()
protocol.home()

# Load mock labware (replace with real definitions in production)
tiprack_2 = protocol.load_labware("mock_definition", 10)
reservoir = protocol.load_labware("mock_definition", 3)
plate = protocol.load_labware("mock_definition", 1)
tiprack_1 = protocol.load_labware("mock_definition", 9)

p300 = protocol.load_instrument("p300_single_gen2", "right", [tiprack_1])


@flow(name="mix-color")
def mix_color(R: int, Y: int, B: int, G: int, mix_well: str):
    """
    Mix colors with specified RGB values into a well.

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
    # Deploy mix_color flow to high-priority queue
    mix_color.from_source(
        source=GitRepository(
            "https://github.com/AccelerationConsortium/ac-training-lab.git"
        ),
        entrypoint="src/ac_training_lab/ot-2/_scripts/prefect_deploy/device.py:mix_color",
    ).deploy(
        name="mix-color",
        work_pool_name="ot2-device-pool",
        work_queue_name="high-priority",  # High priority for color mixing
        description="Deployment for mixing colors on OT-2 device",
        tags=["ot2", "color-mixing", "high-priority"],
    )  # NOTE: this would likely become a github actions workflow to auto-deploy on push
    # NOTE: if doing this locally instead of with a git repo, in from_source, pass a filepath and entrypoint

    # # Deploy move_sensor_to_measurement_position flow to standard queue
    # move_sensor_to_measurement_position.deploy(
    #     name="move-sensor-to-measurement-position",
    #     work_pool_name="ot2-device-pool",
    #     work_queue_name="standard",  # Standard priority for sensor movement
    #     description="Deployment for moving sensor to measurement position",
    #     tags=["ot2", "sensor", "measurement"],
    # )

    # # Deploy move_sensor_back flow to low-priority queue
    # move_sensor_back.deploy(
    #     name="move-sensor-back",
    #     work_pool_name="ot2-device-pool",
    #     work_queue_name="low-priority",  # Low priority for sensor reset
    #     description="Deployment for moving sensor back to charging position",
    #     tags=["ot2", "sensor", "charging"],
    # )

    print("Deployments created successfully!")
