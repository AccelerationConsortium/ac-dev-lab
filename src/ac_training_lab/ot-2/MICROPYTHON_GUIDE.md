# MicroPython Integration Guide

This guide shows how to use the OT-2 orchestration framework with MicroPython devices (Pico W, ESP32, etc.) for microcontroller-based laboratory automation.

## 🔄 FastAPI vs MQTT Comparison

| Feature | FastAPI | MQTT |
|---------|---------|------|
| **Self-Documentation** | ✅ Auto-generated OpenAPI docs | ❌ Manual documentation |
| **MicroPython Support** | 🔶 Limited (requires urequests) | ✅ Native (mqtt_as.py) |
| **Network Overhead** | Higher (HTTP headers) | Lower (binary protocol) |
| **Debugging** | ✅ Easy (web browser, curl) | 🔶 Requires MQTT client |
| **Firewall Friendly** | ✅ Standard HTTP/HTTPS ports | 🔶 Custom ports (1883/8883) |
| **Real-time** | ❌ Request-response only | ✅ Pub/sub, real-time |
| **Memory Usage** | Higher | Lower |
| **Battery/Power** | Higher consumption | Lower consumption |

**For MicroPython devices**: **MQTT is recommended** due to better memory efficiency and native async support.

## 🎯 Architecture: Device + Orchestrator

```
┌─────────────────┐    MQTT/HTTP    ┌──────────────────┐
│   Device.py     │ <────────────> │  Orchestrator.py │
│                 │                 │                  │
│ • Pico W        │                 │ • Laptop/Server  │
│ • ESP32         │                 │ • Cloud (Railway)│
│ • OT-2 Robot    │                 │ • Local Machine  │
│ • Sensors       │                 │ • Jupyter Notebook│
└─────────────────┘                 └──────────────────┘
```

## 🔧 MicroPython MQTT Implementation

### Device Side (MicroPython - device.py)

```python
# device.py - Runs on Pico W, ESP32, etc.
import json
import time
import asyncio
from mqtt_as import MQTTClient, config
import machine

# Device configuration
DEVICE_ID = "pico-w-lab-001"
MQTT_BROKER = "broker.hivemq.com"  # or your broker
MQTT_PORT = 1883

# Task registry for MicroPython
micropython_tasks = {}

def micropython_task(name=None):
    """Decorator to register MicroPython tasks."""
    def decorator(func):
        task_name = name or func.__name__
        micropython_tasks[task_name] = {
            'function': func,
            'name': task_name,
            'doc': func.__doc__ or ""
        }
        print(f"Registered MicroPython task: {task_name}")
        return func
    return decorator

# Example MicroPython tasks
@micropython_task()
def read_sensor(sensor_pin: int) -> dict:
    """Read analog sensor value."""
    from machine import ADC
    adc = ADC(sensor_pin)
    value = adc.read_u16()
    voltage = (value / 65535) * 3.3
    return {
        "sensor_pin": sensor_pin,
        "raw_value": value,
        "voltage": voltage,
        "timestamp": time.time()
    }

@micropython_task()
def control_led(pin: int, state: bool) -> str:
    """Control LED on/off."""
    from machine import Pin
    led = Pin(pin, Pin.OUT)
    led.value(1 if state else 0)
    return f"LED on pin {pin} {'ON' if state else 'OFF'}"

@micropython_task()
def move_servo(pin: int, angle: int) -> str:
    """Move servo to specified angle."""
    from machine import Pin, PWM
    servo = PWM(Pin(pin))
    servo.freq(50)
    
    # Convert angle (0-180) to duty cycle
    duty = int(((angle / 180) * 2000) + 1000)  # 1000-3000 range
    servo.duty_u16(duty * 65535 // 20000)
    
    time.sleep(0.5)  # Allow servo to move
    servo.deinit()
    
    return f"Servo on pin {pin} moved to {angle} degrees"

@micropython_task()
def get_device_status() -> dict:
    """Get MicroPython device status."""
    import gc
    return {
        "device_id": DEVICE_ID,
        "free_memory": gc.mem_free(),
        "platform": "micropython",
        "tasks_available": list(micropython_tasks.keys()),
        "uptime_ms": time.ticks_ms()
    }

class MicroPythonMQTTDevice:
    """MQTT device handler for MicroPython."""
    
    def __init__(self, device_id, broker_host, broker_port=1883):
        self.device_id = device_id
        
        # Configure mqtt_as
        config['server'] = broker_host
        config['port'] = broker_port
        config['client_id'] = device_id
        config['topic'] = f'ot2/{device_id}/result'
        config['will'] = f'ot2/{device_id}/status', '{"status": "offline"}', True, 0
        
        # MQTT topics
        self.command_topic = f"ot2/{device_id}/command"
        self.result_topic = f"ot2/{device_id}/result"
        
        self.client = MQTTClient(config)
        
    async def connect(self):
        """Connect to MQTT broker."""
        await self.client.connect()
        
        # Subscribe to commands
        await self.client.subscribe(self.command_topic, 1)
        print(f"Subscribed to {self.command_topic}")
        
        # Publish online status
        await self.client.publish(
            f"ot2/{self.device_id}/status", 
            '{"status": "online"}', 
            qos=1
        )
        
    async def message_handler(self, topic, msg, retained):
        """Handle incoming MQTT messages."""
        try:
            payload = json.loads(msg.decode())
            print(f"Received: {payload}")
            
            # Execute the requested task
            await self.execute_task(payload)
            
        except Exception as e:
            print(f"Message handling error: {e}")
    
    async def execute_task(self, payload):
        """Execute a task and publish result."""
        try:
            request_id = payload.get('request_id', 'unknown')
            task_name = payload.get('task')
            parameters = payload.get('parameters', {})
            
            if task_name not in micropython_tasks:
                raise ValueError(f"Task '{task_name}' not found")
            
            # Execute the task
            func = micropython_tasks[task_name]['function']
            
            # Convert parameters to match function signature
            result = func(**parameters)
            
            # Publish successful result
            result_payload = {
                'request_id': request_id,
                'task': task_name,
                'status': 'success',
                'result': result,
                'timestamp': time.time()
            }
            
            await self.client.publish(
                self.result_topic, 
                json.dumps(result_payload), 
                qos=1
            )
            
            print(f"Task '{task_name}' completed successfully")
            
        except Exception as e:
            # Publish error result
            error_payload = {
                'request_id': payload.get('request_id', 'unknown'),
                'task': payload.get('task', 'unknown'),
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
            
            await self.client.publish(
                self.result_topic, 
                json.dumps(error_payload), 
                qos=1
            )
            
            print(f"Task execution failed: {e}")
    
    async def run(self):
        """Main device loop."""
        self.client.set_callback(self.message_handler)
        await self.connect()
        
        print(f"MicroPython device {self.device_id} running...")
        print(f"Available tasks: {list(micropython_tasks.keys())}")
        
        while True:
            await asyncio.sleep(1)

async def main():
    """Main function for MicroPython device."""
    device = MicroPythonMQTTDevice(DEVICE_ID, MQTT_BROKER, MQTT_PORT)
    await device.run()

# Run the device
if __name__ == "__main__":
    asyncio.run(main())
```

### Orchestrator Side (CPython - orchestrator.py)

```python
# orchestrator.py - Runs on laptop/server/cloud
import time
from typing import Dict, Any
from src.ac_training_lab.ot_2.orchestration.mqtt_wrapper import MQTTOrchestratorClient

class MicroPythonOrchestrator:
    """
    Orchestrator for MicroPython devices.
    
    This can run on your laptop, server, or cloud (Railway/AWS).
    """
    
    def __init__(self, broker_host: str, device_id: str):
        self.device_id = device_id
        self.client = MQTTOrchestratorClient(
            broker_host=broker_host,
            device_id=device_id,
            broker_port=1883,
            timeout=10.0
        )
    
    def __enter__(self):
        self.client.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()
    
    def read_sensor_data(self, sensor_pin: int) -> Dict[str, Any]:
        """Read sensor data from MicroPython device."""
        return self.client.execute_task("read_sensor", sensor_pin=sensor_pin)
    
    def control_device_led(self, pin: int, state: bool) -> str:
        """Control LED on MicroPython device."""
        return self.client.execute_task("control_led", pin=pin, state=state)
    
    def move_device_servo(self, pin: int, angle: int) -> str:
        """Move servo on MicroPython device."""
        return self.client.execute_task("move_servo", pin=pin, angle=angle)
    
    def get_device_info(self) -> Dict[str, Any]:
        """Get MicroPython device status."""
        return self.client.execute_task("get_device_status")
    
    def run_sensor_experiment(self, sensors: list, led_pin: int) -> Dict[str, Any]:
        """Run a complete sensor experiment."""
        print("🧪 Starting MicroPython sensor experiment...")
        
        # Turn on indicator LED
        self.control_device_led(led_pin, True)
        
        results = []
        
        for sensor_pin in sensors:
            print(f"📊 Reading sensor on pin {sensor_pin}...")
            
            # Read sensor
            sensor_data = self.read_sensor_data(sensor_pin)
            results.append(sensor_data)
            
            print(f"   Value: {sensor_data['voltage']:.2f}V")
            
            # Brief delay between readings
            time.sleep(0.5)
        
        # Turn off indicator LED
        self.control_device_led(led_pin, False)
        
        return {
            "experiment": "sensor_reading",
            "sensors_tested": len(sensors),
            "results": results,
            "average_voltage": sum(r['voltage'] for r in results) / len(results),
            "device_id": self.device_id
        }

def main():
    """Example orchestrator usage."""
    BROKER = "broker.hivemq.com"  # Use your MQTT broker
    DEVICE_ID = "pico-w-lab-001"
    
    print("="*60)
    print("🎯 MicroPython Device Orchestrator")
    print("="*60)
    print(f"📡 Broker: {BROKER}")
    print(f"🤖 Device: {DEVICE_ID}")
    print("="*60)
    
    try:
        with MicroPythonOrchestrator(BROKER, DEVICE_ID) as orchestrator:
            
            # Check device status
            status = orchestrator.get_device_info()
            print(f"📊 Device Status: {status['platform']} with {status['free_memory']} bytes free")
            print(f"🔧 Available Tasks: {status['tasks_available']}")
            
            # Run sensor experiment
            experiment_results = orchestrator.run_sensor_experiment(
                sensors=[26, 27, 28],  # GPIO pins for sensors
                led_pin=25  # GPIO pin for LED
            )
            
            print(f"\n✅ Experiment completed:")
            print(f"   Sensors tested: {experiment_results['sensors_tested']}")
            print(f"   Average voltage: {experiment_results['average_voltage']:.2f}V")
            
            # Control servo
            print(f"\n🔄 Moving servo...")
            servo_result = orchestrator.move_device_servo(pin=15, angle=90)
            print(f"   {servo_result}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    main()
```

## 🚀 Hybrid Approach: FastAPI + MicroPython

For the best of both worlds, use **FastAPI for main orchestration** and **MQTT for MicroPython devices**:

```python
# hybrid_orchestrator.py - FastAPI server that also controls MicroPython devices
from fastapi import FastAPI
from src.ac_training_lab.ot_2.orchestration import task
from src.ac_training_lab.ot_2.orchestration.mqtt_wrapper import MQTTOrchestratorClient

app = FastAPI(title="Hybrid Lab Orchestrator")

# MQTT client for MicroPython devices
micropython_client = MQTTOrchestratorClient("broker.hivemq.com", "pico-w-lab-001")
micropython_client.connect()

@task()
def read_micropython_sensor(sensor_pin: int) -> dict:
    """Read sensor from MicroPython device via MQTT."""
    return micropython_client.execute_task("read_sensor", sensor_pin=sensor_pin)

@task()
def run_hybrid_experiment(ot2_colors: list, micropython_sensors: list) -> dict:
    """
    Run experiment using both OT-2 (FastAPI) and MicroPython (MQTT).
    """
    results = {
        "ot2_results": [],
        "micropython_results": []
    }
    
    # Use OT-2 for liquid handling (FastAPI tasks)
    for color in ot2_colors:
        # This would call other FastAPI tasks
        mix_result = f"Mixed color {color} on OT-2"
        results["ot2_results"].append(mix_result)
    
    # Use MicroPython for sensor readings (MQTT)
    for sensor_pin in micropython_sensors:
        sensor_data = micropython_client.execute_task("read_sensor", sensor_pin=sensor_pin)
        results["micropython_results"].append(sensor_data)
    
    return results
```

## 💡 Key Benefits for MicroPython

### 1. **Memory Efficiency**
- MQTT uses less RAM than HTTP
- `mqtt_as.py` is optimized for microcontrollers
- Binary protocol vs text-heavy HTTP

### 2. **Async Native Support**
- MicroPython has excellent `uasyncio` support
- `mqtt_as.py` is built for async operation
- No blocking operations

### 3. **Power Efficiency**
- MQTT persistent connections use less power
- No HTTP connection overhead
- Better for battery-powered devices

### 4. **Real-time Communication**
- Pub/sub allows instant notifications
- No polling required
- Event-driven architecture

## 🔗 Integration Examples

### Example 1: Pico W Sensor Network
```python
# Each Pico W runs device.py with different tasks
# Orchestrator collects data from all devices
sensors = ["pico-w-001", "pico-w-002", "pico-w-003"]

for device_id in sensors:
    with MicroPythonOrchestrator("broker.hivemq.com", device_id) as orch:
        data = orch.read_sensor_data(26)
        print(f"Device {device_id}: {data}")
```

### Example 2: OT-2 + Environmental Monitoring
```python
# OT-2 does liquid handling (FastAPI)
# Pico W monitors temperature/humidity (MQTT)
# Orchestrator coordinates both

# Mix samples on OT-2
ot2_client.execute_task("mix_colors", r=255, g=128, b=64)

# Monitor environment with Pico W  
env_data = micropython_client.execute_task("read_environmental_sensors")

# Make decisions based on both
if env_data["temperature"] > 25:
    ot2_client.execute_task("adjust_cooling")
```

## 📋 Recommendation Summary

**For your use case:**

1. **OT-2 Robot**: Use **FastAPI** (better documentation, easier debugging)
2. **MicroPython devices**: Use **MQTT** (memory efficient, async native)
3. **Orchestrator**: Can use both simultaneously

This gives you the best of both worlds - the self-documentation benefits of FastAPI where you need them, and the efficiency of MQTT for resource-constrained devices.