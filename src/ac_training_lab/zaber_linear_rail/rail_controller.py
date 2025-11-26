"""
Core controller for Zaber linear rail.

Provides low-level functions for connecting to and controlling a Zaber linear rail.
Uses the zaber-motion library for communication.
"""

import json
from pathlib import Path
from typing import Optional

from zaber_motion import Library
from zaber_motion.ascii import Axis, Connection

from ac_training_lab.zaber_linear_rail.config import (
    AXIS_NUMBER,
    DEFAULT_ACCELERATION,
    DEFAULT_VELOCITY,
    DEVICE_INDEX,
    IOT_DEVICE_ID,
    IOT_TOKEN,
    MAX_POSITION,
    MIN_POSITION,
    SERIAL_PORT,
    STATE_FILE,
    TCP_HOST,
    TCP_PORT,
)

# Global connection and axis references
_connection: Optional[Connection] = None
_axis: Optional[Axis] = None


def _load_state() -> dict:
    """Load state from file."""
    state_path = Path(STATE_FILE)
    if state_path.exists():
        with open(state_path) as f:
            return json.load(f)
    return {"last_position": None, "is_homed": False}


def _save_state(state: dict) -> None:
    """Save state to file."""
    with open(STATE_FILE, "w") as f:
        json.dump(state, f, indent=2)


def connect(
    serial_port: Optional[str] = None,
    tcp_host: Optional[str] = None,
    tcp_port: Optional[int] = None,
) -> dict:
    """
    Connect to Zaber device.

    Connection priority:
    1. TCP if tcp_host provided
    2. IoT if IOT_DEVICE_ID configured
    3. Serial port (default)

    Args:
        serial_port: Override serial port (default: from config)
        tcp_host: TCP host for network connection
        tcp_port: TCP port for network connection

    Returns:
        dict with connection info
    """
    global _connection, _axis

    Library.enable_device_db_store()

    # Determine connection method
    if tcp_host or TCP_HOST:
        host = tcp_host or TCP_HOST
        port = tcp_port or TCP_PORT
        print(f"Connecting via TCP to {host}:{port}...")
        _connection = Connection.open_tcp(host, port)
    elif IOT_DEVICE_ID:
        print(f"Connecting via IoT to device {IOT_DEVICE_ID}...")
        _connection = Connection.open_iot(IOT_DEVICE_ID, IOT_TOKEN or "unauthenticated")
    else:
        port = serial_port or SERIAL_PORT
        print(f"Connecting via serial port {port}...")
        _connection = Connection.open_serial_port(port)

    # Detect devices
    device_list = _connection.detect_devices()
    if not device_list:
        _connection.close()
        _connection = None
        raise RuntimeError("No Zaber devices found")

    print(f"Found {len(device_list)} device(s)")

    # Get the configured device
    if DEVICE_INDEX >= len(device_list):
        _connection.close()
        _connection = None
        raise RuntimeError(
            f"Device index {DEVICE_INDEX} out of range "
            f"(found {len(device_list)} devices)"
        )

    device = device_list[DEVICE_INDEX]
    _axis = device.get_axis(AXIS_NUMBER)

    # Apply default settings
    _axis.settings.set("maxspeed", DEFAULT_VELOCITY, "mm/s")
    _axis.settings.set("accel", DEFAULT_ACCELERATION, "mm/s^2")

    return {
        "connected": True,
        "device_name": device.name,
        "device_id": device.device_id,
        "axis_count": device.axis_count,
    }


def disconnect() -> dict:
    """
    Disconnect from Zaber device.

    Returns:
        dict with status
    """
    global _connection, _axis

    if _connection:
        _connection.close()
        _connection = None
        _axis = None
        return {"disconnected": True}

    return {"disconnected": False, "message": "No active connection"}


def _ensure_connected() -> None:
    """Ensure device is connected, raise if not."""
    if _connection is None or _axis is None:
        raise RuntimeError("Not connected. Call connect() first.")


def home_axis() -> dict:
    """
    Home the axis to find reference position.

    Returns:
        dict with homing result
    """
    _ensure_connected()

    print("Homing axis...")
    _axis.home()
    _axis.wait_until_idle()

    position = _axis.get_position("mm")

    # Update state
    state = _load_state()
    state["is_homed"] = True
    state["last_position"] = position
    _save_state(state)

    print(f"Homing complete. Position: {position:.2f} mm")

    return {"success": True, "position": position, "homed": True}


def move_to_position(target_position: float, velocity: Optional[float] = None) -> dict:
    """
    Move axis to absolute position.

    Args:
        target_position: Target position in mm
        velocity: Optional velocity override in mm/s

    Returns:
        dict with movement result
    """
    _ensure_connected()

    # Validate position
    if not (MIN_POSITION <= target_position <= MAX_POSITION):
        raise ValueError(
            f"Target position {target_position} mm is out of range "
            f"[{MIN_POSITION}, {MAX_POSITION}]"
        )

    # Get starting position
    start_position = _axis.get_position("mm")

    # Set velocity if provided
    if velocity:
        _axis.settings.set("maxspeed", velocity, "mm/s")

    print(f"Moving from {start_position:.2f} mm to {target_position:.2f} mm...")
    _axis.move_absolute(target_position, "mm")
    _axis.wait_until_idle()

    # Get final position
    final_position = _axis.get_position("mm")

    # Update state
    state = _load_state()
    state["last_position"] = final_position
    _save_state(state)

    print(f"Movement complete. Final position: {final_position:.2f} mm")

    return {
        "success": True,
        "start_position": start_position,
        "target_position": target_position,
        "final_position": final_position,
        "distance": abs(final_position - start_position),
    }


def move_relative(distance: float, velocity: Optional[float] = None) -> dict:
    """
    Move axis by relative distance.

    Args:
        distance: Distance to move in mm (positive or negative)
        velocity: Optional velocity override in mm/s

    Returns:
        dict with movement result
    """
    _ensure_connected()

    # Get current position
    current_position = _axis.get_position("mm")
    target_position = current_position + distance

    # Validate target position
    if not (MIN_POSITION <= target_position <= MAX_POSITION):
        raise ValueError(
            f"Target position {target_position} mm would be out of range "
            f"[{MIN_POSITION}, {MAX_POSITION}]"
        )

    # Set velocity if provided
    if velocity:
        _axis.settings.set("maxspeed", velocity, "mm/s")

    print(f"Moving {distance:+.2f} mm from {current_position:.2f} mm...")
    _axis.move_relative(distance, "mm")
    _axis.wait_until_idle()

    # Get final position
    final_position = _axis.get_position("mm")

    # Update state
    state = _load_state()
    state["last_position"] = final_position
    _save_state(state)

    print(f"Movement complete. Final position: {final_position:.2f} mm")

    return {
        "success": True,
        "start_position": current_position,
        "distance_requested": distance,
        "final_position": final_position,
        "actual_distance": final_position - current_position,
    }


def get_position() -> dict:
    """
    Get current axis position.

    Returns:
        dict with position info
    """
    _ensure_connected()

    position = _axis.get_position("mm")
    is_busy = _axis.is_busy()

    return {"position": position, "busy": is_busy}


def stop_movement() -> dict:
    """
    Stop current movement immediately.

    Returns:
        dict with stop result
    """
    _ensure_connected()

    _axis.stop()
    position = _axis.get_position("mm")

    return {"stopped": True, "position": position}


def get_device_info() -> dict:
    """
    Get device information.

    Returns:
        dict with device info
    """
    _ensure_connected()

    device = _axis.device

    # Get current settings
    max_speed = _axis.settings.get("maxspeed", "mm/s")
    accel = _axis.settings.get("accel", "mm/s^2")
    position = _axis.get_position("mm")

    return {
        "device_name": device.name,
        "device_id": device.device_id,
        "axis_number": AXIS_NUMBER,
        "axis_count": device.axis_count,
        "current_position": position,
        "max_speed": max_speed,
        "acceleration": accel,
        "position_limits": {"min": MIN_POSITION, "max": MAX_POSITION},
    }
