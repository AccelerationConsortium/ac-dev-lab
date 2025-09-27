#!/usr/bin/env python3
"""
OpenFlexure Microscope Screen Recording

A simple script to capture screen recordings of the OpenFlexure microscope interface
during vibration testing. This creates timestamped video files for analysis.

Usage:
    python openflexure_video_recorder.py
"""

import datetime
import os
import subprocess
import sys
import time

# Configuration
DURATION_SECONDS = 30
OUTPUT_DIR = "./recordings"
DISPLAY = ":0"  # Default display for Raspberry Pi

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Generate timestamped filename
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
output_file = os.path.join(OUTPUT_DIR, f"openflexure_screen_{timestamp}.mp4")

print(f"OpenFlexure Screen Recorder")
print(f"Recording display {DISPLAY} for {DURATION_SECONDS} seconds...")
print(f"Output: {output_file}")

# Try different screen recording tools available on Raspberry Pi OS
recording_commands = [
    # FFmpeg with X11grab (most common)
    ["ffmpeg", "-f", "x11grab", "-r", "10", "-s", "1920x1080", "-i", DISPLAY, 
     "-t", str(DURATION_SECONDS), "-c:v", "libx264", "-preset", "fast", 
     "-crf", "23", output_file],
    
    # Fallback: FFmpeg with lower resolution
    ["ffmpeg", "-f", "x11grab", "-r", "5", "-s", "1280x720", "-i", DISPLAY,
     "-t", str(DURATION_SECONDS), "-c:v", "libx264", "-preset", "ultrafast", 
     output_file],
     
    # Simple screenshot sequence fallback
    ["bash", "-c", f"for i in $(seq 1 {DURATION_SECONDS}); do scrot {OUTPUT_DIR}/frame_$i.png; sleep 1; done"]
]

success = False

for cmd in recording_commands:
    try:
        print(f"Attempting to record with: {cmd[0]}")
        
        # Start recording
        if cmd[0] == "ffmpeg":
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            print("Recording started... Press Ctrl+C to stop early")
            
            # Wait for completion or user interrupt
            try:
                stdout, stderr = process.communicate(timeout=DURATION_SECONDS + 10)
                if process.returncode == 0:
                    success = True
                    break
                else:
                    print(f"Recording failed with {cmd[0]}: {stderr.decode()}")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"Recording timed out with {cmd[0]}")
                
        else:  # Screenshot sequence fallback
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                success = True
                print("Created screenshot sequence as fallback")
                break
            else:
                print(f"Screenshot sequence failed: {result.stderr}")
                
    except FileNotFoundError:
        print(f"{cmd[0]} not found, trying next method...")
        continue
    except KeyboardInterrupt:
        print("\nRecording interrupted by user")
        if 'process' in locals():
            process.terminate()
        break
    except Exception as e:
        print(f"Error with {cmd[0]}: {e}")
        continue

# Check results
if success and os.path.exists(output_file):
    file_size = os.path.getsize(output_file) / (1024 * 1024)  # MB
    print(f"\nRecording complete!")
    print(f"Video saved: {output_file}")
    print(f"File size: {file_size:.1f} MB")
    print(f"\nTo view the recording:")
    print(f"  vlc {output_file}")
    print(f"  or copy to another device for analysis")
elif success:
    print(f"\nScreenshot sequence created in {OUTPUT_DIR}/")
    print(f"Convert to video with:")
    print(f"  ffmpeg -r 1 -i {OUTPUT_DIR}/frame_%d.png -c:v libx264 {output_file}")
else:
    print(f"\nScreen recording failed. Manual alternatives:")
    print(f"1. Install and use 'recordmydesktop':")
    print(f"   sudo apt install recordmydesktop")
    print(f"   recordmydesktop --width 1280 --height 720 --fps 10 --delay 3")
    print(f"")
    print(f"2. Use 'scrot' for screenshots:")
    print(f"   sudo apt install scrot")
    print(f"   scrot screenshot.png")
    print(f"")
    print(f"3. Use VLC media player (if available):")
    print(f"   Open VLC -> Media -> Convert/Save -> Capture Device")
    print(f"   Set capture mode to 'Desktop' and record")
    
print(f"\nRecording session ended.")