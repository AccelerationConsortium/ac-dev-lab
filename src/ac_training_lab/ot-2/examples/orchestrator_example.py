"""
Example orchestrator that controls an OT-2 device remotely.

This demonstrates how to use the OrchestratorClient to execute tasks
on a remote OT-2 device server.
"""

import logging
import time
from typing import Dict, Any

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent / "orchestration"))
from orchestrator_client import OrchestratorClient

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ColorMixingOrchestrator:
    """
    Orchestrator for automated color mixing experiments.
    
    This class provides a high-level interface for conducting color mixing
    experiments on an OT-2 device.
    """
    
    def __init__(self, device_url: str, auth_token: str = None):
        """
        Initialize the orchestrator.
        
        Args:
            device_url: URL of the OT-2 device server (e.g., "http://192.168.1.100:8000")
            auth_token: Optional authentication token
        """
        self.device_url = device_url
        self.client = OrchestratorClient(device_url, auth_token=auth_token)
        
        logger.info(f"Initialized orchestrator for device: {device_url}")
        
        # Check device connectivity
        if not self.client.health_check():
            raise ConnectionError(f"Cannot connect to device at {device_url}")
            
        # Get available tasks
        self.available_tasks = self.client.get_available_tasks()
        logger.info(f"Available tasks: {list(self.available_tasks.keys())}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()
    
    def run_color_mixing_experiment(
        self,
        experiments: list[Dict[str, Any]],
        measurement_delay: float = 5.0
    ) -> list[Dict[str, Any]]:
        """
        Run a series of color mixing experiments.
        
        Args:
            experiments: List of experiment configurations, each containing:
                - R: Red component (0-300)
                - Y: Yellow component (0-300) 
                - B: Blue component (0-300)
                - well: Target well (e.g., "A1")
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
                    R=exp["R"],
                    Y=exp["Y"], 
                    B=exp["B"],
                    mix_well=exp["well"]
                )
                logger.info(f"Mix result: {mix_result}")
                
                # Move sensor to measurement position
                sensor_result = self.client.execute_task(
                    "move_sensor_to_measurement_position",
                    mix_well=exp["well"]
                )
                logger.info(f"Sensor positioning: {sensor_result}")
                
                # Wait for measurement (in real scenario, this would trigger external measurement)
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
        """Get current device status."""
        return self.client.execute_task("get_robot_status")


# Example experiment configurations
EXAMPLE_EXPERIMENTS = [
    {"R": 100, "Y": 50, "B": 30, "well": "A1"},
    {"R": 50, "Y": 100, "B": 50, "well": "A2"},  
    {"R": 30, "Y": 30, "B": 100, "well": "A3"},
    {"R": 80, "Y": 80, "B": 80, "well": "A4"},
]


def main():
    """
    Main function demonstrating orchestrator usage.
    """
    # Device server URL - update this to match your OT-2 device
    device_url = "http://localhost:8000"  # Change to your device's IP
    
    print("\n" + "="*60)
    print("🎨 Color Mixing Orchestrator Example")
    print("="*60)
    print(f"🤖 Device URL: {device_url}")
    print(f"🧪 Experiments: {len(EXAMPLE_EXPERIMENTS)}")
    print("="*60 + "\n")
    
    try:
        # Create orchestrator
        with ColorMixingOrchestrator(device_url) as orchestrator:
            
            # Check device status
            status = orchestrator.get_device_status()
            print(f"📊 Device Status: {status}")
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
        print(f"💡 Make sure the device server is running at {device_url}")
        print(f"   Start it with: python device_example.py")
    except Exception as e:
        print(f"❌ Error: {e}")
        logger.exception("Orchestrator failed")


if __name__ == "__main__":
    main()