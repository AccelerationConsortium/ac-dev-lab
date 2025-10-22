# CHANGELOG

## [Unreleased]
### Added
- Support for both `rpicam-vid` (Raspberry Pi OS Trixie) and `libcamera-vid` (Raspberry Pi OS Bookworm) camera commands in `src/ac_training_lab/picam/device.py` to ensure compatibility across different OS versions.
- Analog clock overlay module (`src/ac_training_lab/video_editing/analog_clock_overlay.py`) for adding customizable analog clocks to video streams and time-lapse videos.
- Comprehensive documentation for analog clock usage in `docs/analog_clock_recommendations.md` and `docs/analog_clock_installation.md`.
- Demonstration script (`examples/analog_clock_demo.py`) showing various clock styles, positions, and use cases.

### Fixed
- Ctrl+C interrupt handling in `src/ac_training_lab/picam/device.py` now properly exits the streaming loop instead of restarting.

## [1.1.0] - 2024-06-11
### Added
- Imperial (10-32 thread) alternative design to SEM door automation bill of materials in `docs/sem-door-automation-components.md`.
- Validated McMaster-Carr part numbers and direct links for all imperial components.

### Changed
- No changes to metric design section.

### Notes
- All components sourced from McMaster-Carr for reliability and reproducibility.
