#!/usr/bin/env python3
"""
AprilTag Coordinate Transformation
Corrects AprilTag poses detected in flipped images back to original coordinate system
"""

import json
import numpy as np
from scipy.spatial.transform import Rotation as R
import argparse

def transform_vertical_flip(pose_data):
    """
    Transform coordinates from vertically flipped image back to original
    Vertical flip: Y gets negated, X stays same, rotations around X-axis get negated
    """
    transformed_detections = []
    
    for detection in pose_data['detections']:
        # Transform position  
        original_pos = {
            'x': detection['position']['x'],   # Keep X
            'y': -detection['position']['y'],  # Negate Y
            'z': detection['position']['z']    # Keep Z
        }
        
        # Transform orientation - vertical flip affects pitch primarily
        original_orient = {
            'roll': detection['orientation']['roll'],      # Keep roll
            'pitch': -detection['orientation']['pitch'],   # Negate pitch
            'yaw': detection['orientation']['yaw']         # Keep yaw
        }
        
        # Recalculate distance
        distance_cm = np.sqrt(original_pos['x']**2 + original_pos['y']**2 + original_pos['z']**2) * 100
        
        transformed_detection = {
            'tag_id': detection['tag_id'],
            'position': original_pos,
            'orientation': original_orient,
            'distance_cm': distance_cm,
            'transformation_applied': 'vertical_flip_correction'
        }
        
        transformed_detections.append(transformed_detection)
    
    return {
        'timestamp': pose_data['timestamp'],
        'detections': transformed_detections,
        'coordinate_system': 'original_camera_orientation'
    }

def transform_coordinates(input_file, flip_type, output_file=None):
    """
    Apply coordinate transformation to correct for image flipping
    
    Args:
        input_file: JSON file with AprilTag detections from flipped image
        flip_type: 'horizontal' or 'vertical'
        output_file: Output file name (optional)
    """
    
    # Load detection data
    with open(input_file, 'r') as f:
        pose_data = json.load(f)
    
    print(f"🔄 Transforming coordinates from {flip_type} flip")
    print(f"📂 Input: {input_file}")
    
    # Apply transformation
    if flip_type == 'horizontal':
        transformed_data = transform_horizontal_flip(pose_data)
    elif flip_type == 'vertical':
        transformed_data = transform_vertical_flip(pose_data)
    else:
        raise ValueError("flip_type must be 'horizontal' or 'vertical'")
    
    # Generate output filename if not provided
    if output_file is None:
        base_name = input_file.replace('.json', '')
        output_file = f"{base_name}_corrected.json"
    
    # Save transformed data
    with open(output_file, 'w') as f:
        json.dump(transformed_data, f, indent=2)
    
    print(f"✅ Corrected coordinates saved to: {output_file}")
    
    # Show comparison
    original_detection = pose_data['detections'][0]
    corrected_detection = transformed_data['detections'][0]
    
    print(f"\n📊 Coordinate Transformation Results:")
    print(f"   Tag ID: {original_detection['tag_id']}")
    print(f"   Original Position: ({original_detection['position']['x']:.3f}, {original_detection['position']['y']:.3f}, {original_detection['position']['z']:.3f})")
    print(f"   Corrected Position: ({corrected_detection['position']['x']:.3f}, {corrected_detection['position']['y']:.3f}, {corrected_detection['position']['z']:.3f})")
    print(f"   Original Distance: {original_detection['distance_cm']:.1f}cm")
    print(f"   Corrected Distance: {corrected_detection['distance_cm']:.1f}cm")
    
    return output_file

def main():
    parser = argparse.ArgumentParser(description='Transform AprilTag coordinates to correct for image flipping')
    parser.add_argument('input_file', help='JSON file with AprilTag detections from flipped image')
    parser.add_argument('flip_type', choices=['horizontal', 'vertical'], 
                       help='Type of flip applied to the image')
    parser.add_argument('--output', '-o', help='Output file name (optional)')
    
    args = parser.parse_args()
    
    transform_coordinates(args.input_file, args.flip_type, args.output)

if __name__ == "__main__":
    main()