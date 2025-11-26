"""
Configuration settings for Zaber linear rail control.

Edit these values during initial setup to match your hardware and environment.
"""

import os

# Serial port where Zaber device is connected (USB)
# On Raspberry Pi, typically /dev/ttyUSB0 or /dev/ttyACM0
SERIAL_PORT = os.getenv("ZABER_SERIAL_PORT", "/dev/ttyUSB0")

# Device index is 0-based (for device_list), axis number is 1-based (Zaber)
DEVICE_INDEX = int(os.getenv("ZABER_DEVICE_INDEX", "0"))
AXIS_NUMBER = int(os.getenv("ZABER_AXIS_NUMBER", "1"))
