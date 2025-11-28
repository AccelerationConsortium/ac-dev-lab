# CHANGELOG

## [Unreleased]
### Added
- **AprilTag Detection and Hand-Eye Calibration System for A1 Mini Camera**:
  - AprilTag detection with 6DOF pose estimation (`src/ac_training_lab/a1_cam/detect_apriltag.py`) supporting multiple tag families (tag36h11, tagStandard41h12, tag25h9, tag16h5) with position (x,y,z) and orientation (roll,pitch,yaw) output in JSON format.
  - Camera calibration tool (`src/ac_training_lab/a1_cam/calibrate_camera.py`) for 11x8 checkerboard patterns achieving 0.27px RMS reprojection error.
  - Hand-eye calibration implementation (`src/ac_training_lab/a1_cam/hand_eye_calibration.py`) using OpenCV's CALIB_HAND_EYE_TSAI algorithm to compute camera-to-end-effector transformation.
  - Calibration data collection helper (`src/ac_training_lab/a1_cam/collect_hand_eye_data.py`) to streamline gathering robot pose and AprilTag detection pairs.
  - Updated camera intrinsics (`src/ac_training_lab/a1_cam/config/a1_intrinsics.yaml`) with improved calibration accuracy (fx: 490.9, fy: 507.4, 0.27px error).
  - 15 calibration images in `src/ac_training_lab/a1_cam/calibration_images/` for reproducible camera calibration.
  - Dependencies: `pupil-apriltags` for robust AprilTag detection and `scipy` for rotation transformations.
- Support for both `rpicam-vid` (Raspberry Pi OS Trixie) and `libcamera-vid` (Raspberry Pi OS Bookworm) camera commands in `src/ac_training_lab/picam/device.py` to ensure compatibility across different OS versions.
- Comprehensive Unit Operations section in `docs/index.md` documenting all available capabilities including dispensing, synthesis, characterization, and robotics operations.
- Expanded Training Workflows section in `docs/index.md` with 10 educational workflows including RGB/RYB color matching, titration, yeast growth optimization, vision-enabled 3D printing optimization, microscopy image stitching, and AprilTag robot path planning.
- Research Workflows section in `docs/index.md` documenting alkaline catalysis lifecycle testing and battery slurry viscosity optimization.
- Direct links from unit operations and workflows to relevant code locations in the repository for easier navigation.

### Fixed
- Ctrl+C interrupt handling in `src/ac_training_lab/picam/device.py` now properly exits the streaming loop instead of restarting.
- Fixed typo "reagants" → "reagents" in Conductivity workflow description.

## [1.1.0] - 2024-06-11
### Added
- Imperial (10-32 thread) alternative design to SEM door automation bill of materials in `docs/sem-door-automation-components.md`.
- Validated McMaster-Carr part numbers and direct links for all imperial components.

### Changed
- No changes to metric design section.

### Notes
- All components sourced from McMaster-Carr for reliability and reproducibility.
