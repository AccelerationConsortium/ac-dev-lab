# CHANGELOG

## [Unreleased]
### Added
- **XArm5 Integration**: Complete module for controlling UFACTORY xArm5 robotic arm from Raspberry Pi 5 (`src/ac_training_lab/xarm5/`)
  - Comprehensive README with setup instructions for Raspberry Pi 5
  - Requirements file with xarm-python-sdk dependency
  - Example scripts for basic movement, gripper control, linear track integration, and safety features
  - Support for rail/lift/arm combo integration with linear track control
  - Network configuration guide for xArm5 control box
  - Troubleshooting and safety documentation
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
