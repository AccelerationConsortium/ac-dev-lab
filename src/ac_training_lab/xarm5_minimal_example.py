"""Minimal example for controlling UFACTORY xArm5 from Raspberry Pi 5.

This script demonstrates basic programmatic control of the xArm5 robotic arm.

Installation:
    pip install xarm-python-sdk

Usage:
    python xarm5_minimal_example.py
"""

from xarm.wrapper import XArmAPI

# Configuration
XARM_IP = "192.168.1.100"  # Replace with your xArm5 IP address


def main():
    """Minimal example of xArm5 control."""
    # Connect to xArm5
    arm = XArmAPI(XARM_IP)

    # Enable motion
    arm.motion_enable(enable=True)
    arm.set_mode(0)  # Position control mode
    arm.set_state(0)  # Ready state

    # Move to home position
    arm.move_gohome(wait=True)

    # Move to a position (x, y, z in mm, angles in degrees)
    arm.set_position(x=300, y=0, z=200, roll=180, pitch=0, yaw=0, speed=100, wait=True)

    # Disconnect
    arm.disconnect()


if __name__ == "__main__":
    main()
