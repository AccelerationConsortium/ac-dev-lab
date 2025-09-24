# Quick Start Guide: OT-2 Orchestration

Get up and running with OT-2 orchestration in 5 minutes! Choose between FastAPI (HTTP) or MQTT solutions.

## 🚀 FastAPI Solution (Recommended)

### 1. Install Dependencies
```bash
pip install fastapi uvicorn httpx opentrons
```

### 2. Create Device Script (`device.py`)
```python
#!/usr/bin/env python3
"""Minimal OT-2 Device Server"""

import sys
from pathlib import Path

# Add orchestration to path  
sys.path.append(str(Path(__file__).parent / "orchestration"))
from device_server import DeviceServer, task

# Mock Opentrons for demo (replace with real opentrons imports)
try:
    import opentrons.simulate
    protocol = opentrons.simulate.get_protocol_api("2.12")
    SIMULATION = False
except ImportError:
    protocol = None
    SIMULATION = True

@task
def mix_colors(r: int, g: int, b: int, well: str = "A1") -> str:
    """Mix RGB colors in specified well."""
    if SIMULATION:
        return f"SIMULATED: Mixed RGB({r},{g},{b}) in {well}"
    
    # Add your real OT-2 code here:
    # protocol.load_labware(...)
    # pipette.aspirate(...)
    # pipette.dispense(...)
    
    return f"Mixed RGB({r},{g},{b}) in {well}"

@task
def get_status() -> dict:
    """Get robot status."""
    return {"status": "ready", "simulation": SIMULATION}

if __name__ == "__main__":
    server = DeviceServer(port=8000)
    print("🤖 OT-2 Device Server starting...")
    print("📡 API: http://localhost:8000/docs")
    server.run()
```

### 3. Create Orchestrator Script (`orchestrator.py`)
```python
#!/usr/bin/env python3
"""Minimal OT-2 Orchestrator"""

import sys
from pathlib import Path

# Add orchestration to path
sys.path.append(str(Path(__file__).parent / "orchestration"))
from orchestrator_client import OrchestratorClient

def main():
    device_url = "http://localhost:8000"
    
    with OrchestratorClient(device_url) as client:
        # Check status
        status = client.execute_task("get_status")
        print(f"Device Status: {status}")
        
        # Run color mixing
        result = client.execute_task("mix_colors", r=255, g=128, b=64, well="B2")
        print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

### 4. Run the System
```bash
# Terminal 1: Start device server
python device.py

# Terminal 2: Run orchestrator  
python orchestrator.py
```

### 5. Test via Web Interface
Open http://localhost:8000/docs and try the API interactively!

---

## 📡 MQTT Solution (For IoT Environments)

### 1. Install Dependencies
```bash
pip install paho-mqtt opentrons

# Start MQTT broker (using Docker)
docker run -it -p 1883:1883 eclipse-mosquitto
```

### 2. Create Device Script (`mqtt_device.py`)
```python
#!/usr/bin/env python3
"""Minimal OT-2 MQTT Device Server"""

import sys
from pathlib import Path

# Add orchestration to path
sys.path.append(str(Path(__file__).parent / "orchestration"))
from mqtt_wrapper import MQTTDeviceServer, mqtt_task

@mqtt_task
def mix_colors(r: int, g: int, b: int, well: str = "A1") -> str:
    """Mix RGB colors in specified well."""
    # Add your real OT-2 code here
    return f"SIMULATED: Mixed RGB({r},{g},{b}) in {well}"

@mqtt_task
def get_status() -> dict:
    """Get robot status."""
    return {"status": "ready", "device": "ot2-001"}

if __name__ == "__main__":
    server = MQTTDeviceServer(
        broker_host="localhost",
        device_id="ot2-001"
    )
    print("🤖 OT-2 MQTT Device Server starting...")
    print("📡 MQTT Topics: ot2/ot2-001/*")
    server.start()
```

### 3. Create Orchestrator Script (`mqtt_orchestrator.py`)
```python
#!/usr/bin/env python3
"""Minimal OT-2 MQTT Orchestrator"""

import sys
from pathlib import Path

# Add orchestration to path
sys.path.append(str(Path(__file__).parent / "orchestration"))
from mqtt_wrapper import MQTTOrchestratorClient

def main():
    with MQTTOrchestratorClient("localhost", "ot2-001") as client:
        # Check status
        status = client.execute_task("get_status")
        print(f"Device Status: {status}")
        
        # Run color mixing
        result = client.execute_task("mix_colors", r=255, g=128, b=64, well="B2")
        print(f"Result: {result}")

if __name__ == "__main__":
    main()
```

### 4. Run the System
```bash
# Terminal 1: Start MQTT broker (if not using Docker)
mosquitto

# Terminal 2: Start device server  
python mqtt_device.py

# Terminal 3: Run orchestrator
python mqtt_orchestrator.py
```

---

## 🔧 Using the Full Examples

For more complete examples with real OT-2 integration:

```bash
# Clone the repository
git clone https://github.com/AccelerationConsortium/ac-dev-lab.git
cd ac-dev-lab/src/ac_training_lab/ot-2/examples

# FastAPI Examples
python device_example.py              # Full device server
python orchestrator_example.py       # Full orchestrator

# MQTT Examples  
python mqtt_device_example.py        # Full MQTT device
python mqtt_orchestrator_example.py  # Full MQTT orchestrator

# Standalone Examples (copy-paste ready)
python simple_fastapi_example.py     # Self-contained FastAPI
python simple_mqtt_example.py        # Self-contained MQTT
```

## 📚 Next Steps

1. **Read the full documentation:** `README_orchestration.md`
2. **Migration from Prefect:** `MIGRATION_GUIDE.md`  
3. **Production deployment:** See deployment section in README
4. **Add security:** Enable TLS and authentication
5. **Customize for your lab:** Modify tasks for your specific OT-2 setup

## 🆘 Troubleshooting

**"Module not found" errors:**
- Ensure you're in the right directory
- Check that orchestration files are present
- Use absolute paths if needed

**"Connection refused" errors:**  
- FastAPI: Check port 8000 is available
- MQTT: Ensure MQTT broker is running

**Opentrons conflicts:**
- Use separate Python environment
- Don't install Prefect in the same environment  

**Need help?** Open an issue in the ac-training-lab repository!