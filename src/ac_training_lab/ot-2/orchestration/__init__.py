"""
Lightweight FastAPI-based orchestration framework for OT-2 devices.

This module provides a Prefect-like interface without pydantic v1/v2 conflicts.
"""

from .device_server import DeviceServer, task
from .orchestrator_client import OrchestratorClient

__all__ = ["DeviceServer", "task", "OrchestratorClient"]