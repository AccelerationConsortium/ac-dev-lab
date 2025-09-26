#!/usr/bin/env python3
"""
OpenFlexure Microscope Video Recording

A simple script to record video from OpenFlexure microscope for vibration testing.
This captures frames via MQTT and saves them as animated GIF files.

Usage:
    python openflexure_video_recorder.py --duration 30 --fps 2 --output test.gif
"""

import argparse
import base64
import datetime
import json
import os
import sys
import time
import threading
from io import BytesIO
from queue import Queue

try:
    import paho.mqtt.client as mqtt
    from PIL import Image
except ImportError as e:
    print(f"Missing dependencies: {e}")
    print("Install with: pip install paho-mqtt pillow")
    if "--help" not in sys.argv and "-h" not in sys.argv:
        sys.exit(1)


class OpenFlexureVideoRecorder:
    """Simple video recorder for OpenFlexure microscope."""
    
    def __init__(self, host, port, username, password, microscope):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.microscope = microscope
        
        # Video recording state
        self._recording = False
        self._frames = []
        self._recording_thread = None
        
        # MQTT setup
        self.client = mqtt.Client()
        self.client.tls_set()
        self.client.username_pw_set(self.username, self.password)
        self.receiveq = Queue()
        
        def on_message(client, userdata, message):
            received = json.loads(message.payload.decode("utf-8"))
            self.receiveq.put(received)
            
        self.client.on_message = on_message
        self.client.connect(self.host, port=self.port, keepalive=60)
        self.client.loop_start()
        self.client.subscribe(self.microscope + "/return", qos=2)
        
    def take_image(self):
        """Capture a single image from the microscope."""
        command = json.dumps({"command": "take_image"})
        self.client.publish(self.microscope + "/command", payload=command, qos=2, retain=False)
        
        while self.receiveq.empty():
            time.sleep(0.05)
            
        image = self.receiveq.get()
        image_string = image["image"]
        image_bytes = base64.b64decode(image_string)
        return Image.open(BytesIO(image_bytes))
    
    def record_video(self, duration_seconds=30, fps=2, output_filename=None):
        """Record video for specified duration and save as GIF."""
        if output_filename is None:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            output_filename = f"openflexure_recording_{timestamp}.gif"
        
        print(f"Recording {duration_seconds} seconds at {fps} FPS...")
        
        frames = []
        frame_interval = 1.0 / fps
        end_time = time.time() + duration_seconds
        
        while time.time() < end_time:
            try:
                frame = self.take_image()
                frames.append(frame)
                print(f"Captured frame {len(frames)}")
                time.sleep(frame_interval)
            except Exception as e:
                print(f"Error capturing frame: {e}")
                time.sleep(frame_interval)
        
        if frames:
            # Save as animated GIF
            frame_duration = int(1000 / fps)  # milliseconds per frame
            frames[0].save(
                output_filename,
                save_all=True,
                append_images=frames[1:],
                duration=frame_duration,
                loop=0
            )
            print(f"Video saved: {output_filename} ({len(frames)} frames)")
            return output_filename
        else:
            print("No frames captured")
            return None
    
    def disconnect(self):
        """Clean disconnect from microscope."""
        self.client.loop_stop()
        self.client.disconnect()


def main():
    """Command-line interface for video recording."""
    parser = argparse.ArgumentParser(description="Record video from OpenFlexure microscope")
    
    parser.add_argument("--host", default="your_mqtt_broker", help="MQTT broker host")
    parser.add_argument("--port", type=int, default=8883, help="MQTT broker port")
    parser.add_argument("--microscope", default="microscope2", help="Microscope name")
    parser.add_argument("--access-key", required=True, help="Access key for authentication")
    parser.add_argument("--duration", type=int, default=30, help="Recording duration in seconds")
    parser.add_argument("--fps", type=int, default=2, help="Frames per second")
    parser.add_argument("--output", help="Output filename (auto-generated if not specified)")
    
    args = parser.parse_args()
    
    # Connect to microscope
    recorder = OpenFlexureVideoRecorder(
        host=args.host,
        port=args.port,
        username=args.microscope + "clientuser",
        password=args.access_key,
        microscope=args.microscope
    )
    
    try:
        # Record video
        video_path = recorder.record_video(
            duration_seconds=args.duration,
            fps=args.fps,
            output_filename=args.output
        )
        
        if video_path:
            print(f"Recording complete: {video_path}")
            if os.path.exists(video_path):
                file_size = os.path.getsize(video_path) / 1024
                print(f"File size: {file_size:.1f} KB")
        
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        recorder.disconnect()


if __name__ == "__main__":
    main()