# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **OpenFlexure Microscope Video Recording**: Added comprehensive video recording functionality for capturing microscope feeds during experiments
  - `start_video_recording()` method for continuous recording
  - `stop_video_recording()` method to end recording and save video
  - `record_video_for_duration()` convenience method for timed recording
  - Configurable FPS (frames per second) settings (1-10 recommended)
  - Automatic timestamped filename generation
  - Animated GIF output format for universal compatibility
  - Error handling for connection issues during recording
  - Thread-safe recording implementation
  - GUI controls in Streamlit interface for video recording
  - Standalone command-line video recorder script (`video_recorder.py`)
  - Demonstration script with mock data (`demo_video_recording.py`)
  - Comprehensive test suite for video recording functionality
  - Updated documentation with usage examples and troubleshooting guide

### Date
- 2025-01-26

### Purpose
- Enables video capture during vibration testing and other experiments (addresses issue #216)
- Provides visual documentation of microscope behavior over time
- Supports research workflows requiring time-lapse microscopy