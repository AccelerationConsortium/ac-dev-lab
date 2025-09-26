"""
Orchestrator client for remote task execution.

This module provides a client for executing tasks on remote OT-2 devices
through the FastAPI device server.
"""

import logging
from typing import Any, Dict, Optional, Union
import json

try:
    import httpx
except ImportError as e:
    raise ImportError(
        "httpx is required for the orchestrator client. Install with: pip install httpx"
    ) from e

logger = logging.getLogger(__name__)


class OrchestratorClient:
    """
    Client for executing tasks on remote OT-2 device servers.
    
    This provides a simple interface for calling device functions remotely,
    similar to how Prefect deployments work but without version conflicts.
    """
    
    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: float = 60.0
    ):
        """
        Initialize the orchestrator client.
        
        Args:
            base_url: Base URL of the device server (e.g., "http://ot2-device:8000")
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        
        # Configure headers
        self.headers = {'Content-Type': 'application/json'}
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
        
        # Create HTTP client
        self.client = httpx.Client(
            timeout=timeout,
            headers=self.headers
        )
        
        logger.info(f"Initialized orchestrator client for {base_url}")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def close(self):
        """Close the HTTP client."""
        self.client.close()
    
    def get_available_tasks(self) -> Dict[str, Any]:
        """
        Get list of available tasks from the device server.
        
        Returns:
            Dictionary of available tasks with their signatures
        """
        try:
            response = self.client.get(f"{self.base_url}/tasks")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to device server: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Device server error: {e.response.text}")
    
    def execute_task(
        self,
        task_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute a task on the remote device.
        
        Args:
            task_name: Name of the task to execute
            parameters: Parameters to pass to the task
            **kwargs: Additional parameters (merged with parameters dict)
            
        Returns:
            Task execution result
            
        Raises:
            ConnectionError: If unable to connect to device server
            ValueError: If task not found or invalid parameters
            RuntimeError: If task execution fails
        """
        # Merge parameters
        params = parameters or {}
        params.update(kwargs)
        
        logger.info(f"Executing task '{task_name}' with parameters: {params}")
        
        try:
            response = self.client.post(
                f"{self.base_url}/execute/{task_name}",
                json=params
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status') == 'success':
                logger.info(f"Task '{task_name}' completed successfully")
                return result.get('result')
            else:
                raise RuntimeError(f"Task execution failed: {result}")
                
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to device server: {e}")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            if e.response.status_code == 404:
                raise ValueError(f"Task '{task_name}' not found on device server")
            elif e.response.status_code == 400:
                raise ValueError(f"Invalid parameters for task '{task_name}': {error_detail}")
            else:
                raise RuntimeError(f"Device server error ({e.response.status_code}): {error_detail}")
    
    def health_check(self) -> bool:
        """
        Check if the device server is healthy and responding.
        
        Returns:
            True if server is healthy, False otherwise
        """
        try:
            response = self.client.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception:
            return False
    
    def __call__(self, task_name: str, **kwargs) -> Any:
        """
        Convenience method to execute a task.
        
        Usage:
            client = OrchestratorClient("http://device:8000")
            result = client("mix_colors", r=255, g=128, b=64)
        """
        return self.execute_task(task_name, **kwargs)


class AsyncOrchestratorClient:
    """
    Async version of the orchestrator client for high-performance scenarios.
    """
    
    def __init__(
        self,
        base_url: str,
        auth_token: Optional[str] = None,
        timeout: float = 60.0
    ):
        self.base_url = base_url.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        
        # Configure headers
        self.headers = {'Content-Type': 'application/json'}
        if auth_token:
            self.headers['Authorization'] = f'Bearer {auth_token}'
        
        # Create async HTTP client
        self.client = httpx.AsyncClient(
            timeout=timeout,
            headers=self.headers
        )
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the async HTTP client."""
        await self.client.aclose()
    
    async def get_available_tasks(self) -> Dict[str, Any]:
        """Async version of get_available_tasks."""
        try:
            response = await self.client.get(f"{self.base_url}/tasks")
            response.raise_for_status()
            return response.json()
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to device server: {e}")
        except httpx.HTTPStatusError as e:
            raise RuntimeError(f"Device server error: {e.response.text}")
    
    async def execute_task(
        self,
        task_name: str,
        parameters: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """Async version of execute_task."""
        # Merge parameters
        params = parameters or {}
        params.update(kwargs)
        
        logger.info(f"Executing task '{task_name}' with parameters: {params}")
        
        try:
            response = await self.client.post(
                f"{self.base_url}/execute/{task_name}",
                json=params
            )
            response.raise_for_status()
            
            result = response.json()
            
            if result.get('status') == 'success':
                logger.info(f"Task '{task_name}' completed successfully")
                return result.get('result')
            else:
                raise RuntimeError(f"Task execution failed: {result}")
                
        except httpx.RequestError as e:
            raise ConnectionError(f"Failed to connect to device server: {e}")
        except httpx.HTTPStatusError as e:
            error_detail = e.response.text
            if e.response.status_code == 404:
                raise ValueError(f"Task '{task_name}' not found on device server")
            elif e.response.status_code == 400:
                raise ValueError(f"Invalid parameters for task '{task_name}': {error_detail}")
            else:
                raise RuntimeError(f"Device server error ({e.response.status_code}): {error_detail}")
    
    async def health_check(self) -> bool:
        """Async health check."""
        try:
            response = await self.client.get(f"{self.base_url}/")
            return response.status_code == 200
        except Exception:
            return False


def create_client(base_url: str, **kwargs) -> OrchestratorClient:
    """
    Convenience function to create an orchestrator client.
    
    Args:
        base_url: Device server URL
        **kwargs: Additional arguments passed to OrchestratorClient
        
    Returns:
        Configured orchestrator client
    """
    return OrchestratorClient(base_url, **kwargs)