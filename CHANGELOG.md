# CHANGELOG

## [Unreleased]
### Changed
- Removed all fallbacks in `src/ac_training_lab/a1_cam/detect_apriltag.py`:
  - Import of pupil_apriltags now raises error if not installed
  - File loading raises FileNotFoundError instead of returning None
  - Image loading raises FileNotFoundError instead of returning None
  - Tag family is now specified explicitly via --tag-family parameter instead of trying multiple families
- Added --tag-family CLI argument for explicit tag family specification (default: tag36h11)
- Cross-checked AprilTag pose detection math against official documentation (verified correct)

### Added
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
