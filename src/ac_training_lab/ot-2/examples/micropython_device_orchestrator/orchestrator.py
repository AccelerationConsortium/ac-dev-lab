"""
orchestrator.py - Remote orchestration of laboratory devices

This script runs on your laptop, server, or cloud instance (not on the lab device).
It can control multiple laboratory devices remotely via MQTT or HTTP.

Compatible with:
- Local Python environment (laptop/desktop)
- Cloud platforms (Railway, AWS, Google Cloud)
- Jupyter notebooks
- Any environment with network access

Usage:
1. Ensure device.py is running on your laboratory hardware
2. Configure MQTT_BROKER to match your device
3. Run: python orchestrator.py
4. Orchestrator will connect and control the remote device
"""

import time
import asyncio
import json
from typing import Dict, Any, List, Optional
from dataclasses import dataclass

# Import our MQTT client (from the orchestration framework)
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent / "orchestration"))

try:
    from mqtt_wrapper import MQTTOrchestratorClient
    MQTT_AVAILABLE = True
except ImportError:
    print("⚠️  MQTT wrapper not available - using simplified client")
    MQTT_AVAILABLE = False
    # Fallback simple MQTT client for demonstration
    import paho.mqtt.client as mqtt

# Orchestrator Configuration
MQTT_BROKER = "broker.hivemq.com"  # Must match device configuration
MQTT_PORT = 1883
DEFAULT_TIMEOUT = 15.0

@dataclass
class DeviceInfo:
    """Information about a connected laboratory device."""
    device_id: str
    platform: str
    tasks_available: List[str]
    last_seen: float
    status: str

class LaboratoryOrchestrator:
    """
    Remote orchestrator for laboratory devices.
    
    This class can control multiple laboratory devices running device.py
    from anywhere with network connectivity (laptop, cloud, etc.).
    """
    
    def __init__(self, broker_host: str = MQTT_BROKER, broker_port: int = MQTT_PORT):
        """
        Initialize the laboratory orchestrator.
        
        Args:
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.connected_devices: Dict[str, DeviceInfo] = {}
        
        print(f"🎯 Laboratory Orchestrator initialized")
        print(f"📡 MQTT Broker: {broker_host}:{broker_port}")
    
    def connect_to_device(self, device_id: str) -> 'DeviceConnection':
        """
        Connect to a specific laboratory device.
        
        Args:
            device_id: Target device identifier
            
        Returns:
            DeviceConnection object for controlling the device
        """
        return DeviceConnection(
            device_id=device_id,
            broker_host=self.broker_host,
            broker_port=self.broker_port
        )
    
    def discover_devices(self, timeout: float = 10.0) -> List[str]:
        """
        Discover available laboratory devices on the network.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            List of discovered device IDs
        """
        print(f"🔍 Discovering devices for {timeout}s...")
        
        # In a real implementation, this would scan MQTT topics
        # For now, return known devices or simulate discovery
        discovered = []
        
        # Simulate device discovery
        potential_devices = ["lab-device-001", "pico-w-lab-001", "ot2-device-001"]
        
        for device_id in potential_devices:
            try:
                # Try to get status from each potential device
                with self.connect_to_device(device_id) as device:
                    status = device.get_status(timeout=3.0)
                    if status:
                        discovered.append(device_id)
                        print(f"✅ Found device: {device_id}")
            except Exception:
                # Device not available
                pass
        
        print(f"📊 Discovery complete: {len(discovered)} devices found")
        return discovered

class DeviceConnection:
    """
    Connection to a specific laboratory device.
    
    This provides a high-level interface for controlling remote lab hardware.
    """
    
    def __init__(self, device_id: str, broker_host: str, broker_port: int):
        """
        Initialize connection to a laboratory device.
        
        Args:
            device_id: Target device identifier  
            broker_host: MQTT broker hostname
            broker_port: MQTT broker port
        """
        self.device_id = device_id
        self.broker_host = broker_host
        self.broker_port = broker_port
        
        if MQTT_AVAILABLE:
            self.client = MQTTOrchestratorClient(
                broker_host=broker_host,
                broker_port=broker_port,
                device_id=device_id,
                timeout=DEFAULT_TIMEOUT,
                topic_prefix="lab"  # Match device.py topic prefix
            )
        else:
            self.client = None
            print("⚠️  Using simplified MQTT client")
    
    def __enter__(self):
        """Context manager entry."""
        if self.client and MQTT_AVAILABLE:
            self.client.connect()
        print(f"🔗 Connected to device: {self.device_id}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if self.client and MQTT_AVAILABLE:
            self.client.disconnect()
        print(f"📋 Disconnected from device: {self.device_id}")
    
    def execute_task(self, task_name: str, **kwargs) -> Any:
        """
        Execute a task on the remote laboratory device.
        
        Args:
            task_name: Name of the task to execute
            **kwargs: Task parameters
            
        Returns:
            Task execution result
        """
        if self.client and MQTT_AVAILABLE:
            return self.client.execute_task(task_name, **kwargs)
        else:
            # Simulate task execution for demo
            print(f"🔄 [SIMULATED] Executing '{task_name}' on {self.device_id}")
            print(f"   Parameters: {kwargs}")
            time.sleep(0.5)  # Simulate execution time
            return f"Simulated result for {task_name}"
    
    # High-level device control methods
    
    def get_status(self, timeout: Optional[float] = None) -> Dict[str, Any]:
        """Get comprehensive device status."""
        return self.execute_task("get_device_status")
    
    def read_sensor(self, pin: int) -> Dict[str, Any]:
        """Read analog sensor from specified pin."""
        return self.execute_task("read_analog_sensor", pin=pin)
    
    def control_led(self, pin: int, state: bool) -> str:
        """Control LED on/off."""
        return self.execute_task("control_led", pin=pin, state=state)
    
    def move_servo(self, pin: int, angle: int) -> str:
        """Move servo to specified angle (0-180 degrees)."""
        return self.execute_task("move_servo", pin=pin, angle=angle)
    
    def read_multiple_sensors(self, pins: List[int]) -> Dict[str, Any]:
        """Read multiple sensors simultaneously."""
        return self.execute_task("read_multiple_sensors", pins=pins)
    
    def calibrate_device(self, led_pin: int, sensor_pins: List[int]) -> Dict[str, Any]:
        """Run device calibration sequence."""
        return self.execute_task("run_device_calibration", led_pin=led_pin, sensor_pins=sensor_pins)

class ExperimentManager:
    """
    High-level experiment management for laboratory orchestration.
    
    This class provides common experimental workflows and data collection.
    """
    
    def __init__(self, orchestrator: LaboratoryOrchestrator):
        """
        Initialize experiment manager.
        
        Args:
            orchestrator: Laboratory orchestrator instance
        """
        self.orchestrator = orchestrator
        self.experiment_results = []
    
    def run_sensor_calibration_experiment(
        self, 
        device_ids: List[str], 
        sensor_pins: List[int],
        led_pin: int = 25
    ) -> Dict[str, Any]:
        """
        Run sensor calibration across multiple devices.
        
        Args:
            device_ids: List of devices to calibrate
            sensor_pins: Sensor pins to calibrate on each device
            led_pin: LED pin for status indication
            
        Returns:
            Calibration results from all devices
        """
        print("🔬 Starting Multi-Device Sensor Calibration Experiment")
        print(f"📊 Devices: {len(device_ids)}, Sensors per device: {len(sensor_pins)}")
        
        experiment_start = time.time()
        results = {}
        
        for device_id in device_ids:
            print(f"\n🤖 Calibrating device: {device_id}")
            
            try:
                with self.orchestrator.connect_to_device(device_id) as device:
                    
                    # Get initial device status
                    status = device.get_status()
                    print(f"   Device platform: {status.get('platform', 'unknown')}")
                    print(f"   Available memory: {status.get('free_memory', 'unknown')} bytes")
                    
                    # Run calibration
                    calibration_result = device.calibrate_device(
                        led_pin=led_pin,
                        sensor_pins=sensor_pins
                    )
                    
                    results[device_id] = {
                        "device_status": status,
                        "calibration": calibration_result,
                        "success": calibration_result["calibration_status"] == "completed"
                    }
                    
                    print(f"   ✅ Calibration: {calibration_result['calibration_status']}")
                    print(f"   📈 Quality: {calibration_result['calibration_quality']}")
                    print(f"   📊 Max drift: {calibration_result['max_drift']:.4f}V")
                    
            except Exception as e:
                print(f"   ❌ Device {device_id} failed: {e}")
                results[device_id] = {
                    "success": False,
                    "error": str(e)
                }
        
        experiment_duration = time.time() - experiment_start
        
        # Compile overall results
        successful_devices = [dev for dev, res in results.items() if res.get("success")]
        failed_devices = [dev for dev, res in results.items() if not res.get("success")]
        
        overall_results = {
            "experiment_type": "sensor_calibration",
            "start_time": experiment_start,
            "duration_seconds": experiment_duration,
            "devices_tested": len(device_ids),
            "successful_devices": len(successful_devices),
            "failed_devices": len(failed_devices),
            "success_rate": len(successful_devices) / len(device_ids) * 100,
            "device_results": results,
            "summary": {
                "successful": successful_devices,
                "failed": failed_devices
            }
        }
        
        # Store results
        self.experiment_results.append(overall_results)
        
        print(f"\n📈 Experiment Complete!")
        print(f"   ⏱️  Duration: {experiment_duration:.1f}s")
        print(f"   ✅ Success Rate: {overall_results['success_rate']:.1f}%")
        print(f"   📊 Successful: {successful_devices}")
        if failed_devices:
            print(f"   ❌ Failed: {failed_devices}")
        
        return overall_results
    
    def run_sensor_monitoring_experiment(
        self,
        device_id: str,
        sensor_pins: List[int],
        duration_minutes: float = 5.0,
        sample_interval_seconds: float = 30.0
    ) -> Dict[str, Any]:
        """
        Run continuous sensor monitoring experiment.
        
        Args:
            device_id: Device to monitor
            sensor_pins: Sensor pins to monitor
            duration_minutes: Experiment duration in minutes
            sample_interval_seconds: Time between samples
            
        Returns:
            Monitoring experiment results
        """
        print(f"📊 Starting Sensor Monitoring Experiment")
        print(f"🤖 Device: {device_id}")
        print(f"📈 Sensors: {sensor_pins}")
        print(f"⏱️  Duration: {duration_minutes} minutes")
        print(f"📊 Sample interval: {sample_interval_seconds}s")
        
        experiment_start = time.time()
        duration_seconds = duration_minutes * 60
        samples = []
        
        with self.orchestrator.connect_to_device(device_id) as device:
            
            # Initial status check
            status = device.get_status()
            print(f"✅ Device connected: {status.get('platform', 'unknown')}")
            
            # Turn on LED to indicate monitoring
            device.control_led(25, True)  # Assuming LED on pin 25
            
            sample_count = 0
            while (time.time() - experiment_start) < duration_seconds:
                
                sample_count += 1
                sample_time = time.time()
                
                print(f"📊 Sample {sample_count} at {sample_time - experiment_start:.1f}s")
                
                # Read all sensors
                sensor_data = device.read_multiple_sensors(sensor_pins)
                
                # Add timing info
                sample_data = {
                    "sample_number": sample_count,
                    "timestamp": sample_time,
                    "elapsed_seconds": sample_time - experiment_start,
                    "sensor_data": sensor_data
                }
                
                samples.append(sample_data)
                
                # Print sample summary
                avg_voltage = sensor_data["average_voltage"]
                print(f"   Average voltage: {avg_voltage:.3f}V")
                
                # Wait for next sample (or exit if duration reached)
                remaining_time = duration_seconds - (time.time() - experiment_start)
                wait_time = min(sample_interval_seconds, remaining_time)
                
                if wait_time > 0:
                    time.sleep(wait_time)
            
            # Turn off LED
            device.control_led(25, False)
        
        # Analyze results
        total_duration = time.time() - experiment_start
        
        # Calculate statistics
        all_voltages = []
        for sample in samples:
            for sensor, reading in sample["sensor_data"]["readings"].items():
                all_voltages.append(reading["voltage"])
        
        if all_voltages:
            avg_voltage = sum(all_voltages) / len(all_voltages)
            min_voltage = min(all_voltages)
            max_voltage = max(all_voltages)
            voltage_range = max_voltage - min_voltage
        else:
            avg_voltage = min_voltage = max_voltage = voltage_range = 0
        
        monitoring_results = {
            "experiment_type": "sensor_monitoring",
            "device_id": device_id,
            "start_time": experiment_start,
            "planned_duration": duration_seconds,
            "actual_duration": total_duration,
            "sample_count": len(samples),
            "sample_interval": sample_interval_seconds,
            "sensor_pins": sensor_pins,
            "samples": samples,
            "statistics": {
                "average_voltage": avg_voltage,
                "min_voltage": min_voltage,
                "max_voltage": max_voltage,
                "voltage_range": voltage_range,
                "samples_per_minute": len(samples) / (total_duration / 60)
            }
        }
        
        self.experiment_results.append(monitoring_results)
        
        print(f"\n📈 Monitoring Complete!")
        print(f"   ⏱️  Duration: {total_duration:.1f}s")
        print(f"   📊 Samples: {len(samples)}")
        print(f"   📈 Avg voltage: {avg_voltage:.3f}V")
        print(f"   📊 Range: {voltage_range:.3f}V")
        
        return monitoring_results

def main():
    """
    Main orchestrator demonstration.
    
    This shows how to use the orchestrator to control laboratory devices remotely.
    """
    print("=" * 70)
    print("🎯 Laboratory Device Orchestrator")
    print("=" * 70)
    print("📡 This script controls remote laboratory devices via MQTT")
    print("🤖 Ensure device.py is running on your laboratory hardware")
    print("=" * 70)
    
    # Initialize orchestrator
    orchestrator = LaboratoryOrchestrator(MQTT_BROKER, MQTT_PORT)
    
    try:
        # Example 1: Single device control
        print("\n🔌 Example 1: Single Device Control")
        print("-" * 50)
        
        device_id = "lab-device-001"  # Change to match your device
        
        with orchestrator.connect_to_device(device_id) as device:
            
            # Get device status
            print(f"📊 Getting status from {device_id}...")
            status = device.get_status()
            print(f"   Platform: {status.get('platform', 'unknown')}")
            print(f"   Available tasks: {status.get('tasks_available', [])}")
            
            # Control LED
            print(f"💡 Turning LED on...")
            led_result = device.control_led(pin=25, state=True)
            print(f"   {led_result}")
            
            # Read sensor
            print(f"📊 Reading sensor...")
            sensor_data = device.read_sensor(pin=26)
            print(f"   Voltage: {sensor_data['voltage']:.3f}V")
            
            # Move servo
            print(f"🔄 Moving servo...")
            servo_result = device.move_servo(pin=15, angle=90)
            print(f"   {servo_result}")
            
            # Turn LED off
            print(f"💡 Turning LED off...")
            device.control_led(pin=25, state=False)
        
        # Example 2: Multi-device experiment
        print("\n🔬 Example 2: Multi-Device Experiment")
        print("-" * 50)
        
        experiment_manager = ExperimentManager(orchestrator)
        
        # Run calibration experiment
        calibration_results = experiment_manager.run_sensor_calibration_experiment(
            device_ids=["lab-device-001"],  # Add more device IDs as available
            sensor_pins=[26, 27, 28],
            led_pin=25
        )
        
        # Example 3: Continuous monitoring
        print("\n📈 Example 3: Continuous Monitoring")
        print("-" * 50)
        
        monitoring_results = experiment_manager.run_sensor_monitoring_experiment(
            device_id="lab-device-001",
            sensor_pins=[26, 27],
            duration_minutes=1.0,  # Short duration for demo
            sample_interval_seconds=10.0
        )
        
        # Display final summary
        print("\n" + "=" * 70)
        print("📋 ORCHESTRATION SESSION SUMMARY")
        print("=" * 70)
        print(f"🔬 Experiments completed: {len(experiment_manager.experiment_results)}")
        
        for i, result in enumerate(experiment_manager.experiment_results, 1):
            experiment_type = result["experiment_type"]
            duration = result.get("duration_seconds", result.get("actual_duration", 0))
            print(f"   {i}. {experiment_type}: {duration:.1f}s")
        
        print("✅ All experiments completed successfully!")
        
    except Exception as e:
        print(f"❌ Orchestration error: {e}")
        print("💡 Check that:")
        print("   - device.py is running on your laboratory hardware")
        print("   - MQTT broker is accessible")
        print("   - Device ID matches between device.py and orchestrator.py")

if __name__ == "__main__":
    main()