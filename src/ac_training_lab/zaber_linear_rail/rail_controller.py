"""
Core controller for Zaber linear rail.

Simple wrappers around zaber-motion library for Prefect task integration.
"""

from typing import Optional

from zaber_motion import Library
from zaber_motion.ascii import Connection

from ac_training_lab.zaber_linear_rail.config import (
    AXIS_NUMBER,
    DEVICE_INDEX,
    SERIAL_PORT,
)

# Global connection and axis references
_connection: Optional[Connection] = None
_axis = None


def _check_connected():
    """Raise if not connected."""
    if _axis is None:
        raise RuntimeError("Not connected. Call connect() first.")


def connect(serial_port: Optional[str] = None) -> dict:
    """Connect to Zaber device via USB serial."""
    global _connection, _axis

    Library.enable_device_db_store()
    port = serial_port or SERIAL_PORT
    _connection = Connection.open_serial_port(port)
    device_list = _connection.detect_devices()

    if not device_list:
        _connection.close()
        _connection = None
        raise RuntimeError("No Zaber devices found")

    device = device_list[DEVICE_INDEX]
    _axis = device.get_axis(AXIS_NUMBER)

    return {
        "device_name": device.name,
        "device_id": device.device_id,
        "axis_count": device.axis_count,
    }


def disconnect() -> None:
    """Disconnect from Zaber device."""
    global _connection, _axis
    if _connection:
        _connection.close()
        _connection = None
        _axis = None


def home() -> float:
    """Home the axis. Returns position in mm."""
    _check_connected()
    _axis.home()
    _axis.wait_until_idle()
    return _axis.get_position("mm")


def move_absolute(position: float, unit: str = "mm") -> float:
    """Move to absolute position. Returns final position."""
    _check_connected()
    _axis.move_absolute(position, unit)
    _axis.wait_until_idle()
    return _axis.get_position("mm")


def move_relative(distance: float, unit: str = "mm") -> float:
    """Move by relative distance. Returns final position."""
    _check_connected()
    _axis.move_relative(distance, unit)
    _axis.wait_until_idle()
    return _axis.get_position("mm")


def get_position(unit: str = "mm") -> float:
    """Get current position."""
    _check_connected()
    return _axis.get_position(unit)


def stop() -> float:
    """Stop movement. Returns position."""
    _check_connected()
    _axis.stop()
    return _axis.get_position("mm")
