#!/usr/bin/env python3
"""
Camera Calibration Script for A1 Mini Camera
Based on the apriltag_demo.ipynb approach

This script performs camera calibration using checkerboard images to generate
accurate camera intrinsics for your working distance (~15cm).

Instructions:
1. Print a checkerboard pattern (7x10 internal corners, 23mm square size)
2. Take 15-20 photos of the checkerboard at ~15cm distance from different angles
3. Save photos as 'calib_01.jpg', 'calib_02.jpg', etc. in images/ directory  
4. Run this script to generate new camera intrinsics

The script will output:
- New a1_intrinsics.yaml file with corrected camera matrix and distortion coefficients
- Calibration quality metrics (reprojection error)
"""

import cv2
import numpy as np
import glob
import yaml
import os
from pathlib import Path

def calibrate_camera_from_images(image_paths, pattern_size, square_size_m, image_size=None):
    """
    Calibrate camera using checkerboard images
    
    Args:
        image_paths: List of paths to calibration images
        pattern_size: (cols, rows) of internal checkerboard corners 
        square_size_m: Size of checkerboard squares in meters
        image_size: (width, height) of images, auto-detected if None
        
    Returns:
        ret: Calibration success flag
        camera_matrix: 3x3 camera matrix
        dist_coeffs: Distortion coefficients 
        rvecs: Rotation vectors
        tvecs: Translation vectors
        rms_error: RMS reprojection error
    """
    
    # Prepare object points - coordinates of corners in checkerboard coordinate system
    objp = np.zeros((pattern_size[0] * pattern_size[1], 3), np.float32)
    objp[:, :2] = np.mgrid[0:pattern_size[0], 0:pattern_size[1]].T.reshape(-1, 2)
    objp *= square_size_m  # Scale by actual square size
    
    # Arrays to store object points and image points from all images
    objpoints = []  # 3D points in real world space
    imgpoints = []  # 2D points in image plane
    
    print(f"🔍 Processing {len(image_paths)} calibration images...")
    
    successful_images = 0
    for i, image_path in enumerate(image_paths):
        print(f"   Processing image {i+1}/{len(image_paths)}: {Path(image_path).name}")
        
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            print(f"      ❌ Could not load image: {image_path}")
            continue
            
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Auto-detect image size from first successful image
        if image_size is None:
            image_size = gray.shape[::-1]  # (width, height)
        
        # Find checkerboard corners
        ret, corners = cv2.findChessboardCorners(gray, pattern_size, None)
        
        if ret:
            # Refine corner positions for sub-pixel accuracy
            corners = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), 
                                     (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001))
            
            objpoints.append(objp)
            imgpoints.append(corners)
            successful_images += 1
            print(f"      ✅ Found checkerboard corners")
        else:
            print(f"      ❌ Could not find checkerboard corners")
    
    print(f"\n📊 Successfully processed {successful_images}/{len(image_paths)} images")
    
    if successful_images < 10:
        print("⚠️  Warning: Less than 10 successful images. Consider taking more calibration photos.")
        
    if successful_images < 3:
        print("❌ Error: Not enough successful images for calibration (need at least 3)")
        return False, None, None, None, None, None
    
    print("🔧 Performing camera calibration...")
    
    # Perform camera calibration
    ret, camera_matrix, dist_coeffs, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, image_size, None, None,
        flags=cv2.CALIB_RATIONAL_MODEL
    )
    
    # Calculate reprojection error
    mean_error = 0
    for i in range(len(objpoints)):
        imgpoints2, _ = cv2.projectPoints(objpoints[i], rvecs[i], tvecs[i], camera_matrix, dist_coeffs)
        error = cv2.norm(imgpoints[i], imgpoints2, cv2.NORM_L2) / len(imgpoints2)
        mean_error += error
    
    rms_error = mean_error / len(objpoints)
    
    return ret, camera_matrix, dist_coeffs, rvecs, tvecs, rms_error

def save_calibration_to_yaml(camera_matrix, dist_coeffs, image_size, rms_error, output_path):
    """Save calibration results to YAML file compatible with detect_apriltag.py"""
    
    calib_data = {
        'camera_matrix': camera_matrix.tolist(),
        'distortion_coefficients': dist_coeffs.flatten().tolist(), 
        'image_size': list(image_size),
        'rms_reprojection_error_pixels': float(rms_error)
    }
    
    # Create config directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        yaml.dump(calib_data, f, default_flow_style=False)
    
    print(f"✅ Saved calibration to: {output_path}")

def main():
    print("📷 A1 Mini Camera Calibration")
    print("=" * 40)
    
    # Configuration matching detected pattern  
    pattern_size = (11, 8)  # Internal corners (cols, rows) 
    square_size_mm = 23.0   # Size of each square in mm (measure your printed checkerboard!)
    square_size_m = square_size_mm / 1000.0  # Convert to meters
    
    print(f"📋 Checkerboard settings:")
    print(f"   Internal corners: {pattern_size[0]} x {pattern_size[1]}")
    print(f"   Square size: {square_size_mm}mm")
    print(f"   ⚠️  Verify your printed checkerboard matches these dimensions!")
    
    # Look for calibration images
    image_dir = "calibration_images"
    if not os.path.exists(image_dir):
        print(f"\n❌ Images directory not found: {image_dir}")
        print("Please create the calibration_images directory and add your checkerboard calibration photos.")
        print("Expected filenames: calib_01.jpg, calib_02.jpg, etc.")
        return
    
    # Find calibration images
    image_patterns = [
        f"{image_dir}/calib_*.jpg",
        f"{image_dir}/calib_*.png", 
        f"{image_dir}/calibration_*.jpg",
        f"{image_dir}/calibration_*.png",
        f"{image_dir}/*.jpg",
        f"{image_dir}/*.png"
    ]
    
    image_paths = []
    for pattern in image_patterns:
        image_paths.extend(glob.glob(pattern))
    
    # Remove duplicates and sort
    image_paths = sorted(list(set(image_paths)))
    
    if not image_paths:
        print(f"\n❌ No calibration images found in {image_dir}/")
        print("Please add calibration images and try again.")
        print("Supported formats: .jpg, .png")
        return
    
    print(f"\n🖼️  Found {len(image_paths)} calibration images")
    
    # Perform calibration
    ret, camera_matrix, dist_coeffs, rvecs, tvecs, rms_error = calibrate_camera_from_images(
        image_paths, pattern_size, square_size_m
    )
    
    if not ret:
        print("❌ Calibration failed!")
        return
    
    print("\n✅ Calibration successful!")
    print(f"📊 Results:")
    print(f"   RMS reprojection error: {rms_error:.4f} pixels")
    print(f"   Camera matrix:")
    print(f"     fx: {camera_matrix[0,0]:.2f}")
    print(f"     fy: {camera_matrix[1,1]:.2f}") 
    print(f"     cx: {camera_matrix[0,2]:.2f}")
    print(f"     cy: {camera_matrix[1,2]:.2f}")
    
    # Quality assessment
    if rms_error < 0.5:
        print("   🟢 Excellent calibration quality")
    elif rms_error < 1.0:
        print("   🟡 Good calibration quality") 
    else:
        print("   🔴 Poor calibration quality - consider retaking photos")
    
    # Save to config directory
    output_path = "config/a1_intrinsics_new.yaml"
    
    # Get image size from first image
    first_img = cv2.imread(image_paths[0])
    image_size = (first_img.shape[1], first_img.shape[0])  # (width, height)
    
    save_calibration_to_yaml(camera_matrix, dist_coeffs, image_size, rms_error, output_path)
    
    print(f"\n📁 Next steps:")
    print(f"   1. Test the new calibration: python detect_apriltag.py images/your_test_image.png")
    print(f"   2. If results look good, backup old calibration:")
    print(f"      mv config/a1_intrinsics.yaml config/a1_intrinsics_backup.yaml")
    print(f"   3. Use new calibration:")
    print(f"      mv config/a1_intrinsics_new.yaml config/a1_intrinsics.yaml")

if __name__ == "__main__":
    main()