"""Gripper control demonstration for xArm5.

This script demonstrates how to control various gripper types with the xArm5.
Supports standard gripper, BIO gripper, and RobotIQ gripper.
"""

import time

from xarm.wrapper import XArmAPI

# Configuration
XARM_IP = "192.168.1.100"  # Replace with your xArm5 IP address
GRIPPER_TYPE = "standard"  # Options: "standard", "bio", "robotiq"


def demo_standard_gripper(arm):
    """Demonstrate standard xArm gripper."""
    print("\n" + "-" * 60)
    print("Standard Gripper Demo")
    print("-" * 60)

    # Enable gripper
    print("\nEnabling gripper...")
    arm.set_gripper_enable(True)
    arm.set_gripper_mode(0)
    time.sleep(1)

    # Get current gripper position
    ret = arm.get_gripper_position()
    if ret[0] == 0:
        print(f"Current gripper position: {ret[1]} (0=closed, 800=open)")

    # Open gripper
    print("\nOpening gripper...")
    arm.set_gripper_position(800, wait=True)
    print("✓ Gripper opened")
    time.sleep(1)

    # Partially close
    print("\nPartially closing gripper (400/800)...")
    arm.set_gripper_position(400, wait=True)
    print("✓ Gripper at 50% position")
    time.sleep(1)

    # Close gripper
    print("\nClosing gripper...")
    arm.set_gripper_position(0, wait=True)
    print("✓ Gripper closed")
    time.sleep(1)

    # Open again
    print("\nOpening gripper again...")
    arm.set_gripper_position(800, wait=True)
    print("✓ Gripper opened")


def demo_bio_gripper(arm):
    """Demonstrate BIO gripper."""
    print("\n" + "-" * 60)
    print("BIO Gripper Demo")
    print("-" * 60)

    # Enable BIO gripper
    print("\nEnabling BIO gripper...")
    arm.set_bio_gripper_enable(True)
    time.sleep(1)

    # Set speed
    arm.set_bio_gripper_speed(500)

    # Get status
    ret = arm.get_bio_gripper_status()
    if ret[0] == 0:
        print(f"BIO Gripper status: {ret[1]}")

    # Open gripper
    print("\nOpening BIO gripper...")
    arm.open_bio_gripper(wait=True)
    print("✓ BIO gripper opened")
    time.sleep(1)

    # Close gripper
    print("\nClosing BIO gripper...")
    arm.close_bio_gripper(wait=True)
    print("✓ BIO gripper closed")
    time.sleep(1)

    # Open again
    print("\nOpening BIO gripper again...")
    arm.open_bio_gripper(wait=True)
    print("✓ BIO gripper opened")


def demo_robotiq_gripper(arm):
    """Demonstrate RobotIQ gripper."""
    print("\n" + "-" * 60)
    print("RobotIQ Gripper Demo")
    print("-" * 60)

    # Reset and activate
    print("\nInitializing RobotIQ gripper...")
    arm.robotiq_reset()
    time.sleep(2)
    arm.robotiq_set_activate(True)
    time.sleep(2)

    # Get status
    ret = arm.robotiq_get_status()
    if ret[0] == 0:
        print(f"RobotIQ status: {ret[1]}")

    # Open gripper
    print("\nOpening RobotIQ gripper...")
    arm.robotiq_open(wait=True)
    print("✓ RobotIQ gripper opened")
    time.sleep(1)

    # Set specific position
    print("\nSetting RobotIQ gripper to 50% (128/255)...")
    arm.robotiq_set_position(128, wait=True)
    print("✓ RobotIQ gripper at 50% position")
    time.sleep(1)

    # Close gripper
    print("\nClosing RobotIQ gripper...")
    arm.robotiq_close(wait=True)
    print("✓ RobotIQ gripper closed")
    time.sleep(1)

    # Open again
    print("\nOpening RobotIQ gripper again...")
    arm.robotiq_open(wait=True)
    print("✓ RobotIQ gripper opened")


def main():
    """Execute gripper demonstration."""
    print("=" * 60)
    print("XArm5 Gripper Control Demo")
    print(f"Gripper Type: {GRIPPER_TYPE.upper()}")
    print("=" * 60)

    # Connect to xArm5
    print(f"\nConnecting to xArm5 at {XARM_IP}...")
    arm = XArmAPI(XARM_IP)

    if not arm.connected:
        print("❌ Failed to connect to xArm5")
        return

    print("✓ Connected successfully")

    try:
        # Enable motion
        print("\nEnabling motion...")
        arm.motion_enable(enable=True)
        arm.set_mode(0)
        arm.set_state(0)
        time.sleep(1)

        # Move to working position
        print("\nMoving to working position...")
        arm.set_position(
            x=300, y=0, z=300, roll=180, pitch=0, yaw=0, speed=100, wait=True
        )
        print("✓ In working position")

        # Execute gripper demo based on type
        if GRIPPER_TYPE.lower() == "standard":
            demo_standard_gripper(arm)
        elif GRIPPER_TYPE.lower() == "bio":
            demo_bio_gripper(arm)
        elif GRIPPER_TYPE.lower() == "robotiq":
            demo_robotiq_gripper(arm)
        else:
            print(f"\n❌ Unknown gripper type: {GRIPPER_TYPE}")
            print("   Valid options: standard, bio, robotiq")

        # Return to home
        print("\nReturning to home position...")
        arm.move_gohome(wait=True)
        print("✓ Returned to home")

        print("\n" + "=" * 60)
        print("Gripper demo completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user - stopping robot...")
        arm.emergency_stop()

    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Attempting emergency stop...")
        arm.emergency_stop()

    finally:
        # Clean up
        print("\nDisconnecting...")
        arm.disconnect()
        print("✓ Disconnected safely")


if __name__ == "__main__":
    main()
