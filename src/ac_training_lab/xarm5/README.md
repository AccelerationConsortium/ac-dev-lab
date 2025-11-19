# XArm5 Control for Raspberry Pi 5

This module provides integration for controlling the UFACTORY xArm5 robotic arm from a Raspberry Pi 5 as part of the AC Training Lab's rail/lift/arm combo system.

## Hardware Overview

The **xArm5** is a 5-degree-of-freedom collaborative robotic arm manufactured by UFACTORY. It features:
- 5 servo joints with precise control
- Network-based control via TCP/IP
- Support for various end effectors (grippers, sensors)
- Compatible with linear tracks and additional accessories
- Payload capacity suitable for laboratory automation tasks

## Prerequisites

### Hardware Requirements
- Raspberry Pi 5 (4GB or 8GB RAM recommended)
- UFACTORY xArm5 robotic arm with control box
- Ethernet connection (recommended) or WiFi
- Power supply for both Raspberry Pi and xArm5
- Optional: Linear track for extended workspace
- Optional: Gripper or end effector

### Software Requirements
- Raspberry Pi OS (Bookworm or later)
- Python 3.8 or higher
- Network connectivity between Raspberry Pi and xArm5 control box

## Installation on Raspberry Pi 5

### 1. Set Up Raspberry Pi OS

If starting fresh, use the [Raspberry Pi Imager](https://www.raspberrypi.org/software/) to install Raspberry Pi OS on a microSD card.

```bash
# Update system packages
sudo apt update
sudo apt upgrade -y
```

### 2. Install Python Dependencies

```bash
# Install Python virtual environment tools
sudo apt install python3-pip python3-venv -y

# Create a virtual environment (recommended for Bookworm OS)
python3 -m venv ~/xarm-env
source ~/xarm-env/bin/activate
```

### 3. Install xArm Python SDK

**Option A: Install from PyPI (Recommended)**
```bash
pip install xarm-python-sdk
```

**Option B: Install from source**
```bash
git clone https://github.com/xArm-Developer/xArm-Python-SDK.git
cd xArm-Python-SDK
pip install .
```

### 4. Install AC Training Lab Package (Optional)

To use this module as part of the ac-training-lab package:
```bash
# Clone the ac-training-lab repository
git clone https://github.com/AccelerationConsortium/ac-dev-lab.git
cd ac-dev-lab

# Install with xarm5 dependencies
pip install -e .
```

## Network Configuration

### Finding Your xArm5 IP Address

1. Check the xArm5 control box display panel
2. Or check your router's DHCP client list
3. Or use network scanning tools:
   ```bash
   sudo apt install nmap
   nmap -sn 192.168.1.0/24  # Adjust subnet to match your network
   ```

### Static IP Configuration (Recommended)

For reliable automation, configure a static IP for the xArm5 control box:
1. Access the control box web interface
2. Navigate to Network Settings
3. Set a static IP address (e.g., 192.168.1.100)
4. Configure gateway and DNS if needed

## Quick Start Examples

### Basic Connection Test

```python
from xarm.wrapper import XArmAPI

# Replace with your xArm5 control box IP
arm = XArmAPI('192.168.1.100')

# Check connection and get robot info
print(f"Connected: {arm.connected}")
print(f"Version: {arm.version}")
print(f"State: {arm.state}")

# Disconnect
arm.disconnect()
```

### Simple Movement Example

```python
from xarm.wrapper import XArmAPI

# Connect to xArm5
arm = XArmAPI('192.168.1.100')

# Enable motion
arm.motion_enable(enable=True)
arm.set_mode(0)  # Position control mode
arm.set_state(0)  # Ready state

# Move to home position
arm.move_gohome(wait=True)

# Move to a specific position (x, y, z in mm, angles in degrees)
arm.set_position(x=300, y=0, z=200, roll=180, pitch=0, yaw=0, speed=100, wait=True)

# Get current position
position = arm.get_position()
print(f"Current position: {position}")

# Disconnect
arm.disconnect()
```

### Using with Gripper

```python
from xarm.wrapper import XArmAPI

# Connect
arm = XArmAPI('192.168.1.100')

# Enable gripper
arm.set_gripper_enable(True)
arm.set_gripper_mode(0)

# Open gripper
arm.set_gripper_position(800, wait=True)  # 800 = fully open

# Close gripper
arm.set_gripper_position(0, wait=True)  # 0 = fully closed

# Disconnect
arm.disconnect()
```

## Rail/Lift/Arm Integration

For integration with linear tracks and vertical lifts:

### Linear Track Control

```python
from xarm.wrapper import XArmAPI

arm = XArmAPI('192.168.1.100', enable_track=True)

# Enable linear motor (track)
arm.set_linear_motor_enable(True)

# Move track to specific position (in mm)
arm.set_linear_motor_pos(500, wait=True)

# Get track position
track_pos = arm.get_linear_motor_pos()
print(f"Track position: {track_pos} mm")
```

## Example Scripts

See the `_scripts/` directory for more examples:
- `basic_movement.py` - Basic arm movements
- `gripper_demo.py` - Gripper control demonstrations
- `track_integration.py` - Linear track coordination
- `safety_demo.py` - Emergency stop and safety features

## Safety Considerations

⚠️ **IMPORTANT SAFETY WARNINGS:**

1. **Keep clear of the robot workspace** during operation
2. **Test in simulation first** before running on real hardware
3. **Use emergency stop** features in your code
4. **Start with slow speeds** when testing new movements
5. **Monitor the robot** during initial testing
6. **Set appropriate workspace limits** to prevent collisions
7. **Enable collision detection** when available

### Emergency Stop

```python
# In case of emergency
arm.emergency_stop()

# Reset after emergency stop
arm.clean_error()
arm.set_state(0)
```

## Troubleshooting

### Connection Issues

**Problem:** Cannot connect to xArm5
- Verify both devices are on the same network
- Check IP address is correct
- Ping the control box: `ping 192.168.1.100`
- Check firewall settings on Raspberry Pi
- Ensure control box is powered on and initialized

**Problem:** Connection drops frequently
- Use wired Ethernet instead of WiFi
- Check network cable quality
- Configure static IP addresses
- Reduce network traffic on the subnet

### Movement Issues

**Problem:** Robot doesn't move
- Check if motion is enabled: `arm.motion_enable(True)`
- Verify robot state: `arm.get_state()`
- Clear any errors: `arm.clean_error()`
- Check if servo is attached: `arm.set_servo_attach()`

**Problem:** Jerky or unexpected movements
- Reduce speed and acceleration parameters
- Check for network latency
- Use `wait=True` for sequential movements
- Verify trajectory planning settings

### Python Environment Issues

**Problem:** Module not found errors
- Ensure virtual environment is activated
- Reinstall xarm-python-sdk: `pip install --upgrade xarm-python-sdk`
- Check Python version compatibility (3.8+)

## Additional Resources

### Official Documentation
- [xArm Python SDK GitHub](https://github.com/xArm-Developer/xArm-Python-SDK)
- [xArm API Documentation](https://github.com/xArm-Developer/xArm-Python-SDK/blob/master/doc/api/xarm_api.md)
- [UFACTORY Official Website](https://www.ufactory.cc/)

### Community Resources
- [AccelerationConsortium xarm-translocation](https://github.com/AccelerationConsortium/xarm-translocation) - Advanced control package
- [xArm ROS Integration](https://github.com/xArm-Developer/xarm_ros) - For ROS users
- [xArm ROS2 Integration](https://github.com/xArm-Developer/xarm_ros2) - For ROS2 users

### AC Training Lab Resources
- [AC Training Lab Documentation](https://ac-training-lab.readthedocs.io/)
- [AC Training Lab GitHub](https://github.com/AccelerationConsortium/ac-training-lab)
- [Discussions](https://github.com/AccelerationConsortium/ac-training-lab/discussions)

## Contributing

To contribute improvements or report issues:
1. Open an issue on the [AC Training Lab GitHub](https://github.com/AccelerationConsortium/ac-training-lab/issues)
2. Join the discussion at [AC Discussions](https://github.com/AccelerationConsortium/ac-training-lab/discussions)
3. Submit a pull request with your changes

## License

This module is part of the ac-training-lab project and follows the same MIT License.

## Support

For support with:
- **Hardware issues**: Contact UFACTORY support
- **Software/integration issues**: Open an issue on GitHub
- **General questions**: Join our discussions or reach out to sterling.baird@utoronto.ca
