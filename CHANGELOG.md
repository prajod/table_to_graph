# Changelog

All notable changes to this project will be documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and releases use semantic versioning.

## [Unreleased]

### Added

- Cross-platform GitHub Actions checks for Python 3.10 through 3.13 and Windows CMD.
- Public contribution, security, and conduct policies.
- A documented Windows/Python 3.13 tested environment.

### Changed

- Renamed the benchmark metric to target-token context hit rate.
- Made the quality command non-mutating and repository-wide.
- Migrated package metadata to standardized `[project]` fields.

### Fixed

- Removed Unicode emoji console output that could crash on Windows CP1252 terminals.
- Corrected benchmark package imports for static type checking.
