# Changelog

All notable changes to Subscripz-Buster will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.1.0] - 2024-12-20

### Added
- **Adaptive Database Scanning**: Intelligent schema discovery that automatically detects and adapts to different Apple Mail database structures (V8-V10+)
- **Robust Recipient Detection**: Dynamic recipient analysis using PRAGMA table introspection and column heuristics
- **Enhanced Logging**: Comprehensive MCP server logging with detailed operation tracking
- **Dry-Run Mode**: Preview scan scope before processing with `--dry-run` flag
- **Standardized JSON Output**: Consistent data interchange format across all scanners
- **Batch Processing**: Efficient handling of large email datasets with 500-message batches
- **Graceful Degradation**: Continues operation even when recipient data is unavailable

### Changed
- `working_scanner.py` now uses dynamic schema discovery instead of hardcoded queries
- Recipient fetching uses intelligent heuristics to identify column names
- Recipients stored as lists to support multiple recipients per email
- Improved error handling with detailed logging for debugging

### Fixed
- "no such column: address_id" errors in various database versions
- SQL query failures when recipients table structure differs
- Memory issues with large email datasets
- Compatibility issues with Apple Mail V10+ normalized databases

### Technical Details
- Implements the complete solution from `fixes_ideas.txt`
- Uses `defaultdict(list)` for recipients_map to handle multiple recipients
- Dynamic SQL query construction based on discovered schema
- Comprehensive try-except blocks with fallback strategies

## [2.0.0] - 2024-12-19

### Added
- Standardized data structures in `common_structures.py`
- JSON export support for all major scanners
- Comprehensive scanner showing ALL subscriptions
- Financial summary analyzer
- Duplicate finder with fuzzy matching
- Menu-driven launcher system

### Changed
- Complete refactor of scanner architecture
- Modular design with specialized scanners
- Improved duplicate detection algorithms

## [1.0.0] - 2024-12-18

### Added
- Initial release
- Basic email scanning functionality
- MCP server integration
- Excel export capability
- Simple duplicate detection
