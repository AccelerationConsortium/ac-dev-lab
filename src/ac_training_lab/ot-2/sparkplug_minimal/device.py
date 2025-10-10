"""Minimal Sparkplug B device example - runs on OT-2."""

import json
import time
import paho.mqtt.client as mqtt
from mqtt_spb_wrapper import MqttSpbEntityDevice

from decorator import sparkplug_task, get_registered_tasks


# Define device tasks using decorator
@sparkplug_task
def greet(name):
    """Simple greeting function."""
    return f"Hello, {name}!"


# MQTT Configuration
BROKER = "248cc294c37642359297f75b7b023374.s2.eu.hivemq.cloud"
PORT = 8883
USERNAME = "sgbaird"
PASSWORD = "D.Pq5gYtejYbU#L"

# Sparkplug B configuration
GROUP_ID = "lab_devices"
EDGE_NODE_ID = "ot2_device_001"
DEVICE_ID = "device_001"


def on_command(topic, payload):
    """Handle commands from orchestrator."""
    print(f"Received command: {payload}")
    
    # Extract command from payload
    if "metrics" in payload:
        for metric in payload["metrics"]:
            task_name = metric.get("name")
            task_params = metric.get("value", {})
            
            # Execute registered task
            tasks = get_registered_tasks()
            if task_name in tasks:
                result = tasks[task_name](**task_params)
                print(f"Task {task_name} result: {result}")
                
                # Publish result back
                device.publish_data(task_name + "_result", result)
            else:
                print(f"Unknown task: {task_name}")


def main():
    """Run the Sparkplug B device."""
    global device
    
    print(f"Starting Sparkplug B device: {DEVICE_ID}")
    
    # Create Sparkplug B device
    device = MqttSpbEntityDevice(
        GROUP_ID, 
        EDGE_NODE_ID, 
        DEVICE_ID, 
        False
    )
    
    # Configure MQTT connection
    device._MqttSpbEntity__client.tls_set()
    device._MqttSpbEntity__client.username_pw_set(USERNAME, PASSWORD)
    
    # Set command callback
    device.on_command = on_command
    
    # Connect to broker
    device.connect(BROKER, PORT)
    
    # Publish Birth certificate with available tasks
    print("Publishing Birth certificate with available tasks:")
    for task_name in get_registered_tasks().keys():
        print(f"  - {task_name}")
        device.publish_birth()
    
    print("Device ready. Waiting for commands...")
    
    # Keep running
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down device...")
        device.disconnect()


if __name__ == "__main__":
    main()
