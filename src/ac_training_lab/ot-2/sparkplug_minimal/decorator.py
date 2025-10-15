"""Simple decorator and infrastructure for remote task execution via MQTT.

This module handles all the MQTT/Sparkplug B complexity internally.
Users just decorate functions and call them normally.
"""

import json
import os
import time
import threading
from typing import Any, Callable, Dict
import paho.mqtt.client as mqtt

# Configuration - load from environment variables (credentials never exposed in logs)
BROKER = os.getenv("HIVEMQ_HOST") or os.getenv("MQTT_BROKER", "localhost")
PORT = int(os.getenv("MQTT_PORT", "1883"))
USERNAME = os.getenv("HIVEMQ_USERNAME") or os.getenv("MQTT_USERNAME", "")
PASSWORD = os.getenv("HIVEMQ_PASSWORD") or os.getenv("MQTT_PASSWORD", "")
GROUP_ID = os.getenv("MQTT_GROUP_ID", "lab")
DEVICE_ID = None  # Set in device.py
ORCHESTRATOR_MODE = False  # Set to True in orchestrator.py

# Internal state
_task_registry: Dict[str, Callable] = {}
_client = None
_results = {}
_device_capabilities = []


def sparkplug_task(func: Callable) -> Callable:
    """Decorator to register a device function for remote execution.
    
    On device: function executes locally when called
    From orchestrator: function sends command to device and waits for result
    """
    _task_registry[func.__name__] = func
    
    def wrapper(*args, **kwargs):
        if ORCHESTRATOR_MODE:
            # Remote execution: send command to device
            return _execute_remote(func.__name__, *args, **kwargs)
        else:
            # Local execution on device
            return func(*args, **kwargs)
    
    wrapper.__name__ = func.__name__
    wrapper.__doc__ = func.__doc__
    return wrapper


def _on_message(client, userdata, msg):
    """Handle incoming MQTT messages."""
    try:
        payload = json.loads(msg.payload.decode())
        
        if ORCHESTRATOR_MODE:
            # Orchestrator receiving results from device
            if "result" in payload:
                task_id = payload.get("task_id")
                if task_id:
                    _results[task_id] = payload["result"]
            elif "capabilities" in payload:
                _device_capabilities.clear()
                _device_capabilities.extend(payload["capabilities"])
        else:
            # Device receiving commands
            if "task" in payload:
                task_name = payload["task"]
                task_id = payload.get("task_id")
                params = payload.get("params", {})
                
                # Execute task
                if task_name in _task_registry:
                    result = _task_registry[task_name](**params)
                    
                    # Send result back
                    _publish({
                        "task_id": task_id,
                        "result": result
                    })
    except Exception as e:
        print(f"Error handling message: {e}")


def _publish(payload: Dict[str, Any]):
    """Publish message to MQTT broker."""
    if _client:
        topic = f"{GROUP_ID}/{DEVICE_ID}/data"
        _client.publish(topic, json.dumps(payload))


def _execute_remote(task_name: str, *args, **kwargs) -> Any:
    """Execute task on remote device and wait for result."""
    task_id = f"{task_name}_{time.time()}"
    
    # Send command
    _publish({
        "task": task_name,
        "task_id": task_id,
        "params": kwargs
    })
    
    # Wait for result
    timeout = 10
    start = time.time()
    while task_id not in _results:
        if time.time() - start > timeout:
            raise TimeoutError(f"Task {task_name} timed out")
        time.sleep(0.1)
    
    return _results.pop(task_id)


def start_device(device_id: str):
    """Start device in background. Call this once at module import."""
    global DEVICE_ID, _client
    DEVICE_ID = device_id
    
    _client = mqtt.Client()
    if PORT == 8883:  # Use TLS for secure port
        _client.tls_set()
    if USERNAME:  # Only set credentials if provided
        _client.username_pw_set(USERNAME, PASSWORD)
    _client.on_message = _on_message
    
    _client.connect(BROKER, PORT)
    _client.subscribe(f"{GROUP_ID}/{DEVICE_ID}/cmd")
    
    # Publish capabilities
    _client.publish(
        f"{GROUP_ID}/{DEVICE_ID}/data",
        json.dumps({"capabilities": list(_task_registry.keys())})
    )
    
    # Start background thread
    _client.loop_start()
    print(f"Device {device_id} connected to broker")


def start_orchestrator():
    """Start orchestrator. Call this once at module import."""
    global ORCHESTRATOR_MODE, _client
    ORCHESTRATOR_MODE = True
    
    _client = mqtt.Client()
    if PORT == 8883:  # Use TLS for secure port
        _client.tls_set()
    if USERNAME:  # Only set credentials if provided
        _client.username_pw_set(USERNAME, PASSWORD)
    _client.on_message = _on_message
    
    _client.connect(BROKER, PORT)
    _client.subscribe(f"{GROUP_ID}/+/data")
    
    # Start background thread
    _client.loop_start()
    print("Orchestrator connected to broker")
    
    # Wait for device capabilities
    time.sleep(2)


def stop():
    """Stop MQTT client."""
    if _client:
        _client.loop_stop()
        _client.disconnect()
