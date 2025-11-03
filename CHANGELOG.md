# CHANGELOG

## [Unreleased]
### Added
- Support for both `rpicam-vid` (Raspberry Pi OS Trixie) and `libcamera-vid` (Raspberry Pi OS Bookworm) camera commands in `src/ac_training_lab/picam/device.py` to ensure compatibility across different OS versions.
- Blockly integration demonstration showing how custom visual programming blocks can be created for OT-2 functions from `OT2mqtt.py`:
  - `scripts/blockly_concept_demo.html`: Visual demonstration of block-to-code mapping
  - `scripts/blockly_ot2_demo.html`: Interactive Blockly editor with custom OT-2 blocks
  - `scripts/blockly_example.py`: Python example showing generated code patterns
  - `scripts/BLOCKLY_README.md`: Comprehensive documentation for Blockly integration
  - Custom blocks for `mix_color()`, `move_sensor_back()`, and `protocol.home()` functions

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
