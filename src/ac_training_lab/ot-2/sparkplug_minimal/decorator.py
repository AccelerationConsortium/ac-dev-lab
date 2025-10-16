"""Simple decorator and infrastructure for remote task execution via Sparkplug B/MQTT.

This module handles all the MQTT/Sparkplug B complexity internally using mqtt-spb-wrapper.
Users just decorate functions and call them normally.
"""

import inspect
import os
import time
from typing import Any, Callable, Dict
from mqtt_spb_wrapper import MqttSpbEntityDevice, MqttSpbEntityApplication

# Configuration - load from environment variables (credentials never exposed in logs)
BROKER = os.getenv("HIVEMQ_HOST") or os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USERNAME = os.getenv("HIVEMQ_USERNAME") or os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("HIVEMQ_PASSWORD") or os.getenv("MQTT_PASSWORD", "")
GROUP_ID = os.getenv("MQTT_GROUP_ID", "lab")
DEVICE_ID = None  # Set in device.py
ORCHESTRATOR_MODE = False  # Set to True in orchestrator.py
USE_TLS = PORT == 8883  # Enable TLS for secure port

# Internal state
_task_registry: Dict[str, Callable] = {}
_entity = None
_results = {}
_device_capabilities = {}


def sparkplug_task(func: Callable) -> Callable:
    """Decorator to register a device function for remote execution.
    
    On device: function executes locally when called, publishes signature via Birth
    From orchestrator: function sends command to device and waits for result
    """
    _task_registry[func.__name__] = func
    
    def wrapper(*args, **kwargs):
        if ORCHESTRATOR_MODE:
            # Remote execution: send command to device via Sparkplug CMD message
            return _execute_remote(func.__name__, *args, **kwargs)
        else:
            # Local execution on device
            return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def _handle_command(payload):
    """Handle incoming command from orchestrator."""
    if not ORCHESTRATOR_MODE and "task" in payload:
        task_name = payload["task"]
        task_id = payload.get("task_id")
        params = payload.get("params", {})
        
        # Execute task
        if task_name in _task_registry:
            try:
                result = _task_registry[task_name](**params)
                # Send result back via DATA message
                _entity.data.set_value(f"result_{task_id}", result)
                _entity.publish_data()
            except Exception as e:
                _entity.data.set_value(f"error_{task_id}", str(e))
                _entity.publish_data()


def _handle_data(payload):
    """Handle incoming data from device."""
    if ORCHESTRATOR_MODE:
        # Orchestrator receiving results from device
        for metric in payload.get("metrics", []):
            name = metric.get("name", "")
            value = metric.get("value")
            
            if name.startswith("result_"):
                task_id = name.replace("result_", "")
                _results[task_id] = value
            elif name.startswith("error_"):
                task_id = name.replace("error_", "")
                _results[task_id] = Exception(value)


def _handle_birth(payload):
    """Handle device Birth message (capability announcement)."""
    if ORCHESTRATOR_MODE:
        # Parse device capabilities from Birth message
        _device_capabilities.clear()
        for metric in payload.get("metrics", []):
            name = metric.get("name", "")
            if name.startswith("task_"):
                task_name = name.replace("task_", "")
                _device_capabilities[task_name] = metric.get("value", {})


def _execute_remote(task_name: str, *args, **kwargs) -> Any:
    """Execute task on remote device via Sparkplug CMD and wait for result."""
    # Validate task exists on device
    if task_name not in _device_capabilities:
        raise ValueError(f"Task '{task_name}' not available on device. Available: {list(_device_capabilities.keys())}")
    
    task_id = f"{task_name}_{time.time()}"
    
    # Send command via Sparkplug CMD message
    _entity.data.set_value("task", task_name)
    _entity.data.set_value("task_id", task_id)
    for key, value in kwargs.items():
        _entity.data.set_value(f"param_{key}", value)
    _entity.publish_data()
    
    # Wait for result
    timeout = 10
    start = time.time()
    while task_id not in _results:
        if time.time() - start > timeout:
            raise TimeoutError(f"Task {task_name} timed out after {timeout}s")
        time.sleep(0.1)
    
    result = _results.pop(task_id)
    if isinstance(result, Exception):
        raise result
    return result


def start_device(device_id: str):
    """Start device as Sparkplug Edge Node."""
    global DEVICE_ID, _entity
    DEVICE_ID = device_id
    
    # Create Sparkplug Device entity
    _entity = MqttSpbEntityDevice(
        GROUP_ID,
        DEVICE_ID,
        BROKER,
        PORT,
        USERNAME,
        PASSWORD,
        use_tls=USE_TLS
    )
    
    # Register callbacks
    _entity.on_command = lambda payload: _handle_command(payload)
    
    # Publish Birth certificate with task capabilities
    for task_name, func in _task_registry.items():
        sig = inspect.signature(func)
        params = [param.name for param in sig.parameters.values()]
        _entity.data.set_value(f"task_{task_name}", {
            "parameters": params,
            "doc": func.__doc__ or ""
        })
    
    # Connect and start
    _entity.connect()
    print(f"Device {device_id} connected with Sparkplug B")
    print(f"Available tasks: {list(_task_registry.keys())}")


def start_orchestrator():
    """Start orchestrator as Sparkplug Host Application."""
    global ORCHESTRATOR_MODE, _entity
    ORCHESTRATOR_MODE = True
    
    # Create Sparkplug Application entity
    _entity = MqttSpbEntityApplication(
        GROUP_ID,
        BROKER,
        PORT,
        USERNAME,
        PASSWORD,
        use_tls=USE_TLS
    )
    
    # Register callbacks
    _entity.on_message = lambda topic, payload: (
        _handle_birth(payload) if "NBIRTH" in topic or "DBIRTH" in topic
        else _handle_data(payload) if "NDATA" in topic or "DDATA" in topic
        else None
    )
    
    # Connect and start
    _entity.connect()
    print("Orchestrator connected with Sparkplug B")
    
    # Wait for device Birth messages
    time.sleep(2)
    print(f"Discovered devices with tasks: {list(_device_capabilities.keys())}")


def stop():
    """Stop Sparkplug entity."""
    if _entity:
        _entity.disconnect()
