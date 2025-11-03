# CHANGELOG

## [Unreleased]
### Added
- Support for both `rpicam-vid` (Raspberry Pi OS Trixie) and `libcamera-vid` (Raspberry Pi OS Bookworm) camera commands in `src/ac_training_lab/picam/device.py` to ensure compatibility across different OS versions.
- OT-2 inventory management system for color mixing demo with the following features:
  - MongoDB-based inventory tracking for red, yellow, and blue paint stock levels
  - Automatic evaporation tracking based on elapsed time (configurable rate)
  - Pre-mixing stock availability validation to prevent experiments with insufficient paint
  - Automatic stock subtraction after each color mixing operation
  - Prefect maintenance flow for manual restock operations (`restock-maintenance`)
  - Prefect flow for inventory initialization/reset (`initialize-inventory`)
  - Prefect flow for inventory status monitoring (`check-inventory-status`)
  - Enhanced device flow with inventory tracking (`mix-color-with-inventory`)
  - Audit trail logging for all restock operations in MongoDB
  - Two new work queues: `maintenance` (priority 4) and `monitoring` (priority 5)
  - Command-line orchestrator scripts for easy restock operations
  - Comprehensive documentation in `src/ac_training_lab/ot-2/_scripts/INVENTORY_README.md`

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
