#!/usr/bin/env python3
"""
Hand-Eye Calibration for A1 Mini Robot Arm
Calculates the transformation between camera and end-effector coordinates

This script performs hand-eye calibration to determine the fixed transformation
between the camera and the robot arm's end-effector. Once calibrated, you can
convert AprilTag positions from camera coordinates to robot arm coordinates.

Usage:
1. Move robot to different poses while keeping AprilTag in view
2. For each pose, record: robot pose + AprilTag detection
3. Run calibration to compute camera-to-end-effector transformation
4. Use transformation to convert future detections to robot coordinates
"""

import numpy as np
import cv2
import json
import yaml
from scipy.spatial.transform import Rotation as R
from scipy.optimize import least_squares
import argparse
from datetime import datetime

class HandEyeCalibration:
    def __init__(self):
        self.calibration_data = []
        self.camera_to_ee_transform = None
        
    def add_calibration_point(self, robot_pose, apriltag_pose):
        """
        Add a calibration data point
        
        Args:
            robot_pose: dict with keys 'position' [x,y,z] and 'orientation' [roll,pitch,yaw] 
                       in robot base coordinates (meters, degrees)
            apriltag_pose: dict with keys 'position' [x,y,z] and 'orientation' [roll,pitch,yaw]
                          in camera coordinates (meters, degrees)
        """
        # Convert orientations to rotation matrices
        robot_rot = R.from_euler('xyz', robot_pose['orientation'], degrees=True).as_matrix()
        camera_rot = R.from_euler('xyz', apriltag_pose['orientation'], degrees=True).as_matrix()
        
        calibration_point = {
            'robot_position': np.array(robot_pose['position']),
            'robot_rotation': robot_rot,
            'camera_position': np.array(apriltag_pose['position']), 
            'camera_rotation': camera_rot,
            'timestamp': datetime.now().isoformat()
        }
        
        self.calibration_data.append(calibration_point)
        print(f"✅ Added calibration point {len(self.calibration_data)}")
        
    def load_calibration_data(self, json_file):
        """Load calibration data from JSON file"""
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        for point in data['calibration_points']:
            robot_pose = {
                'position': point['robot_pose']['position'],
                'orientation': point['robot_pose']['orientation']
            }
            apriltag_pose = {
                'position': point['apriltag_pose']['position'], 
                'orientation': point['apriltag_pose']['orientation']
            }
            self.add_calibration_point(robot_pose, apriltag_pose)
            
        print(f"📂 Loaded {len(self.calibration_data)} calibration points")
        
    def save_calibration_data(self, json_file):
        """Save calibration data to JSON file"""
        data = {
            'calibration_info': {
                'description': 'Hand-eye calibration data for A1 Mini robot arm',
                'date_created': datetime.now().isoformat(),
                'num_points': len(self.calibration_data)
            },
            'calibration_points': []
        }
        
        for i, point in enumerate(self.calibration_data):
            # Convert rotation matrices back to euler angles for storage
            robot_euler = R.from_matrix(point['robot_rotation']).as_euler('xyz', degrees=True)
            camera_euler = R.from_matrix(point['camera_rotation']).as_euler('xyz', degrees=True)
            
            data['calibration_points'].append({
                'point_id': i + 1,
                'timestamp': point['timestamp'],
                'robot_pose': {
                    'position': point['robot_position'].tolist(),
                    'orientation': robot_euler.tolist()
                },
                'apriltag_pose': {
                    'position': point['camera_position'].tolist(),
                    'orientation': camera_euler.tolist()
                }
            })
            
        with open(json_file, 'w') as f:
            json.dump(data, f, indent=2)
            
        print(f"💾 Saved calibration data to {json_file}")
        
    def calibrate_hand_eye(self):
        """
        Perform hand-eye calibration using AX=XB formulation
        
        A = robot end-effector motion
        B = camera motion (inverse of AprilTag motion)
        X = camera-to-end-effector transformation (what we want to find)
        
        Returns:
            success: bool indicating if calibration succeeded
            transform: 4x4 transformation matrix from camera to end-effector
        """
        if len(self.calibration_data) < 3:
            print("❌ Need at least 3 calibration points")
            return False, None
            
        print(f"🔄 Computing hand-eye calibration with {len(self.calibration_data)} points...")
        
        # Use OpenCV's hand-eye calibration
        robot_rotations = []
        robot_translations = []
        camera_rotations = []
        camera_translations = []
        
        # Use first pose as reference
        ref_robot_rot = self.calibration_data[0]['robot_rotation']
        ref_robot_pos = self.calibration_data[0]['robot_position']
        ref_camera_rot = self.calibration_data[0]['camera_rotation']
        ref_camera_pos = self.calibration_data[0]['camera_position']
        
        for i in range(1, len(self.calibration_data)):
            data = self.calibration_data[i]
            
            # Robot motion from reference to current pose
            robot_rot_rel = data['robot_rotation'] @ ref_robot_rot.T
            robot_trans_rel = data['robot_position'] - ref_robot_pos
            
            # Camera motion (inverse of AprilTag motion)
            camera_rot_rel = ref_camera_rot @ data['camera_rotation'].T
            camera_trans_rel = ref_camera_pos - data['camera_position']
            
            robot_rotations.append(robot_rot_rel)
            robot_translations.append(robot_trans_rel.reshape(-1, 1))
            camera_rotations.append(camera_rot_rel)
            camera_translations.append(camera_trans_rel.reshape(-1, 1))
            
        # Perform calibration
        try:
            R_cam2ee, t_cam2ee = cv2.calibrateHandEye(
                robot_rotations, robot_translations,
                camera_rotations, camera_translations,
                method=cv2.CALIB_HAND_EYE_TSAI
            )
            
            # Create 4x4 transformation matrix
            self.camera_to_ee_transform = np.eye(4)
            self.camera_to_ee_transform[:3, :3] = R_cam2ee
            self.camera_to_ee_transform[:3, 3] = t_cam2ee.flatten()
            
            print("✅ Hand-eye calibration successful!")
            return True, self.camera_to_ee_transform
            
        except Exception as e:
            print(f"❌ Hand-eye calibration failed: {e}")
            return False, None
            
    def save_transform(self, yaml_file):
        """Save camera-to-end-effector transformation to YAML"""
        if self.camera_to_ee_transform is None:
            print("❌ No calibration to save")
            return
            
        # Extract rotation and translation
        R_cam2ee = self.camera_to_ee_transform[:3, :3]
        t_cam2ee = self.camera_to_ee_transform[:3, 3]
        
        # Convert rotation to euler angles
        euler_cam2ee = R.from_matrix(R_cam2ee).as_euler('xyz', degrees=True)
        
        transform_data = {
            'hand_eye_calibration': {
                'description': 'Camera to end-effector transformation',
                'calibration_date': datetime.now().isoformat(),
                'num_calibration_points': len(self.calibration_data),
                'transformation_matrix': self.camera_to_ee_transform.tolist(),
                'translation': {
                    'x': float(t_cam2ee[0]),
                    'y': float(t_cam2ee[1]), 
                    'z': float(t_cam2ee[2])
                },
                'rotation_euler_degrees': {
                    'roll': float(euler_cam2ee[0]),
                    'pitch': float(euler_cam2ee[1]),
                    'yaw': float(euler_cam2ee[2])
                }
            }
        }
        
        with open(yaml_file, 'w') as f:
            yaml.dump(transform_data, f, default_flow_style=False)
            
        print(f"💾 Saved transformation to {yaml_file}")
        
    def transform_pose(self, camera_pose):
        """
        Transform AprilTag pose from camera coordinates to end-effector coordinates
        
        Args:
            camera_pose: dict with 'position' and 'orientation' in camera coordinates
            
        Returns:
            ee_pose: dict with 'position' and 'orientation' in end-effector coordinates
        """
        if self.camera_to_ee_transform is None:
            print("❌ No hand-eye calibration available")
            return None
            
        # Convert camera pose to homogeneous transformation
        camera_pos = np.array(camera_pose['position'])
        camera_rot = R.from_euler('xyz', camera_pose['orientation'], degrees=True).as_matrix()
        
        T_camera = np.eye(4)
        T_camera[:3, :3] = camera_rot
        T_camera[:3, 3] = camera_pos
        
        # Transform to end-effector coordinates
        T_ee = self.camera_to_ee_transform @ T_camera
        
        # Extract position and orientation
        ee_pos = T_ee[:3, 3]
        ee_rot = R.from_matrix(T_ee[:3, :3]).as_euler('xyz', degrees=True)
        
        return {
            'position': ee_pos.tolist(),
            'orientation': ee_rot.tolist()
        }

def create_example_data():
    """Create example calibration data file"""
    example_data = {
        'calibration_info': {
            'description': 'Example hand-eye calibration data for A1 Mini robot arm',
            'instructions': [
                '1. Move robot to various poses while keeping AprilTag visible',
                '2. Record robot pose (x,y,z,roll,pitch,yaw) in base coordinates',
                '3. Record AprilTag pose from camera detection',
                '4. Repeat for 5-10 different robot poses',
                '5. Run: python hand_eye_calibration.py calibrate example_data.json'
            ]
        },
        'calibration_points': [
            {
                'point_id': 1,
                'robot_pose': {
                    'position': [0.15, 0.0, 0.25],  # Robot end-effector position (m)
                    'orientation': [0.0, 0.0, 0.0]  # Robot end-effector orientation (deg)
                },
                'apriltag_pose': {
                    'position': [-0.02, 0.01, 0.12],  # AprilTag in camera coordinates (m)  
                    'orientation': [0.0, 0.0, 0.0]    # AprilTag orientation (deg)
                }
            },
            {
                'point_id': 2, 
                'robot_pose': {
                    'position': [0.12, 0.05, 0.22],
                    'orientation': [10.0, 5.0, -15.0]
                },
                'apriltag_pose': {
                    'position': [-0.05, 0.03, 0.15],
                    'orientation': [8.0, 3.0, -12.0]
                }
            }
        ]
    }
    
    with open('example_hand_eye_data.json', 'w') as f:
        json.dump(example_data, f, indent=2)
        
    print("📝 Created example_hand_eye_data.json")
    print("   Edit this file with your actual calibration data")

def main():
    parser = argparse.ArgumentParser(description='Hand-Eye Calibration for A1 Mini Robot')
    parser.add_argument('command', choices=['calibrate', 'transform', 'example'],
                       help='Command to run')
    parser.add_argument('data_file', nargs='?', 
                       help='JSON file with calibration data')
    parser.add_argument('--output', '-o', default='hand_eye_transform.yaml',
                       help='Output YAML file for transformation')
    
    args = parser.parse_args()
    
    if args.command == 'example':
        create_example_data()
        return
        
    if args.command == 'calibrate':
        if not args.data_file:
            print("❌ Please provide calibration data file")
            return
            
        calibrator = HandEyeCalibration()
        calibrator.load_calibration_data(args.data_file)
        
        success, transform = calibrator.calibrate_hand_eye()
        if success:
            calibrator.save_transform(args.output)
            
            print(f"\n🎯 Hand-Eye Calibration Results:")
            print(f"   Translation: {transform[:3, 3]}")
            print(f"   Rotation matrix:")
            print(f"   {transform[:3, :3]}")
            
    elif args.command == 'transform':
        # Example of using the calibration
        print("🔄 Transform example - load your transform and AprilTag pose")

if __name__ == "__main__":
    main()