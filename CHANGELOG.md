# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **OT-2 Orchestration Framework** (2024-12-19)
  - FastAPI-based orchestration system compatible with Opentrons package
  - MQTT-based orchestration system with decorator syntax
  - Complete solution to Prefect/Opentrons pydantic version conflicts
  - `@task` and `@mqtt_task` decorators for function registration
  - Remote task execution capabilities over HTTP and MQTT
  - Auto-generated API documentation via FastAPI
  - JWT authentication and HTTPS/TLS security support

- **Cloud Deployment Solutions** (2024-12-19)
  - Railway.app deployment configuration and examples
  - Google Cloud Run deployment guide
  - Complete security setup with HTTPS, JWT auth, SSL certificates
  - Cost comparison analysis vs Prefect Cloud
  - Production-ready Docker configurations

- **MicroPython Integration** (2024-12-19)
  - Native mqtt_as.py support for Pico W and ESP32 microcontrollers
  - Complete device.py/orchestrator.py architecture examples
  - Hybrid architecture recommendations (FastAPI + MQTT)
  - Memory-efficient implementations for microcontroller environments

- **Comprehensive Documentation** (2024-12-19)
  - Security guide with HTTPS, VPN, and firewall configuration
  - Migration guides from Prefect workflows
  - Quick start guide and requirements files
  - FastAPI vs MQTT technical comparison
  - Verification tests with real communication protocols

### Fixed
- Resolved pydantic version incompatibility between Prefect v2 and Opentrons v1
- Eliminated dependency conflicts for OT-2 laboratory automation workflows

### Security
- Added HTTPS/TLS encryption support for FastAPI deployments
- Implemented JWT authentication with role-based access control
- Added TLS/SSL encryption for MQTT communications
- Included VPN integration guides for secure remote access