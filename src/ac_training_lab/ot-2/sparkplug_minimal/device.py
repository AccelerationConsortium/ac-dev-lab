"""Device code - runs on OT-2.

This looks like normal Python code. The @sparkplug_task decorator
handles all MQTT communication in the background.
"""

from decorator import sparkplug_task, start_device
import time


# Define your device functions with the decorator
@sparkplug_task
def greet(name):
    """Simple greeting function."""
    return f"Hello, {name}!"


# Start device (this sets up MQTT in background)
if __name__ == "__main__":
    start_device("ot2_001")
    
    print("Device running. Waiting for commands...")
    print("Available tasks:", ["greet"])
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down...")

