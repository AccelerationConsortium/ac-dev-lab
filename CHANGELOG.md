# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- BO / Prefect HiTL Slack integration tutorial (2025-01-18)
  - Created `scripts/prefect_scripts/bo_hitl_slack_tutorial.py` - Complete Bayesian Optimization workflow with human-in-the-loop evaluation via Slack
  - Added `scripts/prefect_scripts/test_bo_workflow.py` - Demonstration script showing BO workflow without dependencies
  - Added `scripts/prefect_scripts/README_BO_HITL_Tutorial.md` - Setup instructions and documentation
  - Implements Ax Service API for Bayesian optimization with Branin function
  - Integrates Prefect interactive workflows with pause_flow_run for human input
  - Provides Slack notifications for experiment suggestions
  - Supports evaluation via HuggingFace Branin space
  - Includes mock implementations for development without heavy dependencies
  - Follows minimal working example pattern with 4-5 optimization iterations
# CHANGELOG

## [Unreleased]
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
