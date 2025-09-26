"""
Simple standalone FastAPI orchestration example for OT-2.

This is a minimal working example that can be copied and used independently.
"""

import logging
import time
from typing import Any, Callable, Dict, Optional, Union
import functools
import inspect

try:
    from fastapi import FastAPI, HTTPException, Security, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
    import httpx
except ImportError as e:
    print("ERROR: Required packages not installed")
    print("Install with: pip install fastapi uvicorn httpx")
    raise

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== MINIMAL ORCHESTRATION FRAMEWORK ====================

# Global registry for tasks
_task_registry: Dict[str, Dict[str, Any]] = {}

def task(func_or_name=None):
    """
    Decorator to register a function as a remotely callable task.
    Can be used as @task or @task("custom_name")
    """
    def decorator(func: Callable) -> Callable:
        # Determine task name
        if isinstance(func_or_name, str):
            task_name = func_or_name
        else:
            task_name = func.__name__
            
        sig = inspect.signature(func)
        
        _task_registry[task_name] = {
            'function': func,
            'signature': sig,
            'name': task_name,
            'doc': func.__doc__ or "",
        }
        
        logger.info(f"Registered task: {task_name}")
        return func
    
    # Handle both @task and @task("name") usage
    if callable(func_or_name):
        # Used as @task (without parentheses)
        return decorator(func_or_name)
    else:
        # Used as @task("name") or @task()
        return decorator

def create_device_server(host: str = "0.0.0.0", port: int = 8000):
    """Create a FastAPI server with registered tasks."""
    app = FastAPI(title="OT-2 Device Server", version="1.0.0")
    
    @app.get("/")
    async def root():
        return {
            "message": "OT-2 Device Server",
            "available_tasks": list(_task_registry.keys()),
            "docs": "/docs"
        }
    
    @app.get("/tasks")
    async def list_tasks():
        """List all available tasks."""
        tasks = {}
        for name, info in _task_registry.items():
            params = {}
            for param_name, param in info['signature'].parameters.items():
                params[param_name] = {
                    'type': str(param.annotation) if param.annotation != inspect.Parameter.empty else 'Any',
                    'default': param.default if param.default != inspect.Parameter.empty else None,
                    'required': param.default == inspect.Parameter.empty
                }
            
            tasks[name] = {
                'name': name,
                'doc': info['doc'],
                'parameters': params,
            }
        return tasks
    
    @app.post("/execute/{task_name}")
    async def execute_task(task_name: str, parameters: Dict[str, Any] = {}):
        """Execute a registered task."""
        if task_name not in _task_registry:
            raise HTTPException(
                status_code=404,
                detail=f"Task '{task_name}' not found"
            )
        
        task_info = _task_registry[task_name]
        func = task_info['function']
        
        try:
            bound_args = task_info['signature'].bind(**parameters)
            bound_args.apply_defaults()
            result = func(**bound_args.arguments)
            
            return {
                'task_name': task_name,
                'parameters': parameters,
                'result': result,
                'status': 'success'
            }
            
        except Exception as e:
            logger.error(f"Error executing task {task_name}: {e}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return app

class OrchestratorClient:
    """Simple client for executing tasks remotely."""
    
    def __init__(self, base_url: str, timeout: float = 30.0):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.Client(timeout=timeout)
    
    def execute_task(self, task_name: str, **kwargs) -> Any:
        """Execute a task on the remote device."""
        response = self.client.post(
            f"{self.base_url}/execute/{task_name}",
            json=kwargs
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('status') == 'success':
            return result.get('result')
        else:
            raise RuntimeError(f"Task failed: {result}")
    
    def get_available_tasks(self) -> Dict[str, Any]:
        """Get available tasks from the server."""
        response = self.client.get(f"{self.base_url}/tasks")
        response.raise_for_status()
        return response.json()
    
    def close(self):
        self.client.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

# ==================== OT-2 TASK DEFINITIONS ====================
# These are defined at module level so they're registered on import

@task
def mix_color(R: int, Y: int, B: int, mix_well: str) -> str:
    """
    Simulate mixing colors (replace with real OT-2 code).
    
    Args:
        R: Red component (0-300)
        Y: Yellow component (0-300) 
        B: Blue component (0-300)
        mix_well: Target well (e.g., "A1")
    """
    total = R + Y + B
    if total > 300:
        raise ValueError("Sum of proportions must be <= 300")
    
    # Simulate the mixing process
    logger.info(f"SIMULATED: Mixing R:{R}, Y:{Y}, B:{B} in well {mix_well}")
    time.sleep(1)  # Simulate work
    
    return f"Mixed RGB({R},{Y},{B}) in well {mix_well}"

@task
def move_sensor(well: str, action: str = "to") -> str:
    """
    Simulate sensor movement.
    
    Args:
        well: Target well
        action: "to" (move to well) or "back" (return to home)
    """
    if action == "to":
        logger.info(f"SIMULATED: Moving sensor to well {well}")
        time.sleep(0.5)
        return f"Sensor positioned over well {well}"
    else:
        logger.info("SIMULATED: Moving sensor back to home")
        time.sleep(0.5)
        return "Sensor returned to home position"

@task
def get_status() -> dict:
    """Get robot status."""
    return {
        "status": "ready",
        "mode": "simulation",
        "tasks_available": list(_task_registry.keys()),
        "timestamp": time.time()
    }

# ==================== MAIN FUNCTIONS ====================

def run_device_server():
    """Run the device server."""
    app = create_device_server()
    
    print("\n" + "="*60)
    print("🤖 OT-2 FastAPI Device Server")
    print("="*60)
    print("📡 Server: http://localhost:8000")
    print("📚 API Docs: http://localhost:8000/docs")
    print("📋 Tasks: http://localhost:8000/tasks")
    print(f"🔧 Available Tasks: {list(_task_registry.keys())}")
    print("="*60)
    print("Press Ctrl+C to stop")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)

def run_orchestrator_demo():
    """Run a demo orchestrator."""
    device_url = "http://localhost:8000"
    
    print("\n" + "="*60)
    print("🎨 OT-2 Orchestrator Demo")
    print("="*60)
    print(f"🤖 Target Device: {device_url}")
    print("="*60 + "\n")
    
    try:
        with OrchestratorClient(device_url) as client:
            # Check available tasks
            print("📋 Available tasks:")
            tasks = client.get_available_tasks()
            for name, info in tasks.items():
                print(f"  - {name}: {info.get('doc', 'No description')}")
            print()
            
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
        print("💡 Make sure the device server is running!")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "orchestrator":
        run_orchestrator_demo()
    else:
        run_device_server()

# Tasks are automatically registered when the decorators are processed