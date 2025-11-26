"""
Zaber Linear Rail Control Module.

Provides programmatic control of Zaber linear rails via Python with Prefect workflow
orchestration support.

Example:
    from ac_training_lab.zaber_linear_rail import move_to_position, home_axis

    home_axis()
    move_to_position(100.0)  # Move to 100mm
"""

from ac_training_lab.zaber_linear_rail.config import (
    DEFAULT_ACCELERATION,
    DEFAULT_VELOCITY,
    SERIAL_PORT,
)
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

__all__ = [
    "connect",
    "disconnect",
    "home_axis",
    "move_to_position",
    "move_relative",
    "get_position",
    "stop_movement",
    "get_device_info",
    "SERIAL_PORT",
    "DEFAULT_VELOCITY",
    "DEFAULT_ACCELERATION",
]
