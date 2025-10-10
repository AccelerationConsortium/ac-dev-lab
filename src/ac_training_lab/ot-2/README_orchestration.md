# OT-2 Orchestration with Sparkplug B MQTT

Minimal Sparkplug B over MQTT solution for Opentrons OT-2 orchestration that avoids Prefect/Opentrons dependency conflicts.

## Problem

Prefect and FastAPI cannot be used with Opentrons due to dependency incompatibilities:
- Prefect/FastAPI require pydantic v2, anyio v4+, jsonschema v4.18+
- Opentrons requires anyio <4.0.0, jsonschema <4.18.0

## Solution: Sparkplug B over MQTT

Sparkplug B uses minimal dependencies (paho-mqtt + mqtt-spb-wrapper) with no Opentrons conflicts.

## Quick Start

See `sparkplug_minimal/` for a three-file example:
- `decorator.py` - Task registration decorator
- `device.py` - Device code (runs on OT-2)
- `orchestrator.py` - Orchestrator code (runs remotely)

Example: orchestrator sends name, device responds with "Hello, {name}!"

## Key Benefits

- **Auto-discovery**: Devices publish available tasks via Birth certificates
- **No manual sync**: Orchestrator discovers capabilities automatically  
- **Compatible with Opentrons**: No pydantic/anyio/jsonschema conflicts
- **Decorator-based**: `@sparkplug_task` decorator like Prefect's `@flow`
- **Minimal dependencies**: Only paho-mqtt and mqtt-spb-wrapper needed

## Installation

```bash
pip install paho-mqtt mqtt-spb-wrapper
```

## Usage

1. Start device on OT-2:
```bash
python sparkplug_minimal/device.py
```

2. Run orchestrator remotely:
```bash
python sparkplug_minimal/orchestrator.py
```

See `sparkplug_minimal/README.md` for complete details.
