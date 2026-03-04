# Changelog

## [0.2.0] - 2026-03-04

### Changed
- Removed `tier` parameter from all methods — API now uses a single tier
- Fixed error handling to match actual API error format (`detail.error.message`)
- Fixed quickstart.py broken `api_key=""` initialization
- Updated pricing to flat $50/report across all products

### Added
- `get_report_data()` method for raw report data access with field filtering
- `list_brands()`, `create_brand()`, `ensure_brand()` brand management methods
- `test_auth()` method for free API key validation
- `_extract_error_message()` for consistent error parsing across all status codes
- Explicit `RateLimitError` (429) and `ValidationError` (400) handling
- CHANGELOG.md

### Removed
- `tier` parameter from `signal()`, `scan()`, `signal_rerun()`, `scan_rerun()`

## [0.1.2] - 2025-12-05

- Initial public release on PyPI
