"""
Configuration settings for Zaber linear rail control.

Edit these values during initial setup to match your hardware and environment.
"""

import os

# =============================================================================
# CONNECTION CONFIGURATION
# =============================================================================
# Serial port where Zaber device is connected
# On Raspberry Pi, typically /dev/ttyUSB0 or /dev/ttyACM0
SERIAL_PORT = os.getenv("ZABER_SERIAL_PORT", "/dev/ttyUSB0")

# Alternative connection methods
TCP_HOST = os.getenv("ZABER_TCP_HOST", "")
TCP_PORT = int(os.getenv("ZABER_TCP_PORT", "55550"))

# IoT connection (for Zaber Cloud-connected devices)
IOT_DEVICE_ID = os.getenv("ZABER_IOT_DEVICE_ID", "")
IOT_TOKEN = os.getenv("ZABER_IOT_TOKEN", "")


# =============================================================================
# DEVICE CONFIGURATION
# =============================================================================
# Device and axis indices (1-based indexing as per Zaber convention)
DEVICE_INDEX = int(os.getenv("ZABER_DEVICE_INDEX", "0"))  # Index in device list
AXIS_NUMBER = int(os.getenv("ZABER_AXIS_NUMBER", "1"))  # Axis number on device


# =============================================================================
# MOTION PARAMETERS
# =============================================================================
# Default velocity in mm/s (adjust based on your rail specifications)
DEFAULT_VELOCITY = float(os.getenv("ZABER_DEFAULT_VELOCITY", "50.0"))

# Default acceleration in mm/s² (adjust based on your rail specifications)
DEFAULT_ACCELERATION = float(os.getenv("ZABER_DEFAULT_ACCELERATION", "100.0"))

# Position limits in mm (set based on your rail travel range)
MIN_POSITION = float(os.getenv("ZABER_MIN_POSITION", "0.0"))
MAX_POSITION = float(os.getenv("ZABER_MAX_POSITION", "500.0"))


# =============================================================================
# SAFETY SETTINGS
# =============================================================================
# Timeout for movement operations in seconds
MOVEMENT_TIMEOUT = float(os.getenv("ZABER_MOVEMENT_TIMEOUT", "60.0"))

# Homing timeout in seconds
HOMING_TIMEOUT = float(os.getenv("ZABER_HOMING_TIMEOUT", "120.0"))


# =============================================================================
# STATE MANAGEMENT
# =============================================================================
# File to store persistent state
STATE_FILE = os.getenv("ZABER_STATE_FILE", "zaber_state.json")


# =============================================================================
# VALIDATION
# =============================================================================
def validate_config():
    """Validate configuration values."""
    errors = []

    # Validate position limits
    if MIN_POSITION >= MAX_POSITION:
        errors.append(
            f"MIN_POSITION ({MIN_POSITION}) must be less than "
            f"MAX_POSITION ({MAX_POSITION})"
        )

    # Validate velocity
    if DEFAULT_VELOCITY <= 0:
        errors.append(f"DEFAULT_VELOCITY ({DEFAULT_VELOCITY}) must be positive")

    # Validate acceleration
    if DEFAULT_ACCELERATION <= 0:
        errors.append(f"DEFAULT_ACCELERATION ({DEFAULT_ACCELERATION}) must be positive")

    # Validate timeouts
    if MOVEMENT_TIMEOUT <= 0:
        errors.append(f"MOVEMENT_TIMEOUT ({MOVEMENT_TIMEOUT}) must be positive")
    if HOMING_TIMEOUT <= 0:
        errors.append(f"HOMING_TIMEOUT ({HOMING_TIMEOUT}) must be positive")

    if errors:
        raise ValueError(
            "Configuration validation failed:\n" + "\n".join(f"  - {e}" for e in errors)
        )

    return True


# Validate on import
validate_config()
