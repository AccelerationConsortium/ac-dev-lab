# CHANGELOG

## [Unreleased]
### Added
- Support for both `rpicam-vid` (Raspberry Pi OS Trixie) and `libcamera-vid` (Raspberry Pi OS Bookworm) camera commands in `src/ac_training_lab/picam/device.py` to ensure compatibility across different OS versions.
- **Real Blockly installation** using official npm package (blockly v12.3.1) with custom OT-2 blocks:
  - `scripts/blockly_app/`: Complete webpack-bundled application with real Blockly installation
  - Custom blocks for `mix_color()`, `move_sensor_back()`, and `protocol.home()` functions
  - Real-time Python code generation from visual blocks
  - Fully functional drag-and-drop interface
  - Documentation: `scripts/blockly_app/README.md`

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
