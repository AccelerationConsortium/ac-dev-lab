# Minimal Sparkplug B MQTT Example for OT-2

This is a minimal three-file example showing how to use Sparkplug B over MQTT for OT-2 orchestration.

## Files

- `decorator.py` - Simple decorator for registering device tasks
- `device.py` - Device code that runs on the OT-2
- `orchestrator.py` - Orchestrator code that controls the device remotely

## Installation

```bash
pip install paho-mqtt mqtt-spb-wrapper
```

## Usage

1. Start the device (on OT-2):
```bash
python device.py
```

2. Run the orchestrator (from laptop/cloud):
```bash
python orchestrator.py
```

The orchestrator sends a name to the device, which responds with "Hello, {name}!".

## Key Features

- **Auto-discovery**: Device publishes Birth certificates declaring available tasks
- **No manual sync**: Orchestrator discovers device capabilities automatically
- **Compatible with Opentrons**: No pydantic/anyio conflicts
- **Decorator-based**: Simple `@sparkplug_task` decorator like Prefect's `@flow`
