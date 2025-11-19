"""Linear track integration demonstration for xArm5.

This script demonstrates how to control the xArm5 with a linear track (rail)
for extended workspace and coordinated movements.
"""

import time

from xarm.wrapper import XArmAPI

# Configuration
XARM_IP = "192.168.1.100"  # Replace with your xArm5 IP address
TRACK_ENABLED = True  # Set to False if no track is attached


def main():
    """Execute linear track integration demonstration."""
    print("=" * 60)
    print("XArm5 Linear Track Integration Demo")
    print("=" * 60)

    # Connect to xArm5 with track enabled
    print(f"\nConnecting to xArm5 at {XARM_IP}...")
    if TRACK_ENABLED:
        print("Track mode: ENABLED")
        arm = XArmAPI(XARM_IP, enable_track=True)
    else:
        print("Track mode: DISABLED")
        arm = XArmAPI(XARM_IP)

    if not arm.connected:
        print("❌ Failed to connect to xArm5")
        return

    print("✓ Connected successfully")
    print(f"  Robot version: {arm.version}")

    try:
        # Enable motion
        print("\nEnabling motion...")
        arm.motion_enable(enable=True)
        arm.set_mode(0)
        arm.set_state(0)
        time.sleep(1)

        if TRACK_ENABLED:
            # Linear track operations
            print("\n" + "-" * 60)
            print("Linear Track Control")
            print("-" * 60)

            # Enable linear motor
            print("\nEnabling linear motor (track)...")
            arm.set_linear_motor_enable(True)
            time.sleep(1)

            # Get track status
            ret = arm.get_linear_motor_status()
            print(f"Track status: {ret}")

            # Get current track position
            ret = arm.get_linear_motor_pos()
            if ret[0] == 0:
                current_pos = ret[1]
                print(f"Current track position: {current_pos} mm")

            # Move track to position 1 (0 mm - home)
            print("\nMoving track to home position (0 mm)...")
            arm.set_linear_motor_pos(0, wait=True)
            print("✓ Track at home position")
            time.sleep(1)

            # Verify position
            ret = arm.get_linear_motor_pos()
            if ret[0] == 0:
                print(f"  Confirmed position: {ret[1]} mm")

            # Move track to position 2 (300 mm)
            print("\nMoving track to position 300 mm...")
            arm.set_linear_motor_pos(300, wait=True)
            print("✓ Track at 300 mm")
            time.sleep(1)

            # Verify position
            ret = arm.get_linear_motor_pos()
            if ret[0] == 0:
                print(f"  Confirmed position: {ret[1]} mm")

            # Move track to position 3 (600 mm)
            print("\nMoving track to position 600 mm...")
            arm.set_linear_motor_pos(600, wait=True)
            print("✓ Track at 600 mm")
            time.sleep(1)

            # Verify position
            ret = arm.get_linear_motor_pos()
            if ret[0] == 0:
                print(f"  Confirmed position: {ret[1]} mm")

            # Coordinated arm and track movement
            print("\n" + "-" * 60)
            print("Coordinated Arm + Track Movement")
            print("-" * 60)

            # Position 1: Track at 0, arm reaching forward
            print("\nPosition 1: Track home, arm forward...")
            arm.set_linear_motor_pos(0, wait=True)
            arm.set_position(
                x=400, y=0, z=200, roll=180, pitch=0, yaw=0, speed=100, wait=True
            )
            print("✓ Position 1 reached")
            time.sleep(1)

            # Position 2: Track at 300, arm centered
            print("\nPosition 2: Track 300mm, arm centered...")
            arm.set_linear_motor_pos(300, wait=True)
            arm.set_position(
                x=300, y=0, z=200, roll=180, pitch=0, yaw=0, speed=100, wait=True
            )
            print("✓ Position 2 reached")
            time.sleep(1)

            # Position 3: Track at 600, arm reaching back
            print("\nPosition 3: Track 600mm, arm back...")
            arm.set_linear_motor_pos(600, wait=True)
            arm.set_position(
                x=200, y=0, z=200, roll=180, pitch=0, yaw=0, speed=100, wait=True
            )
            print("✓ Position 3 reached")
            time.sleep(1)

            # Return track to home
            print("\nReturning track to home position...")
            arm.set_linear_motor_pos(0, wait=True)
            print("✓ Track at home")

        else:
            # Just arm movements without track
            print("\n(Track disabled - performing arm-only movements)")

            print("\nMoving to position 1...")
            arm.set_position(
                x=300, y=0, z=200, roll=180, pitch=0, yaw=0, speed=100, wait=True
            )
            time.sleep(1)

            print("\nMoving to position 2...")
            arm.set_position(
                x=300, y=100, z=200, roll=180, pitch=0, yaw=0, speed=100, wait=True
            )
            time.sleep(1)

        # Return arm to home
        print("\nReturning arm to home position...")
        arm.move_gohome(wait=True)
        print("✓ Arm at home")

        print("\n" + "=" * 60)
        print("Track integration demo completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user - stopping robot...")
        arm.emergency_stop()
        if TRACK_ENABLED:
            arm.set_linear_motor_stop()

    except Exception as e:
        print(f"\n❌ Error occurred: {e}")
        print("Attempting emergency stop...")
        arm.emergency_stop()
        if TRACK_ENABLED:
            arm.set_linear_motor_stop()

    finally:
        # Clean up
        print("\nDisconnecting...")
        arm.disconnect()
        print("✓ Disconnected safely")


if __name__ == "__main__":
    main()
