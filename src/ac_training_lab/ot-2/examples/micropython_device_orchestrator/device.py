"""
device.py - Runs on the laboratory device (Pico W, ESP32, OT-2, etc.)

This script runs directly on the physical laboratory hardware and exposes 
laboratory functions via MQTT for remote orchestration.

Compatible with:
- Raspberry Pi Pico W
- ESP32/ESP8266
- OT-2 Robot (when using MicroPython)
- Any device with MQTT support

Usage:
1. Upload this file to your MicroPython device
2. Configure WIFI_SSID, WIFI_PASSWORD, and MQTT_BROKER
3. Run: python device.py
4. Device will connect and wait for orchestrator commands
"""

import json
import time
import gc
import asyncio

# MicroPython imports
try:
    # MicroPython-specific imports
    from mqtt_as import MQTTClient, config
    import network
    from machine import Pin, ADC, PWM, unique_id
    import ubinascii
    MICROPYTHON = True
except ImportError:
    # CPython fallback for testing
    import paho.mqtt.client as mqtt
    MICROPYTHON = False
    print("Running in CPython mode (for testing)")

# Device Configuration
DEVICE_ID = "lab-device-001"  # Change this for each device
WIFI_SSID = "your-wifi-ssid"
WIFI_PASSWORD = "your-wifi-password"
MQTT_BROKER = "broker.hivemq.com"  # or your MQTT broker
MQTT_PORT = 1883

# Task registry for device functions
device_tasks = {}

def device_task(name=None):
    """
    Decorator to register device functions for remote execution.
    
    Usage:
        @device_task()
        def my_function(param1: int, param2: str) -> dict:
            # Your lab device code here
            return {"result": "success"}
    """
    def decorator(func):
        task_name = name or func.__name__
        device_tasks[task_name] = {
            'function': func,
            'name': task_name,
            'doc': func.__doc__ or ""
        }
        print(f"📝 Registered device task: {task_name}")
        return func
    return decorator

# ============================================================================
# LABORATORY DEVICE FUNCTIONS
# ============================================================================

@device_task()
def read_analog_sensor(pin: int) -> dict:
    """
    Read analog sensor value from specified pin.
    
    Args:
        pin: GPIO pin number (e.g., 26, 27, 28)
        
    Returns:
        Sensor reading with voltage and raw value
    """
    if MICROPYTHON:
        adc = ADC(pin)
        raw_value = adc.read_u16()
        voltage = (raw_value / 65535) * 3.3
    else:
        # Simulate for CPython testing
        raw_value = 32767
        voltage = 1.65
    
    return {
        "pin": pin,
        "raw_value": raw_value,
        "voltage": voltage,
        "timestamp": time.time(),
        "device_id": DEVICE_ID
    }

@device_task()
def control_led(pin: int, state: bool) -> str:
    """
    Control LED on/off.
    
    Args:
        pin: GPIO pin number
        state: True for ON, False for OFF
        
    Returns:
        Status message
    """
    if MICROPYTHON:
        led = Pin(pin, Pin.OUT)
        led.value(1 if state else 0)
    else:
        # Simulate for CPython
        pass
    
    return f"💡 LED on pin {pin} {'ON' if state else 'OFF'}"

@device_task()
def move_servo(pin: int, angle: int) -> str:
    """
    Move servo motor to specified angle.
    
    Args:
        pin: PWM-capable GPIO pin
        angle: Servo angle (0-180 degrees)
        
    Returns:
        Movement confirmation
    """
    if not (0 <= angle <= 180):
        raise ValueError("Angle must be between 0 and 180 degrees")
    
    if MICROPYTHON:
        servo = PWM(Pin(pin))
        servo.freq(50)  # 50Hz for servo
        
        # Convert angle to duty cycle (1ms-2ms pulse width)
        duty = int(((angle / 180) * 1000) + 1000)  # 1000-2000 microsecond range
        servo.duty_u16(duty * 65535 // 20000)  # Convert to 16-bit duty
        
        time.sleep(0.5)  # Allow servo to move
        servo.deinit()
    else:
        # Simulate for CPython
        time.sleep(0.5)
    
    return f"🔄 Servo on pin {pin} moved to {angle}°"

@device_task()
def read_multiple_sensors(pins: list) -> dict:
    """
    Read multiple analog sensors at once.
    
    Args:
        pins: List of GPIO pins to read
        
    Returns:
        Dictionary with readings from all sensors
    """
    readings = {}
    
    for pin in pins:
        sensor_data = read_analog_sensor(pin)
        readings[f"sensor_{pin}"] = sensor_data
    
    return {
        "sensors_read": len(pins),
        "readings": readings,
        "average_voltage": sum(r["voltage"] for r in readings.values()) / len(readings),
        "timestamp": time.time()
    }

@device_task()
def run_device_calibration(led_pin: int, sensor_pins: list) -> dict:
    """
    Run device calibration sequence.
    
    Args:
        led_pin: LED pin for status indication
        sensor_pins: List of sensor pins to calibrate
        
    Returns:
        Calibration results
    """
    print("🔧 Starting device calibration...")
    
    # Turn on LED to indicate calibration
    control_led(led_pin, True)
    
    # Read baseline sensor values
    baseline_readings = read_multiple_sensors(sensor_pins)
    
    # Wait for stabilization
    time.sleep(2)
    
    # Read final values
    final_readings = read_multiple_sensors(sensor_pins)
    
    # Calculate drift
    drift_values = {}
    for pin in sensor_pins:
        baseline = baseline_readings["readings"][f"sensor_{pin}"]["voltage"]
        final = final_readings["readings"][f"sensor_{pin}"]["voltage"]
        drift_values[f"sensor_{pin}"] = abs(final - baseline)
    
    # Turn off LED
    control_led(led_pin, False)
    
    return {
        "calibration_status": "completed",
        "sensors_calibrated": len(sensor_pins),
        "baseline_readings": baseline_readings,
        "final_readings": final_readings,
        "drift_values": drift_values,
        "max_drift": max(drift_values.values()),
        "calibration_quality": "good" if max(drift_values.values()) < 0.1 else "needs_attention"
    }

@device_task()
def get_device_status() -> dict:
    """
    Get comprehensive device status and information.
    
    Returns:
        Device status dictionary
    """
    status = {
        "device_id": DEVICE_ID,
        "platform": "micropython" if MICROPYTHON else "cpython",
        "tasks_available": list(device_tasks.keys()),
        "uptime_ms": time.ticks_ms() if MICROPYTHON else int(time.time() * 1000),
        "timestamp": time.time()
    }
    
    if MICROPYTHON:
        # Add MicroPython-specific info
        status.update({
            "free_memory": gc.mem_free(),
            "allocated_memory": gc.mem_alloc(),
            "unique_id": ubinascii.hexlify(unique_id()).decode()
        })
        
        # Check WiFi status
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            status["wifi"] = {
                "connected": True,
                "ip": wlan.ifconfig()[0],
                "rssi": wlan.status('rssi') if hasattr(wlan, 'status') else None
            }
        else:
            status["wifi"] = {"connected": False}
    
    return status

# ============================================================================
# MQTT DEVICE HANDLER
# ============================================================================

class MQTTDeviceHandler:
    """Handles MQTT communication for the laboratory device."""
    
    def __init__(self, device_id: str, broker_host: str, broker_port: int = 1883):
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        # MQTT topics
        self.command_topic = f"lab/{device_id}/command"
        self.result_topic = f"lab/{device_id}/result"
        self.status_topic = f"lab/{device_id}/status"
        
        if MICROPYTHON:
            self._setup_micropython_mqtt()
        else:
            self._setup_cpython_mqtt()
    
    def _setup_micropython_mqtt(self):
        """Setup MQTT for MicroPython using mqtt_as."""
        config['server'] = self.broker_host
        config['port'] = self.broker_port
        config['client_id'] = self.device_id
        config['topic'] = self.result_topic
        config['will'] = self.status_topic, '{"status": "offline"}', True, 0
        
        self.client = MQTTClient(config)
    
    def _setup_cpython_mqtt(self):
        """Setup MQTT for CPython using paho-mqtt (testing)."""
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect_cpython
        self.client.on_message = self._on_message_cpython
    
    def _on_connect_cpython(self, client, userdata, flags, rc):
        """CPython MQTT connect callback."""
        if rc == 0:
            print(f"📡 Connected to MQTT broker: {self.broker_host}")
            client.subscribe(self.command_topic)
            client.publish(self.status_topic, '{"status": "online"}')
    
    def _on_message_cpython(self, client, userdata, msg):
        """CPython MQTT message callback."""
        try:
            payload = json.loads(msg.payload.decode())
            print(f"📥 Received command: {payload}")
            # Process command (simplified for testing)
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    async def connect_and_run(self):
        """Connect to MQTT and start device loop."""
        if MICROPYTHON:
            await self._run_micropython()
        else:
            await self._run_cpython()
    
    async def _run_micropython(self):
        """Run MicroPython MQTT device loop."""
        # Connect to WiFi first
        await self._connect_wifi()
        
        # Setup MQTT callbacks
        self.client.set_callback(self._on_message_micropython)
        
        # Connect to MQTT broker
        await self.client.connect()
        
        # Subscribe to command topic
        await self.client.subscribe(self.command_topic, 1)
        print(f"📥 Subscribed to: {self.command_topic}")
        
        # Publish online status
        await self.client.publish(self.status_topic, '{"status": "online"}', qos=1)
        
        print(f"🚀 Device {self.device_id} online and ready!")
        print(f"📋 Available tasks: {list(device_tasks.keys())}")
        
        # Main device loop
        while True:
            await asyncio.sleep(1)
            # Perform any periodic tasks here
    
    async def _run_cpython(self):
        """Run CPython MQTT device loop (for testing)."""
        self.client.connect(self.broker_host, self.broker_port, 60)
        self.client.loop_start()
        
        print(f"🚀 Test device {self.device_id} running in CPython mode!")
        print(f"📋 Available tasks: {list(device_tasks.keys())}")
        
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            self.client.loop_stop()
            self.client.disconnect()
    
    async def _connect_wifi(self):
        """Connect to WiFi (MicroPython only)."""
        wlan = network.WLAN(network.STA_IF)
        wlan.active(True)
        
        if not wlan.isconnected():
            print(f"📶 Connecting to WiFi: {WIFI_SSID}")
            wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            
            # Wait for connection
            timeout = 10
            while not wlan.isconnected() and timeout > 0:
                await asyncio.sleep(1)
                timeout -= 1
            
            if wlan.isconnected():
                print(f"✅ WiFi connected: {wlan.ifconfig()[0]}")
            else:
                raise Exception("❌ Failed to connect to WiFi")
    
    def _on_message_micropython(self, topic, msg, retained):
        """Handle incoming MQTT messages (MicroPython)."""
        try:
            payload = json.loads(msg.decode())
            print(f"📥 Received: {payload}")
            
            # Execute task asynchronously
            asyncio.create_task(self._execute_task(payload))
            
        except Exception as e:
            print(f"❌ Message error: {e}")
    
    async def _execute_task(self, payload: dict):
        """Execute a device task and publish result."""
        try:
            request_id = payload.get('request_id', 'unknown')
            task_name = payload.get('task')
            parameters = payload.get('parameters', {})
            
            if task_name not in device_tasks:
                raise ValueError(f"Task '{task_name}' not found")
            
            print(f"🔄 Executing: {task_name}")
            
            # Execute the task function
            func = device_tasks[task_name]['function']
            result = func(**parameters)
            
            # Publish success result
            result_payload = {
                'request_id': request_id,
                'task': task_name,
                'status': 'success',
                'result': result,
                'timestamp': time.time(),
                'device_id': self.device_id
            }
            
            await self.client.publish(
                self.result_topic, 
                json.dumps(result_payload), 
                qos=1
            )
            
            print(f"✅ Task '{task_name}' completed")
            
        except Exception as e:
            # Publish error result
            error_payload = {
                'request_id': payload.get('request_id', 'unknown'),
                'task': payload.get('task', 'unknown'),
                'status': 'error',
                'error': str(e),
                'timestamp': time.time(),
                'device_id': self.device_id
            }
            
            await self.client.publish(
                self.result_topic, 
                json.dumps(error_payload), 
                qos=1
            )
            
            print(f"❌ Task failed: {e}")

# ============================================================================
# MAIN DEVICE EXECUTION
# ============================================================================

async def main():
    """Main function - runs the laboratory device."""
    print("=" * 60)
    print("🔬 Laboratory Device Starting...")
    print("=" * 60)
    print(f"🏷️  Device ID: {DEVICE_ID}")
    print(f"📡 MQTT Broker: {MQTT_BROKER}")
    print(f"🐍 Platform: {'MicroPython' if MICROPYTHON else 'CPython (test mode)'}")
    print(f"📋 Tasks Available: {len(device_tasks)}")
    
    for task_name, task_info in device_tasks.items():
        print(f"   • {task_name}: {task_info['doc']}")
    
    print("=" * 60)
    
    # Create and run device handler
    device = MQTTDeviceHandler(DEVICE_ID, MQTT_BROKER, MQTT_PORT)
    
    try:
        await device.connect_and_run()
    except Exception as e:
        print(f"❌ Device error: {e}")
        if MICROPYTHON:
            import machine
            print("🔄 Restarting device in 5 seconds...")
            time.sleep(5)
            machine.reset()

# Run the device
if __name__ == "__main__":
    asyncio.run(main())