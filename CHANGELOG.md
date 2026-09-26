# Changelog

All notable changes to Relay are documented here.

## [1.1.1] - 2026-09-26

### Fixed
- A param whose value contains a colon, such as `redirect=https://example.com` or `time=10:30`, was split at the colon; lines now split on whichever of `:` or `=` comes first.
- A URL typed as `localhost:8080/path` was sent without `http://` and failed; any address without an explicit `scheme://` now gets one.

### Added
- Behavioural tests covering the areas above and the rest of the core.

## [1.1.0] - 2026-09-26

### Added
- Release builds for macOS (Apple Silicon) and Linux (x86_64) alongside Windows, with one `SHA256SUMS.txt` per release.
- `--url` and `--method` arguments that open Relay with a request filled in, used by Switchyard's tool handoff.
- The application icon, which the Windows executable was missing.
- A screenshot of the running app in the README.

### Changed
- CI builds the macOS and Linux packages on every push.

## [1.0.0] - 2026-09-16

### Added
- Polished public release documentation and screenshot.
- Cross-platform CI checks plus Windows executable build artifact.
- Automated tagged GitHub Release workflow with SHA256 checksum.
- Issue templates and security/reporting guidance.

### Current product
- GET, POST, PUT, PATCH, DELETE, HEAD, and OPTIONS
- Query parameters, headers, and request bodies
- Formatted response body, headers, status, and timing
- Local request history and saved requests
- cURL export
- Built-in localhost mock endpoint
