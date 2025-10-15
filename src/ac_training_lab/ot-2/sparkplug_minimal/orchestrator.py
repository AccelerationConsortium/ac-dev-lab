"""Orchestrator code - controls OT-2 remotely.

Import the same module as device, but functions are called remotely.
The @sparkplug_task decorator handles sending commands to the device.
"""

from decorator import sparkplug_task, start_orchestrator, stop
import time


# Import the same task definition (or could be defined here)
@sparkplug_task
def greet(name):
    """This will execute remotely on the device."""
    pass  # Body doesn't matter - just the signature


# Start orchestrator (this sets up MQTT in background)
if __name__ == "__main__":
    start_orchestrator()
    
    print("Orchestrator started. Calling device functions...\n")
    
    # Call the function normally - it executes on the device!
    print("Calling: greet('World')")
    result = greet(name="World")
    print(f"Result: {result}\n")
    
    # Call again with different parameter
    print("Calling: greet('OT-2')")
    result = greet(name="OT-2")
    print(f"Result: {result}\n")
    
    print("Done!")
    stop()

