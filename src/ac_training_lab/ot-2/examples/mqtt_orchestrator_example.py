"""
Example MQTT orchestrator that controls an OT-2 device remotely.

This demonstrates how to use the MQTTOrchestratorClient to execute tasks
on a remote OT-2 device via MQTT.
"""

import logging
import time
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "orchestration"))
from mqtt_wrapper import MQTTOrchestratorClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MQTTColorMixingOrchestrator:
    """
    MQTT-based orchestrator for automated color mixing experiments.
    """
    
    def __init__(
        self,
        broker_host: str,
        device_id: str,
        broker_port: int = 1883,
        username: str = None,
        password: str = None,
        use_tls: bool = False,
        timeout: float = 30.0
    ):
        """
        Initialize the MQTT orchestrator.
        
        Args:
            broker_host: MQTT broker hostname
            device_id: Target OT-2 device identifier
            broker_port: MQTT broker port
            username: MQTT username (optional)
            password: MQTT password (optional)
            use_tls: Whether to use TLS encryption
            timeout: Command timeout in seconds
        """
        self.broker_host = broker_host
        self.device_id = device_id
        
        self.client = MQTTOrchestratorClient(
            broker_host=broker_host,
            device_id=device_id,
            broker_port=broker_port,
            username=username,
            password=password,
            use_tls=use_tls,
            timeout=timeout
        )
        
        logger.info(f"Initialized MQTT orchestrator for device: {device_id}")
    
    def __enter__(self):
        self.client.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.disconnect()
    
    def run_color_mixing_experiment(
        self,
        experiments: list[Dict[str, Any]],
        measurement_delay: float = 5.0
    ) -> list[Dict[str, Any]]:
        """
        Run a series of color mixing experiments via MQTT.
        
        Args:
            experiments: List of experiment configurations
            measurement_delay: Time to wait for measurement (seconds)
            
        Returns:
            List of experiment results
        """
        results = []
        
        # Ensure robot is homed
        logger.info("Homing robot...")
        self.client.execute_task("home_robot")
        
        for i, exp in enumerate(experiments, 1):
            logger.info(f"Starting experiment {i}/{len(experiments)}: {exp}")
            
            try:
                # Mix the colors
                mix_result = self.client.execute_task(
                    "mix_color",
                    parameters={
                        "R": exp["R"],
                        "Y": exp["Y"], 
                        "B": exp["B"],
                        "mix_well": exp["well"]
                    }
                )
                logger.info(f"Mix result: {mix_result}")
                
                # Move sensor to measurement position
                sensor_result = self.client.execute_task(
                    "move_sensor_to_measurement_position",
                    parameters={"mix_well": exp["well"]}
                )
                logger.info(f"Sensor positioning: {sensor_result}")
                
                # Wait for measurement
                logger.info(f"Waiting {measurement_delay}s for measurement...")
                time.sleep(measurement_delay)
                
                # Move sensor back
                return_result = self.client.execute_task("move_sensor_back")
                logger.info(f"Sensor return: {return_result}")
                
                # Record results
                experiment_result = {
                    "experiment": exp,
                    "mix_result": mix_result,
                    "sensor_result": sensor_result,
                    "return_result": return_result,
                    "status": "success",
                    "timestamp": time.time()
                }
                
                results.append(experiment_result)
                logger.info(f"Experiment {i} completed successfully")
                
            except Exception as e:
                logger.error(f"Experiment {i} failed: {e}")
                experiment_result = {
                    "experiment": exp,
                    "status": "failed",
                    "error": str(e),
                    "timestamp": time.time()
                }
                results.append(experiment_result)
        
        logger.info(f"All experiments completed. {len([r for r in results if r['status'] == 'success'])}/{len(experiments)} successful")
        return results
    
    def get_device_status(self) -> Dict[str, Any]:
        """Get current device status via MQTT."""
        return self.client.execute_task("get_robot_status")


# Example experiment configurations (same as FastAPI example)
EXAMPLE_EXPERIMENTS = [
    {"R": 100, "Y": 50, "B": 30, "well": "A1"},
    {"R": 50, "Y": 100, "B": 50, "well": "A2"},  
    {"R": 30, "Y": 30, "B": 100, "well": "A3"},
    {"R": 80, "Y": 80, "B": 80, "well": "A4"},
]


def main():
    """
    Main function demonstrating MQTT orchestrator usage.
    """
    # MQTT Configuration - update these values for your setup
    BROKER_HOST = "localhost"  # Update to your MQTT broker
    BROKER_PORT = 1883
    DEVICE_ID = "ot2-device-001"  # Must match the device server
    USERNAME = None  # Set if your broker requires authentication
    PASSWORD = None  # Set if your broker requires authentication
    USE_TLS = False  # Set to True for secure connections
    
    print("\n" + "="*60)
    print("🎨 MQTT Color Mixing Orchestrator Example")
    print("="*60)
    print(f"📡 MQTT Broker: {BROKER_HOST}:{BROKER_PORT}")
    print(f"🤖 Target Device: {DEVICE_ID}")
    print(f"🧪 Experiments: {len(EXAMPLE_EXPERIMENTS)}")
    print(f"🔒 TLS: {'Enabled' if USE_TLS else 'Disabled'}")
    print("="*60 + "\n")
    
    try:
        # Create orchestrator
        with MQTTColorMixingOrchestrator(
            broker_host=BROKER_HOST,
            device_id=DEVICE_ID,
            broker_port=BROKER_PORT,
            username=USERNAME,
            password=PASSWORD,
            use_tls=USE_TLS,
            timeout=30.0
        ) as orchestrator:
            
            # Check device status
            print("📊 Checking device status...")
            status = orchestrator.get_device_status()
            print(f"Device Status: {status}")
            print()
            
            # Run experiments
            print("🚀 Starting experiments...")
            results = orchestrator.run_color_mixing_experiment(
                EXAMPLE_EXPERIMENTS,
                measurement_delay=2.0  # Shorter delay for demo
            )
            
            # Display results
            print("\n" + "="*60)
            print("📈 EXPERIMENT RESULTS")
            print("="*60)
            
            for i, result in enumerate(results, 1):
                status_icon = "✅" if result["status"] == "success" else "❌"
                exp = result["experiment"]
                print(f"{status_icon} Experiment {i}: RGB({exp['R']}, {exp['Y']}, {exp['B']}) → {exp['well']}")
                if result["status"] == "failed":
                    print(f"   Error: {result['error']}")
            
            successful = len([r for r in results if r["status"] == "success"])
            print(f"\n🎯 Success Rate: {successful}/{len(results)} ({100*successful/len(results):.1f}%)")
            
    except ConnectionError as e:
        print(f"❌ Connection Error: {e}")
        print(f"💡 Make sure:")
        print(f"   - MQTT broker is running at {BROKER_HOST}:{BROKER_PORT}")
        print(f"   - Device server is running with device ID: {DEVICE_ID}")
        print(f"   - Network connectivity is working")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("MQTT Orchestrator failed")


if __name__ == "__main__":
    main()