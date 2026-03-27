#!/usr/bin/env python3
"""
Hand-Eye Data Collection Helper
Combines AprilTag detection with robot pose to collect hand-eye calibration data

Usage:
1. Move robot to a pose
2. Run: python collect_hand_eye_data.py --robot-pose x y z roll pitch yaw
3. Script will detect AprilTag and save the pose pair
4. Repeat for 5-10 different robot poses
5. Run hand-eye calibration
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime

def get_apriltag_pose(image_path="images/img1_flipped_vertical.png", tag_size=0.03):
    """
    Run AprilTag detection and return pose data
    
    Returns:
        dict: AprilTag pose with position and orientation, or None if failed
    """
    try:
        # Run AprilTag detection
        cmd = [
            sys.executable, "detect_apriltag.py", 
            image_path, 
            "--tag-size", str(tag_size),
            "--save-json", "temp_apriltag_pose.json"
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ AprilTag detection failed: {result.stderr}")
            return None
            
        # Load detection results
        if not os.path.exists("temp_apriltag_pose.json"):
            print("❌ AprilTag detection output not found")
            return None
            
        with open("temp_apriltag_pose.json", 'r') as f:
            data = json.load(f)
            
        # Clean up temp file
        os.remove("temp_apriltag_pose.json")
        
        if not data['detections']:
            print("❌ No AprilTags detected")
            return None
            
        # Get first detection
        detection = data['detections'][0]
        
        return {
            'position': [
                detection['position']['x'],
                detection['position']['y'], 
                detection['position']['z']
            ],
            'orientation': [
                detection['orientation']['roll'],
                detection['orientation']['pitch'],
                detection['orientation']['yaw']
            ]
        }
        
    except Exception as e:
        print(f"❌ Error during AprilTag detection: {e}")
        return None

def load_existing_data(data_file):
    """Load existing calibration data or create new structure"""
    if os.path.exists(data_file):
        with open(data_file, 'r') as f:
            return json.load(f)
    else:
        return {
            'calibration_info': {
                'description': 'Hand-eye calibration data for A1 Mini robot arm',
                'date_created': datetime.now().isoformat(),
                'instructions': [
                    '1. Move robot to various poses while keeping AprilTag visible',
                    '2. Run collect_hand_eye_data.py with robot pose for each position',
                    '3. Collect 5-10 calibration points',
                    '4. Run: python hand_eye_calibration.py calibrate <data_file>'
                ]
            },
            'calibration_points': []
        }

def save_calibration_point(data_file, robot_pose, apriltag_pose):
    """Add new calibration point to data file"""
    data = load_existing_data(data_file)
    
    point_id = len(data['calibration_points']) + 1
    
    new_point = {
        'point_id': point_id,
        'timestamp': datetime.now().isoformat(),
        'robot_pose': {
            'position': robot_pose['position'],
            'orientation': robot_pose['orientation']
        },
        'apriltag_pose': {
            'position': apriltag_pose['position'],
            'orientation': apriltag_pose['orientation']
        }
    }
    
    data['calibration_points'].append(new_point)
    
    with open(data_file, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"✅ Saved calibration point {point_id} to {data_file}")
    print(f"📊 Total points: {len(data['calibration_points'])}")

def show_calibration_status(data_file):
    """Show current calibration data status"""
    if not os.path.exists(data_file):
        print(f"📝 No calibration data found at {data_file}")
        print("   Start collecting data with: python collect_hand_eye_data.py --robot-pose x y z roll pitch yaw")
        return
        
    data = load_existing_data(data_file)
    points = data['calibration_points']
    
    print(f"📊 Calibration Data Status: {data_file}")
    print(f"   Points collected: {len(points)}")
    print(f"   Recommended minimum: 5-10 points")
    
    if len(points) >= 5:
        print("   ✅ Sufficient data for calibration")
        print(f"   Run: python hand_eye_calibration.py calibrate {data_file}")
    else:
        print(f"   ⚠️  Need {5 - len(points)} more points")
        
    print(f"\n📋 Recent points:")
    for point in points[-3:]:  # Show last 3 points
        robot_pos = point['robot_pose']['position']
        tag_pos = point['apriltag_pose']['position']
        print(f"   Point {point['point_id']}: Robot {robot_pos} → Tag {tag_pos}")

def main():
    parser = argparse.ArgumentParser(description='Collect Hand-Eye Calibration Data')
    parser.add_argument('--robot-pose', nargs=6, type=float, metavar=('X', 'Y', 'Z', 'ROLL', 'PITCH', 'YAW'),
                       help='Robot end-effector pose: x y z roll pitch yaw (m, degrees)')
    parser.add_argument('--image', default='images/img1_flipped_vertical.png',
                       help='AprilTag image to use for detection')
    parser.add_argument('--tag-size', type=float, default=0.03,
                       help='AprilTag size in meters (default: 0.03)')
    parser.add_argument('--data-file', default='hand_eye_calibration_data.json',
                       help='Calibration data file')
    parser.add_argument('--status', action='store_true',
                       help='Show calibration data status')
    
    args = parser.parse_args()
    
    if args.status:
        show_calibration_status(args.data_file)
        return
        
    if not args.robot_pose:
        print("❌ Please provide robot pose with --robot-pose x y z roll pitch yaw")
        print("   or use --status to check current calibration data")
        return
        
    # Parse robot pose
    robot_pose = {
        'position': args.robot_pose[:3],  # x, y, z in meters
        'orientation': args.robot_pose[3:]  # roll, pitch, yaw in degrees
    }
    
    print(f"🤖 Robot pose: {robot_pose['position']} m, {robot_pose['orientation']} deg")
    
    # Capture AprilTag pose
    print(f"🏷️  Detecting AprilTag in {args.image}...")
    apriltag_pose = get_apriltag_pose(args.image, args.tag_size)
    
    if apriltag_pose is None:
        print("❌ Failed to detect AprilTag - check image and try again")
        return
        
    print(f"📷 AprilTag pose: {apriltag_pose['position']} m, {apriltag_pose['orientation']} deg")
    
    # Save calibration point
    save_calibration_point(args.data_file, robot_pose, apriltag_pose)
    
    # Show status
    show_calibration_status(args.data_file)

if __name__ == "__main__":
    main()