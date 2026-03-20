# Changelog

## [0.3.1] - 2026-03-20

### Fixed

- `create_brand()` / `ensure_brand()` sent `url` field but API expects `website` — param renamed to `website`
- `include_financial` documented as `"yes"/"no"` string — corrected to `bool` (matches API schema)
- Response example `credits_used: 2` corrected to `1` (actual credit cost per report)
- 16 type annotations: `str = None` → `Optional[str] = None` across all methods

### Changed

- Repo restructured: SDK package moved to `client/surmado/`, tests to `client/tests/`
- README rewritten as canonical external entry point with repo structure map and API surface table
- `.gitignore` updated: added `__pycache__/`, `.pytest_cache/`; removed stale `testing/` entry

### Added

- `/integrations` directory with guides for webhooks, Zapier, Make, and n8n

### Removed

- `/testing` directory (gitignored scratch scripts with hardcoded data)

## [0.3.0] - 2026-03-04

### Added

- `bundle()` method for full analysis (Signal + Scan + Solutions in one call)

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
