#!/usr/bin/env python3
"""
AprilTag Detection Script for A1 Mini Camera
Detects AprilTags in captured images and computes 6DOF pose using camera intrinsics.

Usage:
    python detect_apriltag.py img1.png
    python detect_apriltag.py  # Uses img1.png by default
"""

import cv2
import numpy as np
import yaml
import argparse
import sys
import json
from datetime import datetime
from pathlib import Path
from scipy.spatial.transform import Rotation as R

try:
    from pupil_apriltags import Detector
    PUPIL_APRILTAGS_AVAILABLE = True
except ImportError:
    print("⚠️  pupil-apriltags library not found. Install with: pip install pupil-apriltags")
    PUPIL_APRILTAGS_AVAILABLE = False

def load_camera_intrinsics(config_path="config/ac_lab_camera_calibration.yaml"):
    """Load camera intrinsics from YAML configuration file."""
    try:
        with open(config_path, 'r') as f:
            calib = yaml.safe_load(f)
        return calib
    except FileNotFoundError:
        print(f"❌ Camera intrinsics file not found: {config_path}")
        return None

def get_camera_matrices(calib):
    """Extract camera matrix and distortion coefficients."""
    K = np.array(calib["camera_matrix"], dtype=np.float32)
    
    # Handle different distortion coefficient formats
    if isinstance(calib["distortion_coefficients"][0], list):
        # Old format: nested list
        dist = np.array(calib["distortion_coefficients"][0], dtype=np.float32)
    else:
        # New format: flat list
        dist = np.array(calib["distortion_coefficients"], dtype=np.float32)
    
    return K, dist


def detect_apriltag_pupil(image_path, camera_matrix, dist_coeffs, tag_size_m=0.05):
    """
    Detect AprilTag using the pupil-apriltags library.
    """
    if not PUPIL_APRILTAGS_AVAILABLE:
        return None
    
    # Load image
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Could not load image: {image_path}")
        return None
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Camera parameters for pupil-apriltags (fx, fy, cx, cy)
    camera_params = [camera_matrix[0,0], camera_matrix[1,1], camera_matrix[0,2], camera_matrix[1,2]]
    
    # Try different tag families
    families_to_try = ['tag36h11', 'tagStandard41h12', 'tag25h9', 'tag16h5']
    
    for family in families_to_try:
        print(f"   Trying {family}...")
        try:
            # Initialize detector
            detector = Detector(families=family)
            
            # Detect tags with pose estimation
            detections = detector.detect(
                gray,
                estimate_tag_pose=True,
                camera_params=camera_params,
                tag_size=tag_size_m
            )
            
            if detections:
                break
        except Exception as e:
            print(f"   Error with {family}: {e}")
            continue
    
    if detections:
        print(f"✅ pupil-apriltags detected {len(detections)} tag(s) with {family}")
        
        results = []
        for detection in detections:
            tag_id = detection.tag_id
            corners = detection.corners
            center = detection.center
            
            print(f"   Tag ID {tag_id}:")
            print(f"     Center: [{center[0]:.1f}, {center[1]:.1f}]")
            print(f"     Corners: {corners.shape}")
            
            # Use pose from pupil-apriltags if available
            if detection.pose_t is not None and detection.pose_R is not None:
                # Convert rotation matrix to rotation vector
                rvec, _ = cv2.Rodrigues(detection.pose_R)
                tvec = detection.pose_t.flatten()
                
                results.append({
                    'tag_id': tag_id,
                    'corners': corners,
                    'center': center,
                    'rvec': rvec.flatten(),
                    'tvec': tvec,
                    'method': 'pupil_apriltags'
                })
                
                print(f"     Position (m): [{tvec[0]:.3f}, {tvec[1]:.3f}, {tvec[2]:.3f}]")
                print(f"     Rotation (rad): [{rvec[0][0]:.3f}, {rvec[1][0]:.3f}, {rvec[2][0]:.3f}]")
                
                # Calculate distance
                distance_cm = np.linalg.norm(tvec) * 100
                print(f"     Distance: {distance_cm:.1f}cm")
                
                # Convert rotation matrix to roll, pitch, yaw
                try:
                    # Check if rotation matrix is valid (positive determinant)
                    det = np.linalg.det(detection.pose_R)
                    if det > 0:
                        euler = R.from_matrix(detection.pose_R).as_euler('xyz', degrees=True)
                        roll, pitch, yaw = euler
                        print(f"     Roll: {roll:.2f}°, Pitch: {pitch:.2f}°, Yaw: {yaw:.2f}°")
                    else:
                        print(f"     ⚠️  Invalid rotation matrix (det={det:.3f}), using rotation vector instead")
                        # Use rotation vector as approximation
                        roll, pitch, yaw = np.degrees(rvec.flatten())
                        print(f"     Roll: {roll:.2f}°, Pitch: {pitch:.2f}°, Yaw: {yaw:.2f}°")
                except ValueError as e:
                    print(f"     ⚠️  Rotation matrix error: {e}")
                    # Fallback to rotation vector
                    roll, pitch, yaw = np.degrees(rvec.flatten())
                    print(f"     Roll: {roll:.2f}°, Pitch: {pitch:.2f}°, Yaw: {yaw:.2f}° (from rvec)")
            else:
                print(f"     ❌ No pose estimation available for tag {tag_id}")
        
        return results
    
    print("❌ No AprilTags detected with any family")
    return None

def visualize_detections(image_path, detections, camera_matrix, dist_coeffs, output_path=None):
    """
    Visualize detected AprilTags with pose axes.
    """
    if not detections:
        return
    
    img = cv2.imread(image_path)
    if img is None:
        return
    
    for detection in detections:
        tag_id = detection['tag_id']
        corners = detection['corners']
        rvec = detection['rvec']
        tvec = detection['tvec']
        
        # Draw tag outline
        corners_int = corners.astype(int)
        cv2.polylines(img, [corners_int], True, (0, 255, 0), 2)
        
        # Draw tag ID
        center = corners.mean(axis=0).astype(int)
        cv2.putText(img, f"ID: {tag_id}", (center[0]-20, center[1]-10), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        # Draw coordinate axes
        axis_length = 0.03  # 3cm axes
        axis_points = np.array([
            [0, 0, 0],           # Origin
            [axis_length, 0, 0], # X-axis (red)
            [0, axis_length, 0], # Y-axis (green)
            [0, 0, axis_length], # Z-axis (blue)
        ], dtype=np.float32)
        
        # Project 3D points to image
        projected, _ = cv2.projectPoints(axis_points, rvec, tvec, camera_matrix, dist_coeffs)
        projected = projected.astype(int).reshape(-1, 2)
        
        # Draw axes
        origin = projected[0]
        cv2.arrowedLine(img, origin, projected[1], (0, 0, 255), 3)  # X-axis: red
        cv2.arrowedLine(img, origin, projected[2], (0, 255, 0), 3)  # Y-axis: green  
        cv2.arrowedLine(img, origin, projected[3], (255, 0, 0), 3)  # Z-axis: blue
    
    # Save or display result
    if output_path:
        cv2.imwrite(output_path, img)
        print(f"✅ Visualization saved to: {output_path}")
    else:
        cv2.imshow('AprilTag Detection', img)
        print("Press any key to close the visualization...")
        cv2.waitKey(0)
        cv2.destroyAllWindows()

def save_pose_to_json(detections, output_path):
    """Save 6DOF pose data to JSON file"""
    pose_data = {
        "timestamp": str(pd.Timestamp.now()) if 'pd' in globals() else str(datetime.now()),
        "detections": []
    }
    
    for detection in detections:
        tag_id = detection['tag_id']
        tvec = detection['tvec']
        
        # Calculate roll, pitch, yaw from rotation vector
        rvec = detection['rvec']
        R_matrix, _ = cv2.Rodrigues(rvec)
        euler = R.from_matrix(R_matrix).as_euler('xyz', degrees=True)
        roll, pitch, yaw = euler
        
        tag_data = {
            "tag_id": int(tag_id),
            "position": {
                "x": float(tvec[0]),
                "y": float(tvec[1]), 
                "z": float(tvec[2])
            },
            "orientation": {
                "roll": float(roll),
                "pitch": float(pitch),
                "yaw": float(yaw)
            },
            "distance_cm": float(np.linalg.norm(tvec) * 100)
        }
        pose_data["detections"].append(tag_data)
    
    # Save to JSON file
    with open(output_path, 'w') as f:
        json.dump(pose_data, f, indent=2)
    
    print(f"✅ Pose data saved to: {output_path}")

def main():
    parser = argparse.ArgumentParser(description='Detect AprilTags in camera image')
    parser.add_argument('image', nargs='?', default='img1.png', 
                       help='Path to image file (default: img1.png)')
    parser.add_argument('--tag-size', type=float, default=0.05,
                       help='AprilTag size in meters (default: 0.05m = 5cm)')
    parser.add_argument('--visualize', action='store_true',
                       help='Show visualization with detected tags')
    parser.add_argument('--save-viz', type=str,
                       help='Save visualization to file')
    parser.add_argument('--save-json', type=str,
                       help='Save pose data to JSON file')
    
    args = parser.parse_args()
    
    # Check if image exists
    if not Path(args.image).exists():
        print(f"❌ Image file not found: {args.image}")
        sys.exit(1)
    
    print("🏷️  AprilTag Detection Starting...")
    print(f"   Image: {args.image}")
    print(f"   Tag size: {args.tag_size}m")
    
    # Load camera intrinsics
    print("\n📷 Loading camera intrinsics...")
    calib = load_camera_intrinsics()
    if calib is None:
        sys.exit(1)
    
    K, dist = get_camera_matrices(calib)
    print(f"✅ Camera intrinsics loaded")
    
    # Extract focal lengths from camera matrix
    fx, fy = K[0,0], K[1,1]
    print(f"   Focal length: fx={fx:.1f}, fy={fy:.1f}")
    
    # Handle different image size formats
    if 'image_size' in calib:
        print(f"   Image size: {calib['image_size']}")
    else:
        print(f"   Image size: not specified in calibration")
    
    # Try AprilTag detection
    print(f"\n🔍 Detecting AprilTags in {args.image}...")
    
    # Use pupil-apriltags for detection
    detections = detect_apriltag_pupil(args.image, K, dist, args.tag_size)
    
    # Results
    if detections:
        print(f"\n✅ Detection successful! Found {len(detections)} tag(s)")
        
        # Show visualization if requested
        if args.visualize or args.save_viz:
            print("\n🖼️  Generating visualization...")
            visualize_detections(args.image, detections, K, dist, args.save_viz)
        
        # Save pose data to JSON if requested
        if args.save_json:
            save_pose_to_json(detections, args.save_json)
        
        print("\n📊 Summary:")
        for det in detections:
            print(f"   Tag {det['tag_id']}: Position [{det['tvec'][0]:.3f}, {det['tvec'][1]:.3f}, {det['tvec'][2]:.3f}]m")
    else:
        print("\n❌ No AprilTags detected in image")
        print("   Possible issues:")
        print("   - No AprilTag in the image")
        print("   - AprilTag too small/blurry/angled")
        print("   - Wrong tag family (script expects tag36h11)")
        print("   - Poor lighting conditions")

if __name__ == "__main__":
    main()