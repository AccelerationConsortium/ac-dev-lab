# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- BO / Prefect HiTL Slack integration tutorial (2025-12-01)
  - Added `scripts/prefect_scripts/bo_hitl_slack_tutorial.py` - Bayesian Optimization with human-in-the-loop evaluation via Slack
  - Uses Ax Service API for Bayesian optimization
  - Integrates Prefect interactive workflows with pause_flow_run
  - Slack notifications for experiment suggestions
  - MongoDB Atlas storage for experiment data
  - Evaluation via HuggingFace Branin space

### Changed
- Support for both `rpicam-vid` (Raspberry Pi OS Trixie) and `libcamera-vid` (Raspberry Pi OS Bookworm) camera commands

### Fixed
- Ctrl+C interrupt handling in `src/ac_training_lab/picam/device.py`

## [1.1.0] - 2024-06-11
### Added
- Imperial (10-32 thread) alternative design to SEM door automation bill of materials

### Notes
- All components sourced from McMaster-Carr for reliability and reproducibility
