"""
Zaber Linear Rail Control Module.

Simple wrappers around zaber-motion library for Prefect integration.

Example:
    from ac_training_lab.zaber_linear_rail import connect, home, move_absolute

    connect()
    home()
    move_absolute(100.0)  # Move to 100mm
"""

from ac_training_lab.zaber_linear_rail.config import SERIAL_PORT
from ac_training_lab.zaber_linear_rail.rail_controller import (
    connect,
    disconnect,
    get_position,
    home,
    move_absolute,
    move_relative,
    stop,
)

__all__ = [
    "connect",
    "disconnect",
    "home",
    "move_absolute",
    "move_relative",
    "get_position",
    "stop",
    "SERIAL_PORT",
]
