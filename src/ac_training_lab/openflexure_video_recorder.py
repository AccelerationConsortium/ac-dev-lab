#!/usr/bin/env python3
"""
OpenFlexure Microscope Video Recording

A simple standalone script to record video for vibration testing.
This script creates mock video frames and saves them as animated GIF files.

Usage:
    python openflexure_video_recorder.py
"""

import datetime
import os
import random
import time
from PIL import Image

# Configuration
DURATION_SECONDS = 30
FPS = 2
OUTPUT_FILENAME = None

# Generate output filename if not specified
if OUTPUT_FILENAME is None:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    OUTPUT_FILENAME = f"openflexure_recording_{timestamp}.gif"

print(f"OpenFlexure Video Recorder")
print(f"Recording {DURATION_SECONDS} seconds at {FPS} FPS...")
print(f"Output: {OUTPUT_FILENAME}")

# Recording loop
frames = []
frame_interval = 1.0 / FPS
end_time = time.time() + DURATION_SECONDS

while time.time() < end_time:
    try:
        # Create a mock frame (since this is standalone without MQTT)
        # In real usage, this would connect to actual microscope camera
        color = (
            random.randint(0, 255),
            random.randint(0, 255), 
            random.randint(0, 255)
        )
        frame = Image.new('RGB', (640, 480), color=color)
        frames.append(frame)
        print(f"Captured frame {len(frames)}")
        time.sleep(frame_interval)
    except Exception as e:
        print(f"Error capturing frame: {e}")
        time.sleep(frame_interval)

# Save video as animated GIF
if frames:
    frame_duration = int(1000 / FPS)  # milliseconds per frame
    frames[0].save(
        OUTPUT_FILENAME,
        save_all=True,
        append_images=frames[1:],
        duration=frame_duration,
        loop=0
    )
    print(f"Video saved: {OUTPUT_FILENAME} ({len(frames)} frames)")
    
    if os.path.exists(OUTPUT_FILENAME):
        file_size = os.path.getsize(OUTPUT_FILENAME) / 1024
        print(f"File size: {file_size:.1f} KB")
else:
    print("No frames captured")

print("Recording complete!")