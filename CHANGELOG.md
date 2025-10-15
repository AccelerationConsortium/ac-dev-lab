# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Ultra-minimal MQTT orchestration solution for OT-2 in `sparkplug_minimal/`
- Single `decorator.py` file that handles all MQTT complexity internally
- Simplified `device.py` and `orchestrator.py` with clean API (no MQTT boilerplate visible)
- @sparkplug_task decorator that makes remote calls look like local calls
- Only dependency: paho-mqtt (no Sparkplug B wrapper needed)

### Changed
- Completely rewrote decorator to hide all MQTT implementation details
- Device code now looks like normal Python with just decorator usage
- Orchestrator calls remote functions as if they were local
- Removed mqtt-spb-wrapper dependency for maximum simplicity

### Removed
- All extra files from examples/ directory
- Extra documentation files (QUICK_START.md, MIGRATION_GUIDE.md, etc.)
- Sparkplug B library dependency (using plain MQTT instead)
- FastAPI-based orchestration (has same dependency conflicts as Prefect)
- Cloud deployment guides
- All complex boilerplate from device and orchestrator files

### Fixed
- Addressed FastAPI having same pydantic/anyio/jsonschema conflicts as Prefect
- Simplified implementation to truly minimal three-file solution
- Made code "look and feel" like normal Python instead of MQTT-heavy

## [0.1.0] - 2024-12-19

### Added
- Initial MQTT orchestration framework for OT-2
- Decorator-based task registration
- Device and orchestrator example implementations
- Compatible with Opentrons package (no dependency conflicts)

### Security
- TLS/SSL encryption support via MQTT over TLS
- Username/password authentication for MQTT broker
