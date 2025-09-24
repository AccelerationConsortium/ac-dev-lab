#!/usr/bin/env python3
"""
Test script to verify MQTT orchestration works with real communication.
This script tests actual MQTT communication using HiveMQ Cloud.
"""

import sys
import time
import threading
import json
from pathlib import Path

# Add orchestration to path
sys.path.append(str(Path(__file__).parent.parent / "orchestration"))
from mqtt_wrapper import MQTTDeviceServer, MQTTOrchestratorClient, mqtt_task

# HiveMQ Cloud test credentials (public for demo purposes)
HIVEMQ_USERNAME = "sgbaird"
HIVEMQ_PASSWORD = "D.Pq5gYtejYbU#L"
HIVEMQ_HOST = "248cc294c37642359297f75b7b023374.s2.eu.hivemq.cloud"
PORT = 8883

# Test device ID
TEST_DEVICE_ID = f"ot2-test-{int(time.time())}"  # Unique ID to avoid conflicts

# Test tasks (mock opentrons but test real MQTT communication)
@mqtt_task()
def test_mix_colors(r: int, g: int, b: int, well: str = "A1") -> str:
    """Test color mixing task."""
    time.sleep(0.5)  # Simulate work
    return f"MQTT_TESTED: Mixed RGB({r},{g},{b}) in well {well}"

@mqtt_task()
def test_get_status() -> dict:
    """Test status retrieval."""
    return {
        "status": "ready",
        "timestamp": time.time(),
        "test_mode": True,
        "device_id": TEST_DEVICE_ID
    }

@mqtt_task()
def test_error_task() -> str:
    """Test error handling."""
    raise ValueError("This is a test MQTT error")

def test_mqtt_server_startup():
    """Test that the MQTT server starts and connects correctly."""
    print("🔧 Testing MQTT server startup...")
    
    try:
        server = MQTTDeviceServer(
            broker_host=HIVEMQ_HOST,
            broker_port=PORT,
            device_id=TEST_DEVICE_ID,
            username=HIVEMQ_USERNAME,
            password=HIVEMQ_PASSWORD,
            use_tls=True
        )
        
        # Start server in background thread
        server_thread = threading.Thread(target=server.start)
        server_thread.daemon = True
        server_thread.start()
        
        # Wait for connection
        time.sleep(5)
        
        if server.connected:
            print("✅ MQTT server connected to HiveMQ Cloud")
            print(f"   Device ID: {TEST_DEVICE_ID}")
            print(f"   Broker: {HIVEMQ_HOST}:{PORT}")
            return server
        else:
            print("❌ MQTT server failed to connect")
            return None
            
    except Exception as e:
        print(f"❌ MQTT server startup failed: {e}")
        return None

def test_mqtt_client_communication(server):
    """Test actual MQTT communication between client and server."""
    print("\n🔧 Testing MQTT client-server communication...")
    
    try:
        client = MQTTOrchestratorClient(
            broker_host=HIVEMQ_HOST,
            broker_port=PORT,
            device_id=TEST_DEVICE_ID,
            username=HIVEMQ_USERNAME,
            password=HIVEMQ_PASSWORD,
            use_tls=True,
            timeout=15.0  # Longer timeout for cloud MQTT
        )
        
        # Connect client
        client.connect()
        time.sleep(2)  # Wait for connection to stabilize
        
        if not client.connected:
            print("❌ MQTT client failed to connect")
            return False
            
        print("✅ MQTT client connected to HiveMQ Cloud")
        
        # Test successful task execution
        print("\n🧪 Testing MQTT task execution...")
        
        result = client.execute_task("test_mix_colors", r=255, g=128, b=64, well="C3")
        expected_text = "MQTT_TESTED: Mixed RGB(255,128,64) in well C3"
        if expected_text in result:
            print(f"✅ MQTT task execution successful: {result}")
        else:
            print(f"❌ Unexpected MQTT task result: {result}")
            client.disconnect()
            return False
        
        # Test status task
        status = client.execute_task("test_get_status")
        if isinstance(status, dict) and status.get("test_mode") == True:
            print(f"✅ MQTT status task successful: {status}")
        else:
            print(f"❌ Unexpected MQTT status result: {status}")
            client.disconnect()
            return False
        
        # Test error handling
        print("\n🧪 Testing MQTT error handling...")
        try:
            client.execute_task("test_error_task")
            print("❌ MQTT error task should have failed but didn't")
            client.disconnect()
            return False
        except Exception as e:
            if "test MQTT error" in str(e):
                print(f"✅ MQTT error handling works: {e}")
            else:
                print(f"❌ Unexpected MQTT error: {e}")
                client.disconnect()
                return False
        
        # Test invalid task
        try:
            client.execute_task("nonexistent_mqtt_task")
            print("❌ Invalid MQTT task should have failed but didn't")
            client.disconnect()
            return False
        except Exception as e:
            if "not found" in str(e).lower():
                print(f"✅ Invalid MQTT task handling works: {e}")
            else:
                print(f"❌ Unexpected error for invalid MQTT task: {e}")
                client.disconnect()
                return False
        
        # Clean up
        client.disconnect()
        return True
        
    except Exception as e:
        print(f"❌ MQTT client communication test failed: {e}")
        return False

def test_multiple_message_exchange():
    """Test multiple rapid message exchanges to verify reliability."""
    print("\n🔧 Testing multiple MQTT message exchanges...")
    
    try:
        with MQTTOrchestratorClient(
            broker_host=HIVEMQ_HOST,
            broker_port=PORT,
            device_id=TEST_DEVICE_ID,
            username=HIVEMQ_USERNAME,
            password=HIVEMQ_PASSWORD,
            use_tls=True,
            timeout=20.0
        ) as client:
            
            # Execute multiple tasks in sequence
            test_cases = [
                {"r": 100, "g": 50, "b": 30, "well": "A1"},
                {"r": 200, "g": 100, "b": 60, "well": "A2"},
                {"r": 150, "g": 75, "b": 45, "well": "A3"},
            ]
            
            results = []
            for i, test_case in enumerate(test_cases, 1):
                print(f"   Test {i}: {test_case}")
                result = client.execute_task("test_mix_colors", **test_case)
                results.append(result)
                print(f"   Result: {result}")
                time.sleep(1)  # Brief pause between tests
            
            # Verify all results
            if len(results) == len(test_cases):
                print("✅ Multiple message exchange test passed")
                return True
            else:
                print(f"❌ Expected {len(test_cases)} results, got {len(results)}")
                return False
                
    except Exception as e:
        print(f"❌ Multiple message exchange test failed: {e}")
        return False

def main():
    """Run all MQTT communication tests."""
    print("="*60)
    print("🚀 MQTT Communication Test Suite (HiveMQ Cloud)")
    print("="*60)
    print(f"🌐 Testing with HiveMQ Cloud: {HIVEMQ_HOST}")
    print(f"🔐 Using TLS encryption on port {PORT}")
    print(f"🏷️  Device ID: {TEST_DEVICE_ID}")
    print("="*60)
    
    # Test 1: Server startup
    server = test_mqtt_server_startup()
    if not server:
        print("\n❌ MQTT server startup test failed - aborting remaining tests")
        return False
    
    # Test 2: Client communication
    if not test_mqtt_client_communication(server):
        print("\n❌ MQTT client communication test failed")
        server.stop()
        return False
    
    # Test 3: Multiple message exchange
    if not test_multiple_message_exchange():
        print("\n❌ Multiple message exchange test failed")
        server.stop()
        return False
    
    # Clean up
    server.stop()
    
    print("\n" + "="*60)
    print("✅ ALL MQTT TESTS PASSED!")
    print("✅ Real MQTT communication verified with HiveMQ Cloud")
    print("✅ TLS encryption and authentication working")
    print("="*60)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)