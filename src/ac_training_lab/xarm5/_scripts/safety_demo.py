"""Safety features demonstration for xArm5.

This script demonstrates safety features including emergency stop,
error handling, collision detection, and safe workspace limits.
"""

import time

from xarm.wrapper import XArmAPI

# Configuration
XARM_IP = "192.168.1.100"  # Replace with your xArm5 IP address

# Workspace limits (in mm)
WORKSPACE_LIMITS = {
    "x_min": 100,
    "x_max": 500,
    "y_min": -300,
    "y_max": 300,
    "z_min": 50,
    "z_max": 500,
}


def check_workspace_limits(position):
    """Check if position is within safe workspace limits.

    Args:
        position: Tuple of (x, y, z) coordinates in mm

    Returns:
        bool: True if position is safe, False otherwise
    """
    x, y, z = position

    if not (WORKSPACE_LIMITS["x_min"] <= x <= WORKSPACE_LIMITS["x_max"]):
        x_min = WORKSPACE_LIMITS["x_min"]
        x_max = WORKSPACE_LIMITS["x_max"]
        print(f"⚠️  X position {x} outside limits [{x_min}, {x_max}]")
        return False

    if not (WORKSPACE_LIMITS["y_min"] <= y <= WORKSPACE_LIMITS["y_max"]):
        y_min = WORKSPACE_LIMITS["y_min"]
        y_max = WORKSPACE_LIMITS["y_max"]
        print(f"⚠️  Y position {y} outside limits [{y_min}, {y_max}]")
        return False

    if not (WORKSPACE_LIMITS["z_min"] <= z <= WORKSPACE_LIMITS["z_max"]):
        z_min = WORKSPACE_LIMITS["z_min"]
        z_max = WORKSPACE_LIMITS["z_max"]
        print(f"⚠️  Z position {z} outside limits [{z_min}, {z_max}]")
        return False

    return True


def demo_safe_movement(arm):
    """Demonstrate safe movement with workspace limits."""
    print("\n" + "-" * 60)
    print("Safe Movement Demo")
    print("-" * 60)

    # Test safe position
    safe_position = (300, 0, 200)
    print(f"\nTesting safe position {safe_position}...")
    if check_workspace_limits(safe_position):
        print("✓ Position is safe - executing movement")
        arm.set_position(
            x=safe_position[0],
            y=safe_position[1],
            z=safe_position[2],
            roll=180,
            pitch=0,
            yaw=0,
            speed=100,
            wait=True,
        )
        print("✓ Movement completed")
        time.sleep(1)
    else:
        print("❌ Position rejected - outside workspace limits")

    # Test unsafe position (too far)
    unsafe_position = (700, 0, 200)
    print(f"\nTesting unsafe position {unsafe_position}...")
    if check_workspace_limits(unsafe_position):
        print("✓ Position is safe - would execute movement")
    else:
        print("❌ Position rejected - outside workspace limits")
        print("   Movement NOT executed for safety")


def demo_error_handling(arm):
    """Demonstrate error detection and recovery."""
    print("\n" + "-" * 60)
    print("Error Handling Demo")
    print("-" * 60)

    # Check for errors
    err_code = arm.error_code
    warn_code = arm.warn_code

    print(f"\nCurrent error code: {err_code}")
    print(f"Current warning code: {warn_code}")

    if arm.has_error:
        print("⚠️  Robot has errors - attempting to clear...")
        arm.clean_error()
        time.sleep(1)

        if arm.has_error:
            print("❌ Failed to clear errors")
        else:
            print("✓ Errors cleared successfully")
    else:
        print("✓ No errors detected")

    if arm.has_warn:
        print("⚠️  Robot has warnings - attempting to clear...")
        arm.clean_warn()
        time.sleep(1)

        if arm.has_warn:
            print("❌ Failed to clear warnings")
        else:
            print("✓ Warnings cleared successfully")
    else:
        print("✓ No warnings detected")


def demo_collision_sensitivity(arm):
    """Demonstrate collision sensitivity settings."""
    print("\n" + "-" * 60)
    print("Collision Sensitivity Demo")
    print("-" * 60)

    # Set collision sensitivity (0-5, where 0 is least sensitive)
    sensitivity = 3
    print(f"\nSetting collision sensitivity to {sensitivity}...")
    arm.set_collision_sensitivity(sensitivity)
    time.sleep(0.5)

    print(f"✓ Collision sensitivity set to {arm.collision_sensitivity}")
    print("  Note: Higher values = more sensitive collision detection")


def demo_emergency_stop(arm):
    """Demonstrate emergency stop functionality."""
    print("\n" + "-" * 60)
    print("Emergency Stop Demo")
    print("-" * 60)

    print("\nStarting a slow movement...")
    print("(In a real emergency, you would call arm.emergency_stop())")

    # Start a movement
    arm.set_position(
        x=350,
        y=0,
        z=200,
        roll=180,
        pitch=0,
        yaw=0,
        speed=50,  # Slow speed for demonstration
        wait=False,  # Don't wait for completion
    )

    # Simulate waiting a bit
    time.sleep(0.5)

    # Emergency stop
    print("\n⚠️  EMERGENCY STOP triggered!")
    arm.emergency_stop()
    print("✓ Robot stopped immediately")

    # Recovery process
    print("\nRecovering from emergency stop...")
    time.sleep(1)

    # Clear errors and reset state
    arm.clean_error()
    arm.set_state(0)
    time.sleep(1)

    print("✓ Robot recovered and ready")


def main():
    """Execute safety features demonstration."""
    print("=" * 60)
    print("XArm5 Safety Features Demo")
    print("=" * 60)

    print("\nWorkspace Limits:")
    for key, value in WORKSPACE_LIMITS.items():
        print(f"  {key}: {value} mm")

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

        # Move to starting position
        print("\nMoving to starting position...")
        arm.move_gohome(wait=True)
        print("✓ At starting position")

        # Run safety demonstrations
        demo_error_handling(arm)
        demo_collision_sensitivity(arm)
        demo_safe_movement(arm)
        demo_emergency_stop(arm)

        # Return to home
        print("\nReturning to home position...")
        arm.move_gohome(wait=True)
        print("✓ Returned to home")

        print("\n" + "=" * 60)
        print("Safety demo completed successfully!")
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
