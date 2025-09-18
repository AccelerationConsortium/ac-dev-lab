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