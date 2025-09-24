#!/usr/bin/env python3
"""
Test script to verify FastAPI orchestration works with real communication.
This script tests actual HTTP communication between server and client.
"""

import sys
import time
import threading
import requests
from pathlib import Path

# Add orchestration to path
sys.path.append(str(Path(__file__).parent.parent / "orchestration"))
from device_server import DeviceServer, task
from orchestrator_client import OrchestratorClient

# Test tasks (mock opentrons but test real communication)
@task()
def test_mix_colors(r: int, g: int, b: int, well: str = "A1") -> str:
    """Test color mixing task."""
    time.sleep(0.5)  # Simulate work
    return f"TESTED: Mixed RGB({r},{g},{b}) in well {well}"

@task()
def test_get_status() -> dict:
    """Test status retrieval."""
    return {
        "status": "ready",
        "timestamp": time.time(),
        "test_mode": True
    }

@task()
def test_error_task() -> str:
    """Test error handling."""
    raise ValueError("This is a test error")

def test_server_startup():
    """Test that the server starts correctly."""
    print("🔧 Testing FastAPI server startup...")
    
    server = DeviceServer(port=8001)  # Use different port to avoid conflicts
    
    # Start server in background thread
    server_thread = threading.Thread(target=lambda: server.run(log_level="warning"))
    server_thread.daemon = True
    server_thread.start()
    
    # Wait for server to start
    time.sleep(2)
    
    # Test if server is responding
    try:
        response = requests.get("http://localhost:8001/", timeout=5)
        if response.status_code == 200:
            print("✅ Server started successfully")
            data = response.json()
            print(f"   Available tasks: {data.get('available_tasks', [])}")
            return True
        else:
            print(f"❌ Server responded with status {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Server startup failed: {e}")
        return False

def test_client_communication():
    """Test actual HTTP communication between client and server."""
    print("\n🔧 Testing FastAPI client-server communication...")
    
    try:
        with OrchestratorClient("http://localhost:8001", timeout=10) as client:
            
            # Test health check
            if not client.health_check():
                print("❌ Health check failed")
                return False
            print("✅ Health check passed")
            
            # Test task listing
            tasks = client.get_available_tasks()
            expected_tasks = ["test_mix_colors", "test_get_status", "test_error_task"]
            
            for task_name in expected_tasks:
                if task_name in tasks:
                    print(f"✅ Task '{task_name}' found in registry")
                else:
                    print(f"❌ Task '{task_name}' missing from registry")
                    return False
            
            # Test successful task execution
            print("\n🧪 Testing task execution...")
            
            result = client.execute_task("test_mix_colors", r=255, g=128, b=64, well="B2")
            expected_text = "TESTED: Mixed RGB(255,128,64) in well B2"
            if expected_text in result:
                print(f"✅ Task execution successful: {result}")
            else:
                print(f"❌ Unexpected task result: {result}")
                return False
            
            # Test status task
            status = client.execute_task("test_get_status")
            if isinstance(status, dict) and status.get("test_mode") == True:
                print(f"✅ Status task successful: {status}")
            else:
                print(f"❌ Unexpected status result: {status}")
                return False
            
            # Test error handling
            print("\n🧪 Testing error handling...")
            try:
                client.execute_task("test_error_task")
                print("❌ Error task should have failed but didn't")
                return False
            except Exception as e:
                if "test error" in str(e):
                    print(f"✅ Error handling works: {e}")
                else:
                    print(f"❌ Unexpected error: {e}")
                    return False
            
            # Test invalid task
            try:
                client.execute_task("nonexistent_task")
                print("❌ Invalid task should have failed but didn't")
                return False
            except Exception as e:
                if "not found" in str(e).lower():
                    print(f"✅ Invalid task handling works: {e}")
                else:
                    print(f"❌ Unexpected error for invalid task: {e}")
                    return False
                    
            return True
            
    except Exception as e:
        print(f"❌ Client communication test failed: {e}")
        return False

def main():
    """Run all FastAPI communication tests."""
    print("="*60)
    print("🚀 FastAPI Communication Test Suite")
    print("="*60)
    
    # Test 1: Server startup
    if not test_server_startup():
        print("\n❌ Server startup test failed - aborting remaining tests")
        return False
    
    # Test 2: Client communication
    if not test_client_communication():
        print("\n❌ Client communication test failed")
        return False
    
    print("\n" + "="*60)
    print("✅ ALL FASTAPI TESTS PASSED!")
    print("✅ Real HTTP communication verified between client and server")
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)