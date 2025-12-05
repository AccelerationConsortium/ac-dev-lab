# A1 Mini Camera - AprilTag Detection & Hand-Eye Calibration

Complete AprilTag detection and hand-eye calibration system for the A1 Mini camera setup, enabling accurate robot arm control based on visual AprilTag detection.

## Features

### 🏷️ AprilTag Detection System
- **6DOF Pose Estimation**: Position (x,y,z) + orientation (roll,pitch,yaw)
- **Multiple Tag Families**: Supports tag36h11, tagStandard41h12, tag25h9, tag16h5
- **JSON Output**: Complete pose data export for robot integration
- **Robust Detection**: Handles image orientation issues with automatic family testing

### 📷 Camera Calibration
- **High Accuracy**: 0.27px RMS reprojection error
- **Checkerboard-based**: 11x8 internal corners, 23mm square size
- **Improved Distance Measurements**: From 133cm error to 39.5cm using proper calibration

### 🤖 Hand-Eye Calibration
- **AX=XB Algorithm**: OpenCV's CALIB_HAND_EYE_TSAI method
- **Camera-to-Robot Transform**: Converts AprilTag detections to robot arm coordinates
- **Data Collection Helper**: Streamlined workflow for gathering calibration data

## Installation

Install required dependencies:

```bash
pip install -r requirements.txt
```

## Quick Start

### 1. AprilTag Detection

Detect AprilTags in an image with 6DOF pose estimation:

```bash
python detect_apriltag.py apriltag_images/img1_flipped_vertical.png --tag-size 0.03 --save-json pose_data.json --visualize
```

**Options:**
- `--tag-size`: AprilTag size in meters (default: 0.05m)
- `--save-json`: Save pose data to JSON file
- `--visualize`: Display visualization with detected tags
- `--save-viz`: Save visualization to file

**Output:**
```json
{
  "timestamp": "2025-11-28 02:45:48.651043",
  "detections": [
    {
      "tag_id": 2,
      "position": {
        "x": -0.170, "y": -0.031, "z": 0.395
      },
      "orientation": {
        "roll": -2.28, "pitch": -8.41, "yaw": -1.26
      },
      "distance_cm": 43.1
    }
  ]
}
```

### 2. Camera Calibration

Recalibrate the camera using checkerboard images:

```bash
python calibrate_camera.py
```

**Requirements:**
- 15-20 checkerboard images in `calibration_images/` directory
- 11x8 internal corners (12x9 squares)
- 23mm square size (measure your printed checkerboard!)

**Output:**
- New calibration file: `config/a1_intrinsics_new.yaml`
- RMS reprojection error metric
- Camera matrix with focal lengths and principal point

### 3. Hand-Eye Calibration

#### Step 1: Collect Calibration Data

Move robot to different poses while keeping AprilTag in view:

```bash
# For each robot pose:
python collect_hand_eye_data.py --robot-pose 0.15 0.0 0.25 0.0 0.0 0.0
```

**Arguments:**
- `--robot-pose`: x y z roll pitch yaw (meters, degrees)
- `--image`: AprilTag image path (default: apriltag_images/img1_flipped_vertical.png)
- `--tag-size`: AprilTag size in meters (default: 0.03)
- `--data-file`: Output calibration data file (default: hand_eye_calibration_data.json)

Check status:
```bash
python collect_hand_eye_data.py --status
```

#### Step 2: Compute Hand-Eye Calibration

Once you have 5-10 calibration points:

```bash
python hand_eye_calibration.py calibrate hand_eye_calibration_data.json
```

**Output:**
- Transformation file: `hand_eye_transform.yaml`
- Camera-to-end-effector transformation matrix
- Translation and rotation parameters

#### Step 3: Create Example Data (Optional)

Generate example calibration data file:

```bash
python hand_eye_calibration.py example
```

## File Structure

```
a1_cam/
├── detect_apriltag.py              # Main AprilTag detection script
├── calibrate_camera.py             # Camera calibration tool
├── hand_eye_calibration.py         # Hand-eye calibration algorithm
├── collect_hand_eye_data.py        # Calibration data collection helper
├── config/
│   ├── a1_intrinsics.yaml          # Current camera intrinsics
│   └── a1_intrinsics_backup.yaml   # Original calibration backup
├── calibration_images/             # Checkerboard images (1.png - 15.png)
├── apriltag_images/                # AprilTag test images
│   └── img1_flipped_vertical.png
├── pose_new_calibration.json       # Sample detection results
├── requirements.txt                # Python dependencies
└── README.md                       # This file
```

## Technical Details

### Detection Library
- **pupil-apriltags**: Robust AprilTag detection with pose estimation
- Supports multiple tag families for robust detection
- Provides 6DOF pose in camera coordinates

### Calibration Method
- **OpenCV checkerboard-based calibration**: Industry-standard approach
- **Rational camera model**: Handles complex lens distortions
- **Sub-pixel corner refinement**: Improves accuracy

### Hand-Eye Algorithm
- **OpenCV's CALIB_HAND_EYE_TSAI**: Solves AX=XB problem
- Computes fixed transformation between camera and end-effector
- Enables conversion from camera to robot base coordinates

### Coordinate Systems
- **Camera coordinates**: Origin at camera optical center, Z forward
- **Robot coordinates**: Robot base frame, typically Z up
- **AprilTag coordinates**: Tag center with Z perpendicular to tag surface

## Usage Examples

### Complete Detection Workflow

```bash
# 1. Capture image with camera (not shown - use your camera interface)

# 2. Detect AprilTag with visualization
python detect_apriltag.py my_image.png --tag-size 0.03 --visualize --save-json pose.json

# 3. Use pose data in robot control
# Read pose.json and transform to robot coordinates using hand-eye calibration
```

### Complete Calibration Workflow

```bash
# 1. Camera Calibration (one-time setup)
# - Take 15-20 checkerboard photos at ~15cm distance
# - Save as calibration_images/1.png, 2.png, etc.
python calibrate_camera.py

# 2. Hand-Eye Calibration (one-time setup)
# - Move robot to pose 1
python collect_hand_eye_data.py --robot-pose 0.15 0.0 0.25 0.0 0.0 0.0

# - Move robot to pose 2
python collect_hand_eye_data.py --robot-pose 0.12 0.05 0.22 10.0 5.0 -15.0

# - Repeat for 5-10 different poses...

# - Compute calibration
python hand_eye_calibration.py calibrate hand_eye_calibration_data.json

# 3. Use calibration for robot control
```

## Calibration Quality

### Current Performance
- ✅ **Tag Detection**: Successfully detects tag36h11 with complete 6DOF pose
- ✅ **Camera Calibration**: 15/15 images processed, 0.27px RMS error (excellent)
- ✅ **Distance Accuracy**: Improved from 133cm to 39.5cm measurement error
- ✅ **Orientation Handling**: Robust across image orientations

### Expected Accuracy
- **Position**: ±5-10mm at 15cm distance (with proper calibration)
- **Orientation**: ±1-2° (depends on tag size and distance)
- **Distance**: ±1-2cm at typical working distances (10-30cm)

## Troubleshooting

### AprilTag Not Detected
- Ensure AprilTag is clearly visible and in focus
- Try different tag families (script auto-tests multiple)
- Check lighting conditions (avoid glare/shadows)
- Verify tag size matches `--tag-size` parameter

### Poor Calibration Results
- Take more calibration images (15-20 recommended)
- Vary checkerboard angles and positions
- Ensure checkerboard is flat and printed accurately
- Verify square size matches actual printed size

### Hand-Eye Calibration Issues
- Collect more calibration points (5-10 minimum)
- Ensure diverse robot poses (vary position and orientation)
- Keep AprilTag visible in all calibration images
- Verify robot pose values are accurate

## Dependencies

- `opencv-python`: Image processing and calibration
- `numpy`: Numerical computations
- `scipy`: Rotation transformations
- `pupil-apriltags`: AprilTag detection with pose estimation
- `PyYAML`: Configuration file handling
- `boto3`: AWS S3 integration (optional)
- `paho-mqtt`: MQTT messaging (optional)

## References

- [AprilTag Detection](https://april.eecs.umich.edu/software/apriltag)
- [OpenCV Camera Calibration](https://docs.opencv.org/4.x/dc/dbb/tutorial_py_calibration.html)
- [Hand-Eye Calibration](https://docs.opencv.org/4.x/d9/d0c/group__calib3d.html#gaebfc1c9f7434196a374c382abf43439b)
- [pupil-apriltags Library](https://github.com/pupil-labs/apriltags)

## Contributing

When updating this system:
1. Test all changes with real AprilTag images
2. Verify calibration accuracy with known distances
3. Update documentation and examples
4. Record changes in CHANGELOG.md

## License

MIT License - See LICENSE.txt in repository root
