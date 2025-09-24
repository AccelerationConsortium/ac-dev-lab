# OT-2 Orchestration Solutions

This directory contains two lightweight orchestration solutions for OT-2 devices that avoid pydantic version conflicts with the Opentrons package.

## Problem Statement

The Prefect orchestration framework uses pydantic v2, while the Opentrons package requires pydantic v1, causing version incompatibilities when trying to run both in the same Python environment. This prevents using Prefect for OT-2 orchestration workflows.

## Solutions Provided

### 1. FastAPI-based Orchestration (`orchestration/`)

A lightweight HTTP-based solution using FastAPI that provides:

- **Decorator-based task registration** (`@task`) similar to Prefect's `@flow`
- **HTTP REST API** for remote task execution
- **Auto-generated documentation** via FastAPI's built-in docs
- **Type validation** and error handling
- **Easy client-server synchronization**

**Pros:**
- Self-documenting API (Swagger/OpenAPI)
- Familiar HTTP-based interface
- Built-in web UI for testing
- Type hints and validation
- Easy debugging and monitoring

**Cons:**
- Requires HTTP network connectivity
- Slightly more overhead than MQTT

### 2. MQTT-based Orchestration (`orchestration/mqtt_wrapper.py`)

A lightweight MQTT solution that provides:

- **Decorator-based task registration** (`@mqtt_task`)
- **MQTT messaging** for reliable communication
- **Request-response pattern** with correlation IDs
- **Automatic reconnection** and error handling
- **Minimal network requirements**

**Pros:**
- Lower network overhead
- Built-in message persistence and delivery guarantees
- Works well in IoT environments
- Can handle intermittent connectivity
- Pub/sub pattern allows multiple listeners

**Cons:**
- Requires MQTT broker setup
- Less intuitive than HTTP for debugging
- No built-in web interface

## Quick Start

### FastAPI Solution

**1. Start the device server:**
```python
from ac_training_lab.ot_2.orchestration import DeviceServer, task

@task
def mix_colors(r: int, g: int, b: int, well: str) -> str:
    # Your OT-2 code here
    return f"Mixed RGB({r},{g},{b}) in {well}"

server = DeviceServer()
server.run()  # Starts on http://localhost:8000
```

**2. Control remotely:**
```python
from ac_training_lab.ot_2.orchestration import OrchestratorClient

with OrchestratorClient("http://ot2-device:8000") as client:
    result = client.execute_task("mix_colors", r=255, g=128, b=64, well="A1")
    print(result)
```

### MQTT Solution

**1. Start the device server:**
```python
from ac_training_lab.ot_2.orchestration.mqtt_wrapper import MQTTDeviceServer, mqtt_task

@mqtt_task
def mix_colors(r: int, g: int, b: int, well: str) -> str:
    # Your OT-2 code here
    return f"Mixed RGB({r},{g},{b}) in {well}"

server = MQTTDeviceServer("mqtt-broker.local", device_id="ot2-001")
server.start()
```

**2. Control remotely:**
```python
from ac_training_lab.ot_2.orchestration.mqtt_wrapper import MQTTOrchestratorClient

with MQTTOrchestratorClient("mqtt-broker.local", "ot2-001") as client:
    result = client.execute_task("mix_colors", {"r": 255, "g": 128, "b": 64, "well": "A1"})
    print(result)
```

## Complete Examples

See the `examples/` directory for complete working examples:

### FastAPI Examples
- `device_example.py` - Complete OT-2 device server with color mixing tasks
- `orchestrator_example.py` - Orchestrator client with experiment workflows

### MQTT Examples  
- `mqtt_device_example.py` - MQTT-based OT-2 device server
- `mqtt_orchestrator_example.py` - MQTT orchestrator client

## Dependencies

### FastAPI Solution
```bash
pip install fastapi uvicorn httpx
```

### MQTT Solution  
```bash
pip install paho-mqtt
```

### OT-2 Integration
```bash
pip install opentrons  # Works with pydantic v1
```

## Running the Examples

### FastAPI Example

**Terminal 1 (Device Server):**
```bash
cd src/ac_training_lab/ot-2/examples
python device_example.py
```

**Terminal 2 (Orchestrator):**
```bash
cd src/ac_training_lab/ot-2/examples  
python orchestrator_example.py
```

**Web Interface:**
Visit http://localhost:8000/docs for interactive API documentation

### MQTT Example

**Setup MQTT Broker (if needed):**
```bash
# Using Docker
docker run -it -p 1883:1883 eclipse-mosquitto

# Or install locally
sudo apt-get install mosquitto mosquitto-clients
sudo systemctl start mosquitto
```

**Terminal 1 (Device Server):**
```bash
cd src/ac_training_lab/ot-2/examples
python mqtt_device_example.py
```

**Terminal 2 (Orchestrator):**
```bash
cd src/ac_training_lab/ot-2/examples
python mqtt_orchestrator_example.py
```

## Key Features

### 🚀 **Easy Migration from Prefect**
Both solutions use similar decorator syntax to Prefect:
```python
# Prefect (has pydantic conflicts)
from prefect import flow
@flow
def my_task(param: int) -> str:
    return f"Result: {param}"

# Our FastAPI solution (no conflicts)  
from ac_training_lab.ot_2.orchestration import task
@task
def my_task(param: int) -> str:
    return f"Result: {param}"

# Our MQTT solution (no conflicts)
from ac_training_lab.ot_2.orchestration.mqtt_wrapper import mqtt_task
@mqtt_task  
def my_task(param: int) -> str:
    return f"Result: {param}"
```

### 🔐 **Security Features**
- Optional authentication tokens (FastAPI)
- TLS encryption support (both solutions)
- Input validation and sanitization
- Error handling and timeout protection

### 📡 **Remote Execution**
Both solutions support secure remote execution over networks:
- LAN: Direct IP connections
- Internet: Through VPN, port forwarding, or cloud MQTT brokers
- IoT: MQTT works well with cellular/satellite connections

### 🔄 **Synchronization**
- Automatic client-server API discovery
- Type-safe parameter passing
- Structured error reporting
- Request correlation and tracing

## Comparison with Existing Solutions

| Feature | Prefect | Our FastAPI | Our MQTT | Original MQTT |
|---------|---------|-------------|----------|---------------|
| Pydantic Compatibility | ❌ Conflicts | ✅ Compatible | ✅ Compatible | ✅ Compatible |
| Setup Complexity | High | Low | Medium | High |
| Decorator Syntax | ✅ @flow | ✅ @task | ✅ @mqtt_task | ❌ Manual |
| Type Safety | ✅ Yes | ✅ Yes | ✅ Yes | ❌ Manual |
| Web Interface | ✅ Dashboard | ✅ Auto-docs | ❌ No | ❌ No |
| Network Requirements | HTTP + DB | HTTP only | MQTT only | MQTT only |
| Error Handling | ✅ Advanced | ✅ Good | ✅ Good | ❌ Manual |
| Auto-discovery | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |

## Production Deployment

### FastAPI Deployment
```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker device_example:server.app

# Or use systemd service
sudo systemctl enable ot2-device-server
sudo systemctl start ot2-device-server
```

### MQTT Deployment
```bash
# Run as background service
nohup python mqtt_device_example.py > device.log 2>&1 &

# Or use systemd service
sudo systemctl enable ot2-mqtt-device
sudo systemctl start ot2-mqtt-device
```

### Security Considerations
- Use TLS encryption for production
- Implement proper authentication
- Network segmentation and firewalls
- Regular security updates
- Monitor and log all communications

## Troubleshooting

### Common Issues

**FastAPI:**
- Port 8000 already in use: Change port in server configuration
- Connection refused: Check firewall settings
- Import errors: Ensure FastAPI dependencies are installed

**MQTT:**
- Connection failed: Verify MQTT broker is running and accessible
- Message timeout: Check network connectivity and broker configuration
- Authentication errors: Verify username/password and broker settings

### Debug Mode
Enable debug logging in both solutions:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Connectivity
```bash
# FastAPI
curl http://localhost:8000/tasks

# MQTT  
mosquitto_pub -h localhost -t "test" -m "hello"
mosquitto_sub -h localhost -t "test"
```

## License

This orchestration framework is part of the ac-training-lab package and follows the same MIT license.

## Contributing

Please see the main repository's CONTRIBUTING.md for guidelines on contributing to this orchestration framework.