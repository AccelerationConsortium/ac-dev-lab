"""
Device server implementation using FastAPI.

This module provides a lightweight alternative to Prefect that is compatible
with the Opentrons package (avoiding pydantic version conflicts).
"""

import asyncio
import functools
import inspect
import logging
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from fastapi import FastAPI, HTTPException, Security, Depends, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    import uvicorn
except ImportError as e:
    raise ImportError(
        "FastAPI and uvicorn are required. Install with: pip install fastapi uvicorn"
    ) from e

# Global registry for tasks
_task_registry: Dict[str, Dict[str, Any]] = {}

# Security (optional)
security = HTTPBearer(auto_error=False)

logger = logging.getLogger(__name__)


def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """
    Optional token verification. Override this function to implement
    your own authentication logic.
    """
    # For development, we'll skip token verification
    # In production, implement proper token validation here
    return True


def task(name: Optional[str] = None):
    """
    Decorator to register a function as a remotely callable task.
    
    Usage:
        @task
        def mix_colors(r: int, g: int, b: int) -> str:
            return f"Mixed RGB({r}, {g}, {b})"
    """
    def decorator(func: Callable) -> Callable:
        task_name = name or func.__name__
        
        # Get function signature for validation
        sig = inspect.signature(func)
        
        # Register the task
        _task_registry[task_name] = {
            'function': func,
            'signature': sig,
            'name': task_name,
            'doc': func.__doc__ or "",
            'is_async': inspect.iscoroutinefunction(func)
        }
        
        logger.info(f"Registered task: {task_name}")
        
        # Return the original function unchanged
        return func
    
    return decorator


class DeviceServer:
    """
    FastAPI-based device server that exposes registered tasks as HTTP endpoints.
    """
    
    def __init__(
        self, 
        title: str = "OT-2 Device Server",
        description: str = "Lightweight orchestration server for OT-2 devices",
        version: str = "1.0.0",
        host: str = "0.0.0.0",
        port: int = 8000,
        require_auth: bool = False
    ):
        self.app = FastAPI(
            title=title,
            description=description,
            version=version
        )
        self.host = host
        self.port = port
        self.require_auth = require_auth
        
        self._setup_routes()
    
    def _setup_routes(self):
        """Setup FastAPI routes for all registered tasks."""
        
        @self.app.get("/")
        async def root():
            return {
                "message": "OT-2 Device Server",
                "available_tasks": list(_task_registry.keys()),
                "docs": "/docs"
            }
        
        @self.app.get("/tasks")
        async def list_tasks():
            """List all available tasks with their signatures."""
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
                    'is_async': info['is_async']
                }
            return tasks
        
        @self.app.post("/execute/{task_name}")
        async def execute_task(
            task_name: str,
            parameters: Dict[str, Any] = {},
            authenticated: bool = Depends(verify_token) if self.require_auth else None
        ):
            """Execute a registered task with given parameters."""
            
            if task_name not in _task_registry:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Task '{task_name}' not found. Available tasks: {list(_task_registry.keys())}"
                )
            
            task_info = _task_registry[task_name]
            func = task_info['function']
            
            try:
                # Bind parameters to function signature for validation
                bound_args = task_info['signature'].bind(**parameters)
                bound_args.apply_defaults()
                
                # Execute the function
                if task_info['is_async']:
                    result = await func(**bound_args.arguments)
                else:
                    result = func(**bound_args.arguments)
                
                return {
                    'task_name': task_name,
                    'parameters': parameters,
                    'result': result,
                    'status': 'success'
                }
                
            except TypeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid parameters for task '{task_name}': {str(e)}"
                )
            except Exception as e:
                logger.error(f"Error executing task {task_name}: {str(e)}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Error executing task '{task_name}': {str(e)}"
                )
    
    def run(self, **kwargs):
        """
        Run the device server.
        
        Args:
            **kwargs: Additional arguments passed to uvicorn.run()
        """
        config = {
            'host': self.host,
            'port': self.port,
            'log_level': 'info',
            **kwargs
        }
        
        logger.info(f"Starting device server on {self.host}:{self.port}")
        logger.info(f"Registered tasks: {list(_task_registry.keys())}")
        
        uvicorn.run(self.app, **config)
    
    def get_app(self):
        """Return the FastAPI app instance for advanced usage."""
        return self.app


# Convenience function for quick server setup
def create_server(**kwargs) -> DeviceServer:
    """Create and return a DeviceServer instance."""
    return DeviceServer(**kwargs)