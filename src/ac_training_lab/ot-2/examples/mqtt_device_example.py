"""
Example OT-2 device server using the lightweight MQTT wrapper.

This demonstrates how to create an MQTT-based device server for OT-2
orchestration without pydantic version conflicts.
"""

import json
import logging
from pathlib import Path

# Import Opentrons API (works with pydantic v1)
try:
    import opentrons.simulate
except ImportError:
    print("Warning: opentrons not installed. Using simulation mode.")
    opentrons = None

# Import our MQTT orchestration framework
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "orchestration"))
from mqtt_wrapper import MQTTDeviceServer, mqtt_task

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ------------------- OT-2 Setup (same as FastAPI example) -------------------
if opentrons:
    protocol = opentrons.simulate.get_protocol_api("2.12")
    protocol.home()

    # Load Labware (using relative paths for the example)
    base_path = Path(__file__).parent.parent / "_scripts"
    
    try:
        with open(base_path / "ac_color_sensor_charging_port.json", encoding="utf-8") as f1:
            labware_def1 = json.load(f1)
            tiprack_2 = protocol.load_labware_from_definition(labware_def1, 10)
    except FileNotFoundError:
        logger.warning("Color sensor labware definition not found, using default tiprack")
        tiprack_2 = protocol.load_labware("opentrons_96_tiprack_300ul", location=10)

    try:
        with open(base_path / "ac_6_tuberack_15000ul.json", encoding="utf-8") as f2:
            labware_def2 = json.load(f2)
            reservoir = protocol.load_labware_from_definition(labware_def2, 3)
    except FileNotFoundError:
        logger.warning("Reservoir labware definition not found, using default")
        reservoir = protocol.load_labware("opentrons_24_tuberack_eppendorf_1.5ml_safelock_snapcap", location=3)

    plate = protocol.load_labware("corning_96_wellplate_360ul_flat", location=1)
    tiprack_1 = protocol.load_labware("opentrons_96_tiprack_300ul", location=9)

    p300 = protocol.load_instrument(
        instrument_name="p300_single_gen2", mount="right", tip_racks=[tiprack_1]
    )
    p300.well_bottom_clearance.dispense = 8

    logger.info("Labwares loaded successfully")
else:
    # Mock objects for testing without Opentrons
    protocol = None
    tiprack_2 = None
    reservoir = None
    plate = None
    tiprack_1 = None
    p300 = None
    logger.info("Running in simulation mode (no Opentrons)")


# ------------------- MQTT Task Definitions -------------------

@mqtt_task
def mix_color(R: int, Y: int, B: int, mix_well: str) -> str:
    """
    Mix colors with specified RGB values into a well.
    
    Args:
        R: Red component (0-300)
        Y: Yellow component (0-300) 
        B: Blue component (0-300)
        mix_well: Target well (e.g., "A1")
        
    Returns:
        Status message
    """
    total = R + Y + B
    if total > 300:
        raise ValueError("The sum of the proportions must be <= 300")
    
    logger.info(f"Mixing R:{R}, Y:{Y}, B:{B} in well {mix_well}")
    
    if not opentrons:
        return f"SIMULATED: Mixed R:{R}, Y:{Y}, B:{B} in well {mix_well}"
    
    # Real OT-2 operation
    position = ["B1", "B2", "B3"]  # R, Y, B vial positions
    portion = {"B1": R, "B2": Y, "B3": B}
    color_volume = {"B1": R, "B2": Y, "B3": B}

    for pos in position:
        if float(portion[pos]) != 0.0:
            p300.pick_up_tip(tiprack_1[pos])
            p300.aspirate(color_volume[pos], reservoir[pos])
            p300.dispense(color_volume[pos], plate[mix_well])
            p300.default_speed = 100
            p300.blow_out(reservoir["A1"].top(z=-5))
            p300.default_speed = 400
            p300.drop_tip(tiprack_1[pos])

    return f"Mixed R:{R}, Y:{Y}, B:{B} in well {mix_well}"


@mqtt_task
def move_sensor_to_measurement_position(mix_well: str) -> str:
    """Move sensor to measurement position above specified well."""
    logger.info(f"Moving sensor to measurement position over well {mix_well}")
    
    if not opentrons:
        return f"SIMULATED: Sensor positioned over well {mix_well}"
    
    p300.pick_up_tip(tiprack_2["A2"])
    p300.move_to(plate[mix_well].top(z=-1.3))
    
    return f"Sensor is now in position for measurement over well {mix_well}"


@mqtt_task 
def move_sensor_back() -> str:
    """Move sensor back to charging position."""
    logger.info("Moving sensor back to charging position")
    
    if not opentrons:
        return "SIMULATED: Sensor moved back to charging position"
    
    p300.drop_tip(tiprack_2["A2"].top(z=-80))
    return "Sensor moved back to charging position"


@mqtt_task
def home_robot() -> str:
    """Home the robot to its initial position."""
    logger.info("Homing robot")
    
    if not opentrons:
        return "SIMULATED: Robot homed"
    
    protocol.home()
    return "Robot homed successfully"


@mqtt_task
def get_robot_status() -> dict:
    """Get current robot status and information."""
    return {
        "opentrons_available": opentrons is not None,
        "protocol_version": "2.12" if opentrons else "simulation",
        "tasks_registered": ["mix_color", "move_sensor_to_measurement_position", "move_sensor_back", "home_robot"],
        "status": "ready"
    }


def create_mqtt_ot2_server(
    broker_host: str,
    broker_port: int = 1883,
    device_id: str = None,
    username: str = None,
    password: str = None,
    use_tls: bool = False
) -> MQTTDeviceServer:
    """
    Create and configure the MQTT-based OT-2 device server.
    
    Args:
        broker_host: MQTT broker hostname
        broker_port: MQTT broker port
        device_id: Unique device identifier (auto-generated if None)
        username: MQTT username (optional)
        password: MQTT password (optional)
        use_tls: Whether to use TLS encryption
        
    Returns:
        Configured MQTTDeviceServer instance
    """
    server = MQTTDeviceServer(
        broker_host=broker_host,
        broker_port=broker_port,
        device_id=device_id,
        username=username,
        password=password,
        use_tls=use_tls,
        topic_prefix="ot2"
    )
    
    logger.info("MQTT OT-2 Device Server created successfully")
    return server


if __name__ == "__main__":
    # Configuration - update these values for your MQTT broker
    BROKER_HOST = "localhost"  # Update to your MQTT broker
    BROKER_PORT = 1883
    DEVICE_ID = "ot2-device-001"  # Unique device identifier
    USERNAME = None  # Set if your broker requires authentication
    PASSWORD = None  # Set if your broker requires authentication
    USE_TLS = False  # Set to True for secure connections
    
    print("\n" + "="*60)
    print("🤖 OT-2 MQTT Device Server Starting...")
    print("="*60)
    print(f"📡 MQTT Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"🏷️  Device ID: {DEVICE_ID}")
    print(f"🔒 TLS: {'Enabled' if USE_TLS else 'Disabled'}")
    print(f"🔐 Auth: {'Enabled' if USERNAME else 'Disabled'}")
    print("="*60)
    print("MQTT Topics:")
    print(f"  📥 Commands: ot2/{DEVICE_ID}/command")
    print(f"  📤 Results:  ot2/{DEVICE_ID}/result")
    print(f"  📊 Status:   ot2/{DEVICE_ID}/status")
    print("="*60)
    print("Press Ctrl+C to stop the server")
    print("="*60 + "\n")
    
    # Create and start the MQTT server
    try:
        server = create_mqtt_ot2_server(
            broker_host=BROKER_HOST,
            broker_port=BROKER_PORT,
            device_id=DEVICE_ID,
            username=USERNAME,
            password=PASSWORD,
            use_tls=USE_TLS
        )
        
        # Start the server (this will block)
        server.start()
        
    except KeyboardInterrupt:
        print("\n🛑 Received shutdown signal...")
        server.stop()
        print("✅ Server stopped successfully")
    except Exception as e:
        print(f"❌ Server error: {e}")
        logger.exception("Server failed")