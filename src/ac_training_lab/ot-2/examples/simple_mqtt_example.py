"""
Simple standalone MQTT orchestration example for OT-2.

This is a minimal working example that can be copied and used independently.
"""

import json
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional
from queue import Queue, Empty
import inspect

try:
    import paho.mqtt.client as mqtt
except ImportError as e:
    print("ERROR: paho-mqtt not installed")
    print("Install with: pip install paho-mqtt")
    raise

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MINIMAL MQTT ORCHESTRATION FRAMEWORK ====================

# Global registry for tasks
_mqtt_task_registry: Dict[str, Dict[str, Any]] = {}

def mqtt_task(func_or_name=None):
    """
    Decorator to register a function as an MQTT-callable task.
    Can be used as @mqtt_task or @mqtt_task("custom_name")
    """
    def decorator(func: Callable) -> Callable:
        # Determine task name  
        if isinstance(func_or_name, str):
            task_name = func_or_name
        else:
            task_name = func.__name__
            
        sig = inspect.signature(func)
        
        _mqtt_task_registry[task_name] = {
            'function': func,
            'signature': sig,
            'name': task_name,
            'doc': func.__doc__ or "",
        }
        
        logger.info(f"Registered MQTT task: {task_name}")
        return func
    
    # Handle both @mqtt_task and @mqtt_task("name") usage
    if callable(func_or_name):
        # Used as @mqtt_task (without parentheses)
        return decorator(func_or_name)
    else:
        # Used as @mqtt_task("name") or @mqtt_task()
        return decorator

class SimpleMQTTDeviceServer:
    """Simple MQTT device server."""
    
    def __init__(self, broker_host: str, device_id: str = None, broker_port: int = 1883):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.device_id = device_id or f"ot2-{uuid.uuid4().hex[:8]}"
        
        # MQTT topics
        self.command_topic = f"ot2/{self.device_id}/command"
        self.result_topic = f"ot2/{self.device_id}/result"
        
        # MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        self.connected = False
        self.running = False
        
        logger.info(f"MQTT Device Server initialized: {self.device_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            client.subscribe(self.command_topic, qos=1)
            logger.info(f"Subscribed to: {self.command_topic}")
        else:
            logger.error(f"Failed to connect to MQTT broker. Code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            logger.info(f"Received command: {payload}")
            self._execute_command(payload)
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _execute_command(self, payload: Dict[str, Any]):
        try:
            request_id = payload.get('request_id', str(uuid.uuid4()))
            task_name = payload.get('task')
            parameters = payload.get('parameters', {})
            
            if task_name not in _mqtt_task_registry:
                raise ValueError(f"Task '{task_name}' not found")
            
            task_info = _mqtt_task_registry[task_name]
            func = task_info['function']
            
            # Execute the function
            bound_args = task_info['signature'].bind(**parameters)
            bound_args.apply_defaults()
            result = func(**bound_args.arguments)
            
            # Publish success
            result_payload = {
                'request_id': request_id,
                'task': task_name,
                'status': 'success',
                'result': result,
                'timestamp': time.time()
            }
            
            self.client.publish(self.result_topic, json.dumps(result_payload), qos=1)
            logger.info(f"Task '{task_name}' completed successfully")
            
        except Exception as e:
            # Publish error
            error_payload = {
                'request_id': payload.get('request_id', 'unknown'),
                'task': payload.get('task', 'unknown'),
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
            
            self.client.publish(self.result_topic, json.dumps(error_payload), qos=1)
            logger.error(f"Task execution failed: {e}")
    
    def start(self):
        """Start the MQTT device server."""
        logger.info("Starting MQTT device server...")
        
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.running = True
            self.client.loop_start()
            
            logger.info("MQTT device server started successfully")
            
            while self.running:
                time.sleep(1)
                
        except Exception as e:
            logger.error(f"Failed to start MQTT server: {e}")
            raise
    
    def stop(self):
        """Stop the MQTT device server."""
        logger.info("Stopping MQTT device server...")
        self.running = False
        
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()

class SimpleMQTTOrchestratorClient:
    """Simple MQTT orchestrator client."""
    
    def __init__(self, broker_host: str, device_id: str, broker_port: int = 1883, timeout: float = 30.0):
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.device_id = device_id
        self.timeout = timeout
        
        # MQTT topics
        self.command_topic = f"ot2/{device_id}/command"
        self.result_topic = f"ot2/{device_id}/result"
        
        # MQTT client
        self.client_id = f"orchestrator-{uuid.uuid4().hex[:8]}"
        self.client = mqtt.Client(self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        self.pending_requests: Dict[str, Queue] = {}
        self.connected = False
        
        logger.info(f"MQTT Orchestrator Client initialized for: {device_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            logger.info("Orchestrator connected to MQTT broker")
            client.subscribe(self.result_topic, qos=1)
        else:
            logger.error(f"Failed to connect to MQTT broker. Code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            if msg.topic == self.result_topic:
                request_id = payload.get('request_id')
                if request_id in self.pending_requests:
                    self.pending_requests[request_id].put(payload)
                    
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def connect(self):
        """Connect to the MQTT broker."""
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.client.loop_start()
            
            # Wait for connection
            start_time = time.time()
            while not self.connected and (time.time() - start_time) < 10:
                time.sleep(0.1)
            
            if not self.connected:
                raise ConnectionError("Failed to connect to MQTT broker")
                
            logger.info("Orchestrator client connected")
            
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from MQTT broker."""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Orchestrator client disconnected")
    
    def execute_task(self, task_name: str, **kwargs) -> Any:
        """Execute a task on the remote device."""
        if not self.connected:
            raise ConnectionError("Not connected to MQTT broker")
        
        request_id = str(uuid.uuid4())
        command = {
            'request_id': request_id,
            'task': task_name,
            'parameters': kwargs,
            'timestamp': time.time()
        }
        
        result_queue = Queue()
        self.pending_requests[request_id] = result_queue
        
        try:
            # Send command
            self.client.publish(self.command_topic, json.dumps(command), qos=1)
            logger.info(f"Sent command: {task_name} with params: {kwargs}")
            
            # Wait for result
            try:
                result = result_queue.get(timeout=self.timeout)
                
                if result.get('status') == 'success':
                    logger.info(f"Task '{task_name}' completed successfully")
                    return result.get('result')
                else:
                    raise RuntimeError(f"Task failed: {result.get('error')}")
                    
            except Empty:
                raise TimeoutError(f"Task '{task_name}' timed out after {self.timeout} seconds")
                
        finally:
            self.pending_requests.pop(request_id, None)
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()

# ==================== OT-2 TASK DEFINITIONS ====================

@mqtt_task
def mix_color(R: int, Y: int, B: int, mix_well: str) -> str:
    """
    Simulate mixing colors (replace with real OT-2 code).
    """
    total = R + Y + B
    if total > 300:
        raise ValueError("Sum of proportions must be <= 300")
    
    logger.info(f"SIMULATED: Mixing R:{R}, Y:{Y}, B:{B} in well {mix_well}")
    time.sleep(1)  # Simulate work
    
    return f"Mixed RGB({R},{Y},{B}) in well {mix_well}"

@mqtt_task
def move_sensor(well: str, action: str = "to") -> str:
    """Simulate sensor movement."""
    if action == "to":
        logger.info(f"SIMULATED: Moving sensor to well {well}")
        time.sleep(0.5)
        return f"Sensor positioned over well {well}"
    else:
        logger.info("SIMULATED: Moving sensor back to home")
        time.sleep(0.5)
        return "Sensor returned to home position"

@mqtt_task
def get_status() -> dict:
    """Get robot status."""
    return {
        "status": "ready", 
        "mode": "simulation",
        "tasks_available": list(_mqtt_task_registry.keys()),
        "timestamp": time.time()
    }

# ==================== MAIN FUNCTIONS ====================

def run_device_server():
    """Run the MQTT device server."""
    BROKER_HOST = "localhost"
    DEVICE_ID = "ot2-demo-device"
    
    print("\n" + "="*60)
    print("🤖 OT-2 MQTT Device Server")
    print("="*60)
    print(f"📡 MQTT Broker: {BROKER_HOST}:1883")
    print(f"🏷️  Device ID: {DEVICE_ID}")
    print(f"🔧 Available Tasks: {list(_mqtt_task_registry.keys())}")
    print("="*60)
    print("MQTT Topics:")
    print(f"  📥 Commands: ot2/{DEVICE_ID}/command")
    print(f"  📤 Results:  ot2/{DEVICE_ID}/result")
    print("="*60)
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    try:
        server = SimpleMQTTDeviceServer(BROKER_HOST, DEVICE_ID)
        server.start()
    except KeyboardInterrupt:
        print("\n🛑 Stopping server...")
        server.stop()
        print("✅ Server stopped")

def run_orchestrator_demo():
    """Run a demo orchestrator."""
    BROKER_HOST = "localhost"
    DEVICE_ID = "ot2-demo-device"
    
    print("\n" + "="*60)
    print("🎨 OT-2 MQTT Orchestrator Demo")
    print("="*60)
    print(f"📡 MQTT Broker: {BROKER_HOST}:1883")
    print(f"🤖 Target Device: {DEVICE_ID}")
    print("="*60 + "\n")
    
    try:
        with SimpleMQTTOrchestratorClient(BROKER_HOST, DEVICE_ID) as client:
            # Run some example experiments
            experiments = [
                {"R": 100, "Y": 50, "B": 30, "mix_well": "A1"},
                {"R": 50, "Y": 100, "B": 50, "mix_well": "A2"},
                {"R": 80, "Y": 80, "B": 80, "mix_well": "A3"},
            ]
            
            for i, exp in enumerate(experiments, 1):
                print(f"🧪 Experiment {i}: {exp}")
                
                # Mix colors
                mix_result = client.execute_task("mix_color", **exp)
                print(f"  ✅ {mix_result}")
                
                # Move sensor
                sensor_result = client.execute_task("move_sensor", well=exp["mix_well"], action="to")
                print(f"  ✅ {sensor_result}")
                
                # Wait for measurement
                print(f"  ⏳ Measuring...")
                time.sleep(1)
                
                # Return sensor
                return_result = client.execute_task("move_sensor", well="", action="back")
                print(f"  ✅ {return_result}")
                print()
            
            # Get final status
            status = client.execute_task("get_status")
            print(f"📊 Final Status: {status}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        print("💡 Make sure the MQTT broker and device server are running!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "orchestrator":
        run_orchestrator_demo()
    else:
        run_device_server()