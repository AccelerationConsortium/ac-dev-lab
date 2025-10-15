# Minimal MQTT Orchestration for OT-2

Simple remote task execution for OT-2 devices. All MQTT complexity hidden in decorator.

## The Problem

Prefect and FastAPI can't run on OT-2 due to dependency conflicts (anyio, jsonschema versions).

## The Solution  

Three simple files:
- `decorator.py` - Handles all MQTT communication
- `device.py` - Runs on OT-2 (looks like normal Python)
- `orchestrator.py` - Runs remotely (calls device functions)

## Usage

**Device (OT-2):**
```python
from decorator import sparkplug_task, start_device

@sparkplug_task
def greet(name):
    return f"Hello, {name}!"

start_device("ot2_001")
```

**Orchestrator (laptop/cloud):**
```python  
from decorator import sparkplug_task, start_orchestrator

@sparkplug_task
def greet(name):
    pass  # Executes remotely on device

start_orchestrator()
result = greet(name="World")  # Remote call!
print(result)  # "Hello, World!"
```

## Installation

```bash
pip install paho-mqtt
```

Only one dependency - no conflicts with Opentrons.

## Running

1. Start device: `python device.py`
2. Run orchestrator: `python orchestrator.py`

The decorator handles all MQTT communication automatically.
