# MicroPython Device + Remote Orchestrator Example

This example demonstrates the exact architecture requested: **device.py** runs on laboratory hardware, **orchestrator.py** runs remotely for control.

## 🎯 Architecture

```
┌─────────────────────────┐    MQTT     ┌────────────────────────┐
│      device.py          │ <────────> │    orchestrator.py     │
│                         │             │                        │
│ • Runs on lab hardware  │             │ • Runs remotely        │
│ • Pico W, ESP32, OT-2   │             │ • Laptop, cloud, etc.  │
│ • Exposes lab functions │             │ • Controls lab devices │
│ • MQTT client           │             │ • Experiment management│
└─────────────────────────┘             └────────────────────────┘
```

## 📁 Files

- **`device.py`** - Runs ON the laboratory device (Pico W, ESP32, etc.)
- **`orchestrator.py`** - Runs REMOTELY (laptop, cloud, server)  
- **`README.md`** - This documentation

## 🚀 Quick Start

### 1. Setup Device (Laboratory Hardware)

**Upload to MicroPython device:**
```python
# Configure these values in device.py
DEVICE_ID = "lab-device-001"      # Unique device name
WIFI_SSID = "your-wifi-ssid"      # Your WiFi network
WIFI_PASSWORD = \"<REDACTED>\"   # Your WiFi password
MQTT_BROKER = "broker.hivemq.com" # MQTT broker (or your own)
```

**Upload device.py to your hardware:**
```bash
# Using ampy (install with: pip install adafruit-ampy)
ampy -p /dev/ttyUSB0 put device.py main.py

# Or using Thonny IDE, mpremote, etc.
```

### 2. Run Orchestrator (Remote Computer)

**On your laptop/server:**
```bash
# Install dependencies
pip install paho-mqtt

# Configure MQTT broker in orchestrator.py to match device
# Then run:
python orchestrator.py
```

## 🔧 Available Device Functions

The **device.py** exposes these laboratory functions via MQTT:

### Basic I/O
- `read_analog_sensor(pin)` - Read analog sensor value
- `control_led(pin, state)` - Control LED on/off  
- `move_servo(pin, angle)` - Move servo motor (0-180°)

### Multi-sensor Operations
- `read_multiple_sensors(pins)` - Read multiple sensors at once
- `run_device_calibration(led_pin, sensor_pins)` - Full calibration sequence

### Status & Diagnostics
- `get_device_status()` - Complete device information

## 🎮 Orchestrator Capabilities

The **orchestrator.py** provides high-level control:

### Device Connection
```python
# Connect to specific device
with orchestrator.connect_to_device("lab-device-001") as device:
    status = device.get_status()
    sensor_data = device.read_sensor(pin=26)
```

### Experiment Management
```python
# Run automated experiments
experiment_manager = ExperimentManager(orchestrator)

# Multi-device calibration
results = experiment_manager.run_sensor_calibration_experiment(
    device_ids=["device-001", "device-002"], 
    sensor_pins=[26, 27, 28]
)

# Continuous monitoring
monitoring = experiment_manager.run_sensor_monitoring_experiment(
    device_id="device-001",
    duration_minutes=30,
    sample_interval_seconds=60
)
```

## 📊 Example Usage

### Simple Sensor Reading
```python
# On orchestrator.py side:
with orchestrator.connect_to_device("lab-device-001") as device:
    
    # Turn on LED  
    device.control_led(pin=25, state=True)
    
    # Read sensor
    data = device.read_sensor(pin=26)
    print(f"Sensor voltage: {data['voltage']:.3f}V")
    
    # Move servo
    device.move_servo(pin=15, angle=90)
    
    # Turn off LED
    device.control_led(pin=25, state=False)
```

### Automated Experiment
```python
# Multi-step experiment with error handling
try:
    # Calibrate device first
    calibration = device.calibrate_device(
        led_pin=25, 
        sensor_pins=[26, 27, 28]
    )
    
    if calibration["calibration_quality"] == "good":
        # Run main experiment
        results = device.read_multiple_sensors([26, 27, 28])
        print(f"Average: {results['average_voltage']:.3f}V")
    else:
        print("Calibration failed - skipping experiment")
        
except Exception as e:
    print(f"Experiment failed: {e}")
```

## 🔌 Hardware Connections

For **Raspberry Pi Pico W** example:

```
Pin 25: LED (status indicator)
Pin 26: Analog sensor 1  
Pin 27: Analog sensor 2
Pin 28: Analog sensor 3
Pin 15: Servo motor (PWM)
```

For **ESP32** adjust pin numbers accordingly.

## 🌐 Network Setup

### Option 1: Public MQTT Broker
```python
# Use free public broker (good for testing)
MQTT_BROKER = "broker.hivemq.com"
```

### Option 2: Local MQTT Broker  
```bash
# Install Mosquitto locally
sudo apt-get install mosquitto mosquitto-clients

# Start broker
sudo systemctl start mosquitto

# Use in code
MQTT_BROKER = "localhost"
```

### Option 3: Cloud MQTT Broker
```python
# Use HiveMQ Cloud, AWS IoT, etc.
MQTT_BROKER = "your-hivemq-instance.s2.eu.hivemq.cloud"
MQTT_PORT = 8883  # For TLS
```

## 🔍 Debugging

### Check Device Status
```bash
# Subscribe to device status
mosquitto_sub -h broker.hivemq.com -t "lab/+/status"

# Send test command
mosquitto_pub -h broker.hivemq.com -t "lab/lab-device-001/command" \
  -m '{"request_id":"test123","task":"get_device_status","parameters":{}}'
```

### Device Logs
```python
# Device.py prints status to console:
# 📝 Registered device task: read_analog_sensor
# 📡 Connected to MQTT broker: broker.hivemq.com  
# 🚀 Device lab-device-001 online and ready!
# 📥 Received: {'task': 'read_sensor', ...}
# ✅ Task 'read_sensor' completed
```

### Orchestrator Logs  
```python
# Orchestrator.py shows:
# 🔗 Connected to device: lab-device-001
# 🔄 [SIMULATED] Executing 'read_sensor' on lab-device-001
# 📋 Disconnected from device: lab-device-001
```

## 🚀 Extending Functionality

### Add New Device Functions
```python
# In device.py, add:
@device_task()
def read_temperature_humidity() -> dict:
    """Read DHT22 sensor."""
    # Your sensor code here
    return {"temp": 25.5, "humidity": 60.2}
```

### Add New Orchestrator Methods
```python
# In orchestrator.py DeviceConnection class:
def read_environment(self) -> Dict[str, Any]:
    """Read environmental sensors."""
    return self.execute_task("read_temperature_humidity")
```

## 🔒 Security Considerations

### Production Deployment
- Use TLS-encrypted MQTT (port 8883)
- Implement device authentication
- Use VPN for network security
- Regular security updates

### Authentication Example
```python
# Add to device.py for secure deployment
MQTT_USERNAME = "device_user"  
MQTT_PASSWORD = \"<REDACTED>\"

# Configure in mqtt_as config
config['user'] = MQTT_USERNAME
config['password'] = MQTT_PASSWORD
```

This example provides the exact architecture you requested: device code running on laboratory hardware and orchestrator code running remotely, with clear separation of concerns and real MQTT communication.