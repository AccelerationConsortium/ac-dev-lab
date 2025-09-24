#!/usr/bin/env python3
"""
Example client for Railway-hosted OT-2 orchestration server.
This demonstrates how to interact with your cloud-deployed FastAPI server.
"""

import httpx
import json
from typing import Dict, Any, Optional

class RailwayOT2Client:
    """
    Client for Railway-hosted OT-2 orchestration server.
    
    This provides the same ease-of-use as Prefect Cloud with built-in security.
    """
    
    def __init__(self, base_url: str, username: str, password: str):
        """
        Initialize client for Railway-hosted server.
        
        Args:
            base_url: Railway app URL (e.g., "https://your-app.railway.app")
            username: Authentication username
            password: Authentication password
        """
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = None
        
        # HTTP client with automatic HTTPS verification
        self.client = httpx.Client(
            timeout=30.0,
            verify=True,  # Verify SSL certificates
            headers={'User-Agent': 'OT2-Railway-Client/1.0'}
        )
        
        # Authenticate on initialization
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with Railway server and get JWT token."""
        try:
            response = self.client.post(
                f"{self.base_url}/auth/login",
                data={"username": self.username, "password": self.password}
            )
            response.raise_for_status()
            
            auth_data = response.json()
            self.token = auth_data["access_token"]
            
            # Set authorization header for future requests
            self.client.headers['Authorization'] = f'Bearer {self.token}'
            
            print(f"✅ Authenticated with Railway server as {self.username}")
            print(f"🌐 Server: {self.base_url}")
            
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError("Invalid username or password") from e
            else:
                raise ConnectionError(f"Authentication failed: {e.response.text}") from e
        except httpx.RequestError as e:
            raise ConnectionError(f"Cannot connect to Railway server: {e}") from e
    
    def get_server_info(self) -> Dict[str, Any]:
        """Get server information and status."""
        response = self.client.get(f"{self.base_url}/")
        response.raise_for_status()
        return response.json()
    
    def list_available_tasks(self) -> Dict[str, Any]:
        """List all available OT-2 tasks on the server."""
        response = self.client.get(f"{self.base_url}/tasks")
        response.raise_for_status()
        return response.json()
    
    def execute_task(self, task_name: str, **kwargs) -> Any:
        """
        Execute an OT-2 task on the Railway server.
        
        Args:
            task_name: Name of the task to execute
            **kwargs: Task parameters
            
        Returns:
            Task execution result
        """
        try:
            response = self.client.post(
                f"{self.base_url}/execute/{task_name}",
                json=kwargs
            )
            
            # Handle token expiration
            if response.status_code == 401:
                print("🔄 Token expired, re-authenticating...")
                self._authenticate()
                response = self.client.post(
                    f"{self.base_url}/execute/{task_name}",
                    json=kwargs
                )
            
            response.raise_for_status()
            result = response.json()
            
            print(f"✅ Task '{task_name}' executed successfully")
            print(f"⏱️  Execution time: {result.get('execution_time_seconds', 'N/A')}s")
            
            return result["result"]
            
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            if e.response.status_code == 404:
                raise ValueError(f"Task '{task_name}' not found on server")
            elif e.response.status_code == 400:
                raise ValueError(f"Invalid parameters for task '{task_name}': {error_detail}")
            else:
                raise RuntimeError(f"Server error ({e.response.status_code}): {error_detail}")
        except httpx.RequestError as e:
            raise ConnectionError(f"Network error: {e}")
    
    def run_experiment(
        self, 
        experiment_name: str, 
        wells: list, 
        colors: list
    ) -> Dict[str, Any]:
        """
        Run a complete color mixing experiment on Railway.
        
        Args:
            experiment_name: Name for the experiment
            wells: List of well positions (e.g., ["A1", "A2"])
            colors: List of RGB tuples (e.g., [[255,0,0], [0,255,0]])
            
        Returns:
            Complete experiment results
        """
        return self.execute_task(
            "cloud_run_experiment",
            experiment_name=experiment_name,
            wells=wells,
            colors=colors
        )
    
    def health_check(self) -> bool:
        """Check if the Railway server is healthy."""
        try:
            response = self.client.get(f"{self.base_url}/health")
            return response.status_code == 200
        except Exception:
            return False
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

def main():
    """
    Example usage of Railway-hosted OT-2 orchestration.
    
    Replace YOUR_APP_URL with your actual Railway deployment URL.
    """
    
    # Railway deployment URL (replace with your actual URL)
    RAILWAY_URL = "https://your-ot2-app.railway.app"
    
    # Authentication (use environment variables in production)
    USERNAME = "ot2_user" 
    PASSWORD = "demo_password_123"  # Change this in production!
    
    print("=" * 60)
    print("🚀 Railway OT-2 Orchestration Client Demo")
    print("=" * 60)
    print(f"🌐 Server: {RAILWAY_URL}")
    print(f"👤 User: {USERNAME}")
    print("=" * 60)
    
    try:
        with RailwayOT2Client(RAILWAY_URL, USERNAME, PASSWORD) as client:
            
            # Check server status
            print("\n📊 Server Information:")
            server_info = client.get_server_info()
            print(f"  Status: {server_info['status']}")
            print(f"  Hosting: {server_info.get('hosting', 'Unknown')}")
            print(f"  Security: {server_info.get('security', 'Unknown')}")
            
            # List available tasks
            print("\n📋 Available Tasks:")
            tasks_info = client.list_available_tasks()
            for task_name, task_info in tasks_info["tasks"].items():
                print(f"  • {task_name}: {task_info['description']}")
            
            # Execute individual tasks
            print("\n🧪 Executing Individual Tasks:")
            
            # Test color mixing
            mix_result = client.execute_task(
                "cloud_mix_colors",
                r=255, g=128, b=64, well="A1"
            )
            print(f"  Mix result: {mix_result}")
            
            # Test sensor movement
            sensor_result = client.execute_task(
                "cloud_move_sensor",
                well="A1", action="to"
            )
            print(f"  Sensor result: {sensor_result}")
            
            # Test status
            status = client.execute_task("cloud_get_status")
            print(f"  Server status: {status['ot2_status']}")
            
            # Run complete experiment
            print("\n🔬 Running Complete Experiment:")
            experiment_result = client.run_experiment(
                experiment_name="Railway Color Demo",
                wells=["A1", "A2", "A3"],
                colors=[[255, 0, 0], [0, 255, 0], [0, 0, 255]]  # Red, Green, Blue
            )
            
            print(f"  Experiment: {experiment_result['experiment_name']}")
            print(f"  Duration: {experiment_result['duration_seconds']:.2f}s")
            print(f"  Wells processed: {experiment_result['wells_processed']}")
            print(f"  Status: {experiment_result['status']}")
            
            print("\n✅ All Railway operations completed successfully!")
            
    except ValueError as e:
        print(f"\n❌ Authentication error: {e}")
        print("💡 Check your username and password")
        
    except ConnectionError as e:
        print(f"\n❌ Connection error: {e}")
        print("💡 Check your Railway URL and internet connection")
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    main()