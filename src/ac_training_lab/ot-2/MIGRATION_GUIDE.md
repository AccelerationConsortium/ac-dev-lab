# Migration Guide: From Prefect to OT-2 Orchestration

This guide helps you migrate existing Prefect workflows to the new OT-2 orchestration solutions that avoid pydantic version conflicts.

## Problem Summary

**Before:** Prefect (pydantic v2) + Opentrons (pydantic v1) = 💥 Version Conflict  
**After:** OT-2 Orchestration (FastAPI/MQTT) + Opentrons = ✅ Compatible

## Quick Migration Examples

### 1. Prefect to FastAPI Migration

**OLD (Prefect - doesn't work with Opentrons):**
```python
from prefect import flow
import opentrons.execute  # ❌ pydantic conflict

@flow
def mix_colors(r: int, g: int, b: int):
    # Your OT-2 code
    return f"Mixed RGB({r},{g},{b})"

# Deploy and run via Prefect server
```

**NEW (FastAPI - compatible with Opentrons):**
```python
from ac_training_lab.ot_2.orchestration import task
import opentrons.execute  # ✅ Works fine

@task  # Same decorator pattern!
def mix_colors(r: int, g: int, b: int):
    # Your OT-2 code (unchanged)
    return f"Mixed RGB({r},{g},{b})"

# Run device server
from ac_training_lab.ot_2.orchestration import DeviceServer
server = DeviceServer()
server.run()  # http://localhost:8000
```

### 2. Prefect to MQTT Migration

**NEW (MQTT - also compatible):**
```python
from ac_training_lab.ot_2.orchestration.mqtt_wrapper import mqtt_task
import opentrons.execute  # ✅ Works fine

@mqtt_task  # Similar decorator pattern!
def mix_colors(r: int, g: int, b: int):
    # Your OT-2 code (unchanged)
    return f"Mixed RGB({r},{g},{b})"

# Run MQTT device server
from ac_training_lab.ot_2.orchestration.mqtt_wrapper import MQTTDeviceServer
server = MQTTDeviceServer("mqtt-broker.local", device_id="ot2-001")
server.start()
```

## Step-by-Step Migration Process

### Phase 1: Setup New Environment

1. **Create new conda/venv environment:**
```bash
conda create -n ot2-orchestration python=3.11
conda activate ot2-orchestration
```

2. **Install dependencies (choose one):**
```bash
# For FastAPI solution:
pip install -r requirements-fastapi.txt

# For MQTT solution:
pip install -r requirements-mqtt.txt

# For both solutions:
pip install -r requirements-fastapi.txt -r requirements-mqtt.txt
```

3. **Verify Opentrons compatibility:**
```python
import opentrons.simulate
from ac_training_lab.ot_2.orchestration import task
print("✅ No pydantic conflicts!")
```

### Phase 2: Convert Existing Code

#### A. Convert Flow Definitions

**Prefect Flow:**
```python
from prefect import flow, task as prefect_task

@prefect_task
def prepare_reagents():
    return "Reagents ready"

@flow
def color_mixing_workflow(colors: dict):
    reagents = prepare_reagents()
    # ... workflow logic
    return result
```

**FastAPI equivalent:**
```python
from ac_training_lab.ot_2.orchestration import task

@task
def prepare_reagents():
    return "Reagents ready"

@task  
def color_mixing_workflow(colors: dict):
    reagents = prepare_reagents()  # Call directly
    # ... same workflow logic
    return result
```

#### B. Convert Deployments

**Prefect Deployment:**
```python
from prefect.deployments import run_deployment

# Deploy flows to Prefect server
deployment = Deployment.build_from_flow(
    flow=my_flow,
    name="ot2-color-mixing",
    work_pool_name="ot2-pool"
)
deployment.apply()

# Execute remotely
run_deployment("my-flow/ot2-color-mixing", parameters={...})
```

**FastAPI equivalent:**
```python
from ac_training_lab.ot_2.orchestration import OrchestratorClient

# Tasks are automatically available via HTTP API
with OrchestratorClient("http://ot2-device:8000") as client:
    result = client.execute_task("color_mixing_workflow", colors={...})
```

**MQTT equivalent:**
```python
from ac_training_lab.ot_2.orchestration.mqtt_wrapper import MQTTOrchestratorClient

with MQTTOrchestratorClient("mqtt-broker.local", "ot2-device-001") as client:
    result = client.execute_task("color_mixing_workflow", colors={...})
```

### Phase 3: Advanced Features Migration

#### Error Handling & Retries

**Prefect:**
```python
from prefect import flow
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(retries=3, retry_delay_seconds=5)
def unreliable_task():
    # Task with automatic retries
    pass
```

**Our Solutions:**
```python
# Implement retry logic explicitly
from ac_training_lab.ot_2.orchestration import task
import time

@task
def unreliable_task():
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Your task logic here
            return "Success"
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(5)  # Retry delay
                continue
            raise e
```

#### State Management

**Prefect (built-in state management):**
```python
from prefect import get_run_logger

@flow
def stateful_workflow():
    logger = get_run_logger()
    # Prefect handles state automatically
```

**Our Solutions (explicit state management):**
```python
@task 
def stateful_workflow():
    import logging
    logger = logging.getLogger(__name__)
    
    # Store state in database/file as needed
    state = {"step": 1, "data": {...}}
    
    # Your workflow logic with explicit state handling
    return state
```

### Phase 4: Deployment Migration

#### Development Setup

**Prefect (requires Prefect server):**
```bash
prefect server start  # Starts web UI + database
prefect worker start --pool default-agent-pool
```

**FastAPI (self-contained):**
```bash
cd src/ac_training_lab/ot-2/examples
python device_example.py  # Starts device server
# Visit http://localhost:8000/docs for web UI
```

**MQTT (requires MQTT broker):**
```bash
# Start MQTT broker (one-time setup)
docker run -it -p 1883:1883 eclipse-mosquitto

# Start device server
cd src/ac_training_lab/ot-2/examples  
python mqtt_device_example.py
```

#### Production Deployment

**FastAPI Production:**
```bash
# Install production server
pip install gunicorn

# Run with multiple workers
gunicorn -w 4 -k uvicorn.workers.UvicornWorker device_example:server.app

# Or create systemd service
sudo systemctl enable ot2-device-server
sudo systemctl start ot2-device-server
```

**MQTT Production:**
```bash
# Use cloud MQTT broker (e.g., AWS IoT, HiveMQ Cloud)
# Or install Mosquitto with clustering

# Run as service
nohup python mqtt_device_example.py > device.log 2>&1 &
```

## Feature Comparison

| Feature | Prefect | FastAPI Solution | MQTT Solution |
|---------|---------|------------------|---------------|
| **Compatibility** |
| Opentrons Support | ❌ Conflicts | ✅ Compatible | ✅ Compatible |
| Pydantic Version | v2 (conflicts) | v1 compatible | v1 compatible |
| **Ease of Use** |
| Decorator Syntax | `@flow` | `@task` | `@mqtt_task` |
| Learning Curve | Medium | Low | Medium |
| Setup Complexity | High (server+DB) | Low (single file) | Medium (broker) |
| **Features** |
| Web Interface | ✅ Advanced | ✅ Auto-generated | ❌ None |
| Error Handling | ✅ Built-in | 🔶 Manual | 🔶 Manual |
| Retry Logic | ✅ Built-in | 🔶 Manual | 🔶 Manual |
| State Management | ✅ Built-in | 🔶 Manual | 🔶 Manual |
| **Network** |
| Protocol | HTTP + DB | HTTP only | MQTT only |
| Firewall Friendly | 🔶 Multiple ports | ✅ Single port | ✅ Single port |
| Offline Resilience | ❌ Needs server | ❌ Needs connection | ✅ Queuing |
| **Scalability** |
| Multiple Devices | ✅ Yes | ✅ Yes | ✅ Yes |
| Load Balancing | ✅ Built-in | 🔶 Manual | 🔶 Manual |
| Monitoring | ✅ Built-in | 🔶 Manual | 🔶 Manual |

Legend: ✅ Full support, 🔶 Manual implementation needed, ❌ Not available

## Common Migration Issues & Solutions

### Issue 1: Import Conflicts
**Problem:** Mixed Prefect and Opentrons imports causing pydantic errors.  
**Solution:** Use separate environments and never import both in the same script.

### Issue 2: Complex Workflows
**Problem:** Multi-step Prefect workflows with dependencies.  
**Solution:** Break into multiple tasks and orchestrate explicitly:

```python
# Instead of Prefect's automatic dependency resolution:
@task
def complex_workflow():
    step1_result = step1_task()
    step2_result = step2_task(step1_result)
    return final_task(step1_result, step2_result)
```

### Issue 3: Missing Prefect Features
**Problem:** Need retries, caching, or state management.  
**Solution:** Implement explicitly or use external tools:

```python
# Add caching with functools
from functools import lru_cache

@task
@lru_cache(maxsize=128)
def cached_computation(params):
    # Expensive computation
    return result

# Add monitoring with logging
import logging
logger = logging.getLogger(__name__)

@task
def monitored_task():
    logger.info("Task started")
    try:
        result = do_work()
        logger.info(f"Task completed: {result}")
        return result
    except Exception as e:
        logger.error(f"Task failed: {e}")
        raise
```

## Testing Your Migration

### 1. Unit Testing
```python
import pytest
from your_module import mix_colors

def test_mix_colors():
    result = mix_colors(100, 50, 30, "A1")
    assert "Mixed RGB(100,50,30)" in result
```

### 2. Integration Testing
```python
# Test FastAPI server
from fastapi.testclient import TestClient
from your_device_server import app

client = TestClient(app)

def test_execute_task():
    response = client.post(
        "/execute/mix_colors",
        json={"R": 100, "Y": 50, "B": 30, "mix_well": "A1"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "success"
```

### 3. End-to-End Testing
```python
# Test with real OT-2 simulator
import opentrons.simulate
from your_orchestrator import run_experiment

def test_full_workflow():
    # Use simulation mode for testing
    results = run_experiment([
        {"R": 100, "Y": 50, "B": 30, "well": "A1"}
    ])
    assert len(results) == 1
    assert results[0]["status"] == "success"
```

## Best Practices for Migration

### 1. **Start Small**
- Migrate one simple workflow first
- Test thoroughly before migrating complex workflows
- Keep Prefect environment as backup during transition

### 2. **Maintain Compatibility** 
- Use the same function signatures when possible
- Keep existing parameter names and types
- Document any breaking changes

### 3. **Add Monitoring**
- Implement logging for all tasks
- Add health checks for device servers
- Monitor network connectivity and broker status

### 4. **Security Considerations**
- Use TLS encryption in production
- Implement authentication for FastAPI endpoints
- Secure MQTT broker with username/password
- Consider network segmentation

### 5. **Documentation**
- Document all task functions clearly
- Maintain API compatibility matrices
- Create runbooks for common operations

## Getting Help

### Common Resources:
- **FastAPI Docs:** https://fastapi.tiangolo.com/
- **MQTT Protocol:** https://mqtt.org/
- **Opentrons API:** https://docs.opentrons.com/

### Troubleshooting:
- Check logs for import/dependency errors
- Verify network connectivity between components  
- Test with simple examples before complex workflows
- Use simulation mode for development and testing

### Community Support:
- Open issues in the ac-training-lab repository
- Join relevant Slack channels or forums
- Contribute back improvements and fixes

This migration guide should help you successfully transition from Prefect to our compatible orchestration solutions while maintaining the same functionality and improving reliability with your OT-2 workflows.