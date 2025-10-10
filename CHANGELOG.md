# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Minimal Sparkplug B over MQTT orchestration solution for OT-2
- Three-file example: decorator.py, device.py, orchestrator.py
- Auto-discovery of device capabilities via Sparkplug B Birth certificates
- @sparkplug_task decorator for simple function registration
- Complete example showing "Hello, {name}!" remote execution

### Removed
- FastAPI-based orchestration (has same dependency conflicts as Prefect)
- Cloud deployment guides for Railway and Google Cloud Run  
- Security guides for HTTPS/JWT (not applicable to MQTT-only solution)
- All FastAPI examples and documentation

### Fixed
- Addressed FastAPI having same pydantic/anyio/jsonschema conflicts as Prefect
- Confirmed Sparkplug B has minimal dependencies with no Opentrons conflicts

## [0.1.0] - 2024-12-19

### Added
- Sparkplug B MQTT orchestration framework for OT-2
- Minimal decorator-based task registration
- Device and orchestrator example implementations
- Compatible with Opentrons package (no dependency conflicts)

### Security
- TLS/SSL encryption support via MQTT over TLS
- Username/password authentication for MQTT broker
