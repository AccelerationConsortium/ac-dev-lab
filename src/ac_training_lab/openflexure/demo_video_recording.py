#!/usr/bin/env python3
"""
OpenFlexure Microscope Video Recording Demo

This demo script shows how to use the video recording functionality
with the OpenFlexure microscope for capturing video feeds during experiments.

This is a simple demonstration that can be adapted for vibration testing
or other experimental needs.
"""

import time
import os
from microscope_demo_client import MicroscopeDemo

# Example configuration - replace with your actual values
DEMO_CONFIG = {
    "host": "your_mqtt_broker",  # Replace with actual MQTT broker
    "port": 8883,
    "microscope": "microscope2",  # Choose: microscope, microscope2, etc.
    "access_key": "your_access_key",  # Replace with actual access key
}

def demo_basic_video_recording():
    """Basic demonstration of video recording functionality."""
    print("OpenFlexure Video Recording Demo")
    print("===============================\n")
    
    try:
        # Connect to microscope
        print(f"Connecting to microscope '{DEMO_CONFIG['microscope']}'...")
        microscope = MicroscopeDemo(
            DEMO_CONFIG["host"],
            DEMO_CONFIG["port"],
            DEMO_CONFIG["microscope"] + "clientuser",
            DEMO_CONFIG["access_key"],
            DEMO_CONFIG["microscope"],
        )
        print("✓ Connected successfully\n")
        
        # Test single image capture
        print("Testing single image capture...")
        test_image = microscope.take_image()
        if test_image:
            print(f"✓ Image captured: {test_image.size}")
        else:
            print("✗ Failed to capture test image")
            return
            
        print("\n" + "="*50)
        print("VIDEO RECORDING DEMONSTRATIONS")
        print("="*50)
        
        # Demo 1: Fixed duration recording
        print("\nDemo 1: Recording for fixed duration (10 seconds)")
        print("-" * 50)
        
        video_path = microscope.record_video_for_duration(
            duration_seconds=10,
            fps=2,
            output_filename="demo_fixed_duration.gif"
        )
        
        if video_path:
            print(f"✓ Demo 1 completed: {video_path}")
            print(f"  File size: {os.path.getsize(video_path) / 1024:.1f} KB")
        else:
            print("✗ Demo 1 failed")
        
        # Demo 2: Manual start/stop recording
        print(f"\nDemo 2: Manual start/stop recording")
        print("-" * 50)
        
        print("Starting recording...")
        microscope.start_video_recording(fps=3, output_dir="./demo_recordings")
        
        print("Recording for 5 seconds...")
        time.sleep(5)
        
        print("Stopping recording...")
        video_path = microscope.stop_video_recording("demo_manual_control.gif")
        
        if video_path:
            print(f"✓ Demo 2 completed: {video_path}")
            print(f"  File size: {os.path.getsize(video_path) / 1024:.1f} KB")
        else:
            print("✗ Demo 2 failed")
        
        # Demo 3: High-frequency recording (for vibration testing)
        print(f"\nDemo 3: High-frequency recording (vibration testing simulation)")
        print("-" * 50)
        
        print("Simulating vibration test recording at higher FPS...")
        video_path = microscope.record_video_for_duration(
            duration_seconds=8,
            fps=5,  # Higher FPS for capturing vibration effects
            output_filename="demo_vibration_test.gif"
        )
        
        if video_path:
            print(f"✓ Demo 3 completed: {video_path}")
            print(f"  File size: {os.path.getsize(video_path) / 1024:.1f} KB")
        else:
            print("✗ Demo 3 failed")
        
        print(f"\n" + "="*50)
        print("DEMONSTRATION COMPLETE")
        print("="*50)
        print("All demo recordings have been saved to the current directory.")
        print("You can view them with any GIF viewer or web browser.")
        
    except Exception as e:
        print(f"Error during demonstration: {e}")
        print("\nNote: This demo requires:")
        print("- A running OpenFlexure microscope")
        print("- Proper MQTT broker configuration")
        print("- Valid access credentials")
        
    finally:
        try:
            microscope.end_connection()
            print("\n✓ Disconnected from microscope")
        except:
            pass

def demo_with_mock_data():
    """Demo using mock data for testing without hardware."""
    print("Mock Video Recording Demo (No Hardware Required)")
    print("=" * 50)
    
    from PIL import Image
    import random
    
    # Create a mock microscope class for demonstration
    class MockMicroscope:
        def __init__(self):
            self._recording = False
            self._frames = []
            
        def take_image(self):
            # Generate a random colored image as mock data
            color = (
                random.randint(0, 255),
                random.randint(0, 255), 
                random.randint(0, 255)
            )
            return Image.new('RGB', (640, 480), color=color)
            
        def record_video_for_duration(self, duration_seconds, fps, output_filename):
            print(f"Mock recording: {duration_seconds}s at {fps} FPS")
            
            # Simulate frame capture
            frames = []
            for i in range(duration_seconds * fps):
                frame = self.take_image()
                frames.append(frame)
                print(f"  Captured mock frame {i+1}/{duration_seconds * fps}")
                
            # Save as GIF
            if frames:
                frames[0].save(
                    output_filename,
                    save_all=True,
                    append_images=frames[1:],
                    duration=int(1000/fps),
                    loop=0
                )
                return output_filename
            return None
    
    # Run mock demo
    mock_microscope = MockMicroscope()
    
    print("Creating mock video recording...")
    video_path = mock_microscope.record_video_for_duration(
        duration_seconds=3,
        fps=2,
        output_filename="mock_demo.gif"
    )
    
    if video_path and os.path.exists(video_path):
        print(f"✓ Mock demo completed: {video_path}")
        print(f"  File size: {os.path.getsize(video_path) / 1024:.1f} KB")
    else:
        print("✗ Mock demo failed")

if __name__ == "__main__":
    import sys
    
    print("OpenFlexure Microscope Video Recording Demo")
    print("Choose demo type:")
    print("1. Hardware demo (requires actual microscope)")
    print("2. Mock demo (no hardware required)")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        print("\nStarting hardware demo...")
        print("Note: Make sure to update DEMO_CONFIG with your actual connection details")
        demo_basic_video_recording()
    elif choice == "2":
        print("\nStarting mock demo...")
        demo_with_mock_data()
    else:
        print("Invalid choice. Exiting.")
        sys.exit(1)