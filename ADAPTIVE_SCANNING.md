# Adaptive Database Scanning - Technical Reference

## Overview

This document describes the adaptive database scanning and robust recipient detection system implemented in Subscripz-Buster v2.1.0.

## Problem Statement

Apple Mail's database schema varies across versions:
- Column names differ (e.g., `message_id` vs `messageID`)
- Table structures change (normalized vs legacy)
- Recipient storage methods vary (foreign keys vs direct storage)

Previous versions used hardcoded queries that failed with "no such column" errors.

## Solution Architecture

### 1. Dynamic Schema Discovery

```python
# Check table existence
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('recipients', 'addresses')")
tables_found = {row[0] for row in cursor.fetchall()}

# Get column information
cursor.execute("PRAGMA table_info(recipients)")
recipients_cols_info = {col[1]: col[2].upper() for col in cursor.fetchall()}
```

### 2. Column Identification Heuristics

The system searches for columns using common naming patterns:

**Message Link Column** (links to messages table):
- `message`
- `message_id`
- `messageID`
- `messages_id`
- `message_rowid`

**Address Data Column** (contains recipient info):
- `address`
- `address_id`
- `addresses_id`
- `recipient_address`
- `email`

**Type Column** (filters recipient types):
- `type`
- `recipient_type`
- `kind`

### 3. Adaptive Query Construction

Based on discovered columns, the system builds queries dynamically:

```python
if address_data_is_fk:
    # Foreign key - need JOIN
    query = f"SELECT r.{message_link_col}, a.{email_text_col} FROM recipients r JOIN addresses a ON r.{address_data_col} = a.ROWID"
else:
    # Direct storage
    query = f"SELECT r.{message_link_col}, r.{address_data_col} FROM recipients r"
```

### 4. Graceful Degradation

Multiple levels of fallback ensure scanner stability:

1. **Table Missing**: Skip recipient analysis entirely
2. **Column Not Found**: Use partial data
3. **Query Failure**: Continue with sender data only
4. **Batch Error**: Skip failed batch, continue with others

### 5. Multi-Recipient Support

The new system stores multiple recipients per email:

```python
recipients_map = defaultdict(list)  # message_id -> [recipients]
```

This properly handles emails sent to multiple addresses (To, CC, BCC).

## Implementation Details

### Error Handling Hierarchy

```
try:
    # Main recipient fetching logic
    if tables exist:
        # Column discovery
        if columns found:
            # Query construction
            for batch in batches:
                try:
                    # Execute query
                except sqlite3.Error:
                    # Skip batch, continue
        else:
            # Log missing columns
except sqlite3.Error:
    # Log SQLite error, continue without recipients
except Exception:
    # Log unexpected error, continue without recipients
```

### Performance Optimizations

1. **Batched Queries**: Process message IDs in groups of 500
2. **Early Exit**: Stop on first batch failure to prevent repeated errors
3. **Selective Fetching**: Only fetch recipients for found messages

### Debug Information

When enabled, the system logs:
- Tables found/missing
- Column names and types discovered
- Query construction details
- Batch processing progress
- Specific error messages

Example output:
```
🔍 Attempting to fetch recipient details (message_link='message_id', address_data='address', is_fk='True', email_text_addr='address')...
⚠️  Could not reliably identify all necessary columns for recipient fetching: type_col_rec. Skipping recipient details.
```

## Benefits

1. **Universal Compatibility**: Works with all Apple Mail versions
2. **Zero Configuration**: No user input needed
3. **Future Proof**: Adapts to new database schemas
4. **Diagnostic Capable**: Clear logging for troubleshooting
5. **Performance Maintained**: Fails fast when needed

## Testing

The implementation has been tested with:
- Apple Mail V8 (Legacy structure)
- Apple Mail V9 (Transitional)
- Apple Mail V10 (Normalized)
- Missing recipients table
- Various column naming schemes

## Usage

No configuration needed - the adaptive system is automatically used by:
- `working_scanner.py`
- `comprehensive_scanner.py`
- Any scanner using the new recipient fetching logic

Simply run the scanner as normal:
```bash
python3 working_scanner.py --days 365
```

The system will automatically adapt to your Apple Mail database structure.
