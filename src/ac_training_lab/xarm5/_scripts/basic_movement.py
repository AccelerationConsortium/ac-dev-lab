"""Basic movement example for xArm5.

This script demonstrates basic movement commands for the xArm5 robotic arm.
Includes connection, enabling motion, moving to positions, and safe shutdown.
"""

from xarm.wrapper import XArmAPI
import time

# Configuration
XARM_IP = "192.168.1.100"  # Replace with your xArm5 IP address


def main():
    """Execute basic movement demonstration."""
    print("=" * 60)
    print("XArm5 Basic Movement Demo")
    print("=" * 60)
    
    # Connect to xArm5
    print(f"\nConnecting to xArm5 at {XARM_IP}...")
    arm = XArmAPI(XARM_IP)
    
    if not arm.connected:
        print("❌ Failed to connect to xArm5")
        return
    
    print("✓ Connected successfully")
    print(f"  Robot version: {arm.version}")
    print(f"  Robot state: {arm.state}")
    
    try:
        # Enable motion
        print("\nEnabling motion...")
        arm.motion_enable(enable=True)
        arm.set_mode(0)  # Position control mode
        arm.set_state(0)  # Ready state
        time.sleep(1)
        
        # Move to home position
        print("\nMoving to home position...")
        arm.move_gohome(wait=True)
        print("✓ Reached home position")
        time.sleep(1)
        
        # Get current position
        position = arm.get_position()
        print(f"\nCurrent position:")
        print(f"  X: {position[1][0]:.2f} mm")
        print(f"  Y: {position[1][1]:.2f} mm")
        print(f"  Z: {position[1][2]:.2f} mm")
        print(f"  Roll: {position[1][3]:.2f}°")
        print(f"  Pitch: {position[1][4]:.2f}°")
        print(f"  Yaw: {position[1][5]:.2f}°")
        
        # Movement sequence
        print("\nExecuting movement sequence...")
        
        # Position 1
        print("\n  Moving to position 1 (forward)...")
        arm.set_position(
            x=300, y=0, z=200,
            roll=180, pitch=0, yaw=0,
            speed=100,
            wait=True
        )
        print("  ✓ Position 1 reached")
        time.sleep(1)
        
        # Position 2
        print("\n  Moving to position 2 (left)...")
        arm.set_position(
            x=300, y=100, z=200,
            roll=180, pitch=0, yaw=0,
            speed=100,
            wait=True
        )
        print("  ✓ Position 2 reached")
        time.sleep(1)
        
        # Position 3
        print("\n  Moving to position 3 (right)...")
        arm.set_position(
            x=300, y=-100, z=200,
            roll=180, pitch=0, yaw=0,
            speed=100,
            wait=True
        )
        print("  ✓ Position 3 reached")
        time.sleep(1)
        
        # Return to home
        print("\nReturning to home position...")
        arm.move_gohome(wait=True)
        print("✓ Returned to home")
        
        print("\n" + "=" * 60)
        print("Movement sequence completed successfully!")
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
