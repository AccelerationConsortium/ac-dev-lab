"""
Lightweight MQTT wrapper for OT-2 orchestration.

This provides a simpler alternative to the FastAPI solution for cases where
MQTT is preferred over HTTP. It uses decorators and automatic synchronization
similar to the FastAPI approach but over MQTT.
"""

import json
import logging
import threading
import time
import uuid
from typing import Any, Callable, Dict, Optional, Union
from queue import Queue, Empty
import inspect

try:
    import paho.mqtt.client as mqtt
except ImportError as e:
    raise ImportError("paho-mqtt is required. Install with: pip install paho-mqtt") from e

logger = logging.getLogger(__name__)

# Global registry for tasks
_mqtt_task_registry: Dict[str, Dict[str, Any]] = {}


def mqtt_task(name: Optional[str] = None):
    """
    Decorator to register a function as an MQTT-callable task.
    
    Usage:
        @mqtt_task
        def mix_colors(r: int, g: int, b: int) -> str:
            return f"Mixed RGB({r}, {g}, {b})"
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        
        # Get function signature for validation
        sig = inspect.signature(func)
        
        # Register the task
        _mqtt_task_registry[task_name] = {
            'function': func,
            'signature': sig,
            'name': task_name,
            'doc': func.__doc__ or "",
        }
        
        logger.info(f"Registered MQTT task: {task_name}")
        return func
    
    return decorator


class MQTTDeviceServer:
    """
    MQTT-based device server for OT-2 orchestration.
    
    This provides similar functionality to the FastAPI server but uses MQTT
    for communication, which can be more suitable for some network setups.
    """
    
    def __init__(
        self,
        broker_host: str,
        broker_port: int = 1883,
        device_id: str = None,
        username: str = None,
        password: str = None,
        use_tls: bool = False,
        topic_prefix: str = "ot2"
    ):
        """
        Initialize the MQTT device server.
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
            device_id: Unique device identifier (auto-generated if None)
            username: MQTT username (optional)
            password: MQTT password (optional)
            use_tls: Whether to use TLS encryption
            topic_prefix: Prefix for MQTT topics
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.device_id = device_id or f"ot2-{uuid.uuid4().hex[:8]}"
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.topic_prefix = topic_prefix
        
        # MQTT topics
        self.command_topic = f"{topic_prefix}/{self.device_id}/command"
        self.result_topic = f"{topic_prefix}/{self.device_id}/result"
        self.status_topic = f"{topic_prefix}/{self.device_id}/status"
        
        # MQTT client
        self.client = mqtt.Client()
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        if use_tls:
            self.client.tls_set()
        
        self.connected = False
        self.running = False
        
        logger.info(f"MQTT Device Server initialized for device: {self.device_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Subscribe to command topic
            client.subscribe(self.command_topic, qos=1)
            logger.info(f"Subscribed to commands on: {self.command_topic}")
            
            # Publish status
            self._publish_status("online", {"tasks": list(_mqtt_task_registry.keys())})
            
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            logger.info(f"Received command: {payload}")
            
            # Execute the command
            self._execute_command(payload)
            
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    def _execute_command(self, payload: Dict[str, Any]):
        """Execute a command from MQTT message."""
        try:
            # Extract command details
            request_id = payload.get('request_id', str(uuid.uuid4()))
            task_name = payload.get('task')
            parameters = payload.get('parameters', {})
            
            if not task_name:
                raise ValueError("No task specified in command")
            
            if task_name not in _mqtt_task_registry:
                raise ValueError(f"Task '{task_name}' not found. Available: {list(_mqtt_task_registry.keys())}")
            
            # Get task info
            task_info = _mqtt_task_registry[task_name]
            func = task_info['function']
            
            # Bind and validate parameters
            bound_args = task_info['signature'].bind(**parameters)
            bound_args.apply_defaults()
            
            # Execute the function
            result = func(**bound_args.arguments)
            
            # Publish successful result
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
            # Publish error result
            error_payload = {
                'request_id': payload.get('request_id', 'unknown'),
                'task': payload.get('task', 'unknown'),
                'status': 'error',
                'error': str(e),
                'timestamp': time.time()
            }
            
            self.client.publish(self.result_topic, json.dumps(error_payload), qos=1)
            logger.error(f"Task execution failed: {e}")
    
    def _publish_status(self, status: str, data: Dict[str, Any] = None):
        """Publish device status."""
        status_payload = {
            'device_id': self.device_id,
            'status': status,
            'timestamp': time.time(),
            'data': data or {}
        }
        
        self.client.publish(self.status_topic, json.dumps(status_payload), qos=1)
    
    def start(self):
        """Start the MQTT device server."""
        logger.info("Starting MQTT device server...")
        
        try:
            self.client.connect(self.broker_host, self.broker_port, 60)
            self.running = True
            
            # Start the MQTT loop
            self.client.loop_start()
            
            logger.info("MQTT device server started successfully")
            
            # Keep the server running
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
            self._publish_status("offline")
            self.client.loop_stop()
            self.client.disconnect()
        
        logger.info("MQTT device server stopped")


class MQTTOrchestratorClient:
    """
    MQTT client for orchestrating OT-2 devices.
    """
    
    def __init__(
        self,
        broker_host: str,
        device_id: str,
        broker_port: int = 1883,
        username: str = None,
        password: str = None,
        use_tls: bool = False,
        topic_prefix: str = "ot2",
        timeout: float = 30.0
    ):
        """
        Initialize the MQTT orchestrator client.
        
        Args:
            broker_host: MQTT broker hostname
            device_id: Target device identifier
            broker_port: MQTT broker port
            username: MQTT username (optional)
            password: MQTT password (optional)
            use_tls: Whether to use TLS encryption
            topic_prefix: Prefix for MQTT topics
            timeout: Command timeout in seconds
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.device_id = device_id
        self.username = username
        self.password = password
        self.use_tls = use_tls
        self.topic_prefix = topic_prefix
        self.timeout = timeout
        
        # MQTT topics
        self.command_topic = f"{topic_prefix}/{device_id}/command"
        self.result_topic = f"{topic_prefix}/{device_id}/result"
        self.status_topic = f"{topic_prefix}/{device_id}/status"
        
        # MQTT client
        self.client_id = f"orchestrator-{uuid.uuid4().hex[:8]}"
        self.client = mqtt.Client(self.client_id)
        self.client.on_connect = self._on_connect
        self.client.on_message = self._on_message
        
        if username and password:
            self.client.username_pw_set(username, password)
        
        if use_tls:
            self.client.tls_set()
        
        # Result handling
        self.pending_requests: Dict[str, Queue] = {}
        self.connected = False
        
        logger.info(f"MQTT Orchestrator Client initialized for device: {device_id}")
    
    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker."""
        if rc == 0:
            self.connected = True
            logger.info(f"Orchestrator connected to MQTT broker")
            
            # Subscribe to result topic
            client.subscribe(self.result_topic, qos=1)
            client.subscribe(self.status_topic, qos=1)
            
        else:
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """Handle incoming MQTT messages."""
        try:
            payload = json.loads(msg.payload.decode('utf-8'))
            
            if msg.topic == self.result_topic:
                # Handle task result
                request_id = payload.get('request_id')
                if request_id in self.pending_requests:
                    self.pending_requests[request_id].put(payload)
            
            elif msg.topic == self.status_topic:
                # Handle status update
                logger.info(f"Device status: {payload}")
                
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in message: {e}")
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
                raise ConnectionError("Failed to connect to MQTT broker within timeout")
                
            logger.info("Orchestrator client connected successfully")
            
        except Exception as e:
            logger.error(f"Failed to connect orchestrator client: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from the MQTT broker."""
        if self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Orchestrator client disconnected")
    
    def execute_task(
        self,
        task_name: str,
        parameters: Dict[str, Any] = None,
        timeout: Optional[float] = None,
        **kwargs
    ) -> Any:
        """
        Execute a task on the remote device via MQTT.
        
        Args:
            task_name: Name of the task to execute
            parameters: Parameters to pass to the task
            timeout: Command timeout (uses default if None)
            **kwargs: Additional parameters
            
        Returns:
            Task execution result
        """
        if not self.connected:
            raise ConnectionError("Not connected to MQTT broker")
        
        # Merge parameters
        params = parameters or {}
        params.update(kwargs)
        
        # Create request
        request_id = str(uuid.uuid4())
        command = {
            'request_id': request_id,
            'task': task_name,
            'parameters': params,
            'timestamp': time.time()
        }
        
        # Setup result queue
        result_queue = Queue()
        self.pending_requests[request_id] = result_queue
        
        try:
            # Send command
            self.client.publish(self.command_topic, json.dumps(command), qos=1)
            logger.info(f"Sent command: {task_name} with params: {params}")
            
            # Wait for result
            cmd_timeout = timeout or self.timeout
            try:
                result = result_queue.get(timeout=cmd_timeout)
                
                if result.get('status') == 'success':
                    logger.info(f"Task '{task_name}' completed successfully")
                    return result.get('result')
                else:
                    raise RuntimeError(f"Task failed: {result.get('error', 'Unknown error')}")
                    
            except Empty:
                raise TimeoutError(f"Task '{task_name}' timed out after {cmd_timeout} seconds")
                
        finally:
            # Cleanup
            self.pending_requests.pop(request_id, None)
    
    def __enter__(self):
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.disconnect()


# Convenience functions
def create_mqtt_server(**kwargs) -> MQTTDeviceServer:
    """Create and return an MQTT device server."""
    return MQTTDeviceServer(**kwargs)


def create_mqtt_client(**kwargs) -> MQTTOrchestratorClient:
    """Create and return an MQTT orchestrator client."""
    return MQTTOrchestratorClient(**kwargs)