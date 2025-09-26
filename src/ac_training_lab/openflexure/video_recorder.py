#!/usr/bin/env python3
"""
OpenFlexure Microscope Video Recording Script

This script provides a simple interface for recording videos from the OpenFlexure microscope
during vibration testing or other experiments. It captures frames via MQTT and saves them
as animated GIF files.

Usage:
    python video_recorder.py --duration 60 --fps 2 --output vibration_test.gif
    
Requirements:
    - OpenFlexure microscope connected and accessible via MQTT
    - Access credentials (configured in my_secrets.py)
"""

import argparse
import sys
import os
from pathlib import Path

# Add the parent directory to sys.path to import microscope_demo_client
sys.path.insert(0, str(Path(__file__).parent))

try:
    from microscope_demo_client import MicroscopeDemo
    try:
        from huggingface.my_secrets import HIVEMQ_BROKER
    except ImportError:
        # For testing purposes when secrets are not available
        HIVEMQ_BROKER = "test_broker"
except ImportError as e:
    print(f"Error importing dependencies: {e}")
    print("Please ensure you have the necessary files and dependencies installed")
    if "--help" not in sys.argv and "-h" not in sys.argv:
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Record video from OpenFlexure microscope",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument(
        "--microscope", 
        default="microscope2",
        choices=["microscope", "microscope2", "deltastagetransmission", "deltastagereflection"],
        help="Which microscope to use"
    )
    
    parser.add_argument(
        "--duration", 
        type=int, 
        default=30,
        help="Recording duration in seconds"
    )
    
    parser.add_argument(
        "--fps", 
        type=int, 
        default=2,
        help="Frames per second for recording"
    )
    
    parser.add_argument(
        "--output", 
        type=str,
        help="Output filename (default: auto-generated with timestamp)"
    )
    
    parser.add_argument(
        "--output-dir",
        type=str,
        default="./recordings",
        help="Output directory for recordings"
    )
    
    parser.add_argument(
        "--access-key",
        type=str,
        required=True,
        help="Access key for microscope authentication"
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.duration < 1 or args.duration > 3600:
        print("Error: Duration must be between 1 and 3600 seconds")
        sys.exit(1)
        
    if args.fps < 1 or args.fps > 30:
        print("Error: FPS must be between 1 and 30")
        sys.exit(1)
    
    print(f"OpenFlexure Microscope Video Recorder")
    print(f"=====================================")
    print(f"Microscope: {args.microscope}")
    print(f"Duration: {args.duration} seconds")
    print(f"FPS: {args.fps}")
    print(f"Output directory: {args.output_dir}")
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Connect to microscope
    try:
        microscope = MicroscopeDemo(
            HIVEMQ_BROKER,
            8883,  # Port
            args.microscope + "clientuser",
            args.access_key,
            args.microscope,
        )
        print(f"Connected to microscope: {args.microscope}")
        
        # Test connection by taking a single image
        print("Testing connection...")
        test_image = microscope.take_image()
        if test_image:
            print("✓ Connection test successful")
        else:
            print("✗ Connection test failed")
            return 1
            
    except Exception as e:
        print(f"Error connecting to microscope: {e}")
        return 1
    
    try:
        # Start recording
        print(f"\nStarting video recording for {args.duration} seconds...")
        print("Press Ctrl+C to stop recording early")
        
        output_filename = args.output
        if output_filename and not output_filename.endswith('.gif'):
            output_filename += '.gif'
            
        video_path = microscope.record_video_for_duration(
            duration_seconds=args.duration,
            fps=args.fps,
            output_filename=output_filename
        )
        
        if video_path:
            print(f"\n✓ Recording completed successfully!")
            print(f"  Video saved to: {video_path}")
            
            # Get file size for user info
            try:
                file_size = os.path.getsize(video_path)
                print(f"  File size: {file_size / 1024 / 1024:.1f} MB")
            except:
                pass
                
            return 0
        else:
            print(f"\n✗ Recording failed")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\nRecording interrupted by user")
        print("Stopping and saving current recording...")
        
        video_path = microscope.stop_video_recording(args.output)
        if video_path:
            print(f"✓ Partial recording saved to: {video_path}")
            return 0
        else:
            print("✗ Failed to save partial recording")
            return 1
            
    except Exception as e:
        print(f"\nError during recording: {e}")
        return 1
        
    finally:
        try:
            microscope.end_connection()
            print("Disconnected from microscope")
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())