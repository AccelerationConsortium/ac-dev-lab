"""Minimal Sparkplug B orchestrator example - controls OT-2 remotely."""

import time
from mqtt_spb_wrapper import MqttSpbEntityApplication


# MQTT Configuration
BROKER = "248cc294c37642359297f75b7b023374.s2.eu.hivemq.cloud"
PORT = 8883
USERNAME = "sgbaird"
PASSWORD = "D.Pq5gYtejYbU#L"

# Sparkplug B configuration
GROUP_ID = "lab_devices"
EDGE_NODE_ID = "ot2_device_001"
DEVICE_ID = "device_001"

# Track device capabilities
device_tasks = []


def on_message(topic, payload):
    """Handle messages from device."""
    print(f"Received from device: {payload}")
    
    # Check for Birth certificate
    if "DBIRTH" in topic or "NBIRTH" in topic:
        print("Device came online! Discovering capabilities...")
        if "metrics" in payload:
            device_tasks.clear()
            for metric in payload["metrics"]:
                task_name = metric.get("name")
                if task_name and not task_name.endswith("_result"):
                    device_tasks.append(task_name)
                    print(f"  - Discovered task: {task_name}")
    
    # Check for task results
    if "metrics" in payload:
        for metric in payload["metrics"]:
            if metric.get("name", "").endswith("_result"):
                result = metric.get("value")
                print(f"Task result: {result}")


def send_command(app, task_name, **params):
    """Send command to device to execute a task."""
    print(f"Sending command: {task_name} with params {params}")
    
    # Publish command as Sparkplug B metric
    app.publish_data(
        f"{GROUP_ID}/{EDGE_NODE_ID}/DCMD/{DEVICE_ID}",
        {
            "metrics": [
                {
                    "name": task_name,
                    "value": params,
                    "type": "String"
                }
            ]
        }
    )


def main():
    """Run the orchestrator."""
    print("Starting Sparkplug B orchestrator")
    
    # Create Sparkplug B application (host)
    app = MqttSpbEntityApplication(GROUP_ID)
    
    # Configure MQTT connection
    app._MqttSpbEntity__client.tls_set()
    app._MqttSpbEntity__client.username_pw_set(USERNAME, PASSWORD)
    
    # Set message callback
    app.on_message = on_message
    
    # Connect to broker
    app.connect(BROKER, PORT)
    
    print("Orchestrator connected. Waiting for device...")
    time.sleep(3)
    
    # Send greeting command
    print("\n--- Sending greet command with name='World' ---")
    send_command(app, "greet", name="World")
    
    print("\nWaiting for response...")
    time.sleep(5)
    
    # Send another greeting
    print("\n--- Sending greet command with name='OT-2' ---")
    send_command(app, "greet", name="OT-2")
    
    print("\nWaiting for response...")
    time.sleep(5)
    
    print("\nDisconnecting orchestrator...")
    app.disconnect()


if __name__ == "__main__":
    main()
