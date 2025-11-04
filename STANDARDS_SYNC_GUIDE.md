# Standards Synchronization Guide

**Version**: 1.0
**Date**: November 4, 2025
**Status**: Active

---

## Overview

The Standards Synchronization feature automatically keeps your Neo4j database in sync with markdown standards files on disk. It detects file changes and performs incremental updates without requiring full reimports.

### Key Features

✅ **Automatic Background Sync** - Runs every hour when the server is running
✅ **Incremental Updates** - Only processes changed files
✅ **Manual Trigger** - API endpoint for on-demand synchronization
✅ **Change Detection** - Uses file hashes to detect modifications
✅ **Multi-Language Support** - Handles standards for all languages
✅ **Metadata Tracking** - Maintains sync history and status

---

## Architecture

### Components

1. **StandardsSyncService** (`services/standards_sync_service.py`)
   - Core synchronization logic
   - File change detection
   - Incremental update management

2. **ScheduledSyncService** (`services/standards_sync_service.py`)
   - Background task scheduler
   - Periodic synchronization (configurable interval)
   - Lifecycle management

3. **Manual Sync Script** (`scripts/sync_standards.py`)
   - Standalone command-line tool
   - Force sync option
   - Detailed status reporting

4. **API Endpoints**
   - `GET /api/v1/sync/status` - Get sync status
   - `POST /api/v1/sync/trigger` - Manually trigger sync

### How It Works

```
┌────────────────────┐
│  Markdown Files    │
│  /standards/       │
│  - python/         │
│  - java/           │
│  - general/        │
└──────┬─────────────┘
       │
       │ (1) Discover files
       │ (2) Calculate hashes
       │ (3) Compare with cache
       ▼
┌────────────────────┐
│  Sync Service      │
│  - Detect changes  │
│  - Parse markdown  │
│  - Update database │
└──────┬─────────────┘
       │
       │ (4) Create/Update/Delete
       │     standards nodes
       ▼
┌────────────────────┐
│   Neo4j Database   │
│   128 Standards    │
│   (Currently)      │
└────────────────────┘
```

### Metadata Tracking

Metadata is stored in `.sync_metadata.json` in the standards directory:

```json
{
  "python/fastapi_async_standards_v1.0.0.md": {
    "path": "/path/to/file.md",
    "last_modified": 1730745600.0,
    "content_hash": "abc123...",
    "standards_count": 64
  }
}
```

---

## Usage

### 1. Automatic Synchronization (Recommended)

The sync service starts automatically when you run the test server:

```bash
python3 test_server.py
```

**Configuration**:
- Interval: 1 hour (3600 seconds)
- Runs in background
- Logs changes to console

**Startup Logs**:
```
✅ Neo4j connection established
✅ Standards sync service initialized (1 hour interval)
```

### 2. Manual Synchronization

#### Via API

Check sync status:
```bash
curl http://localhost:8000/api/v1/sync/status
```

Response:
```json
{
  "enabled": true,
  "files_tracked": 8,
  "standards_in_files": 128,
  "standards_in_database": 128,
  "is_synchronized": true,
  "last_sync": "2025-11-04T10:07:36",
  "scheduled": true,
  "interval_seconds": 3600,
  "running": true
}
```

Trigger manual sync:
```bash
curl -X POST http://localhost:8000/api/v1/sync/trigger
```

Force full re-import:
```bash
curl -X POST "http://localhost:8000/api/v1/sync/trigger?force=true"
```

#### Via Command Line

Basic sync:
```bash
python3 scripts/sync_standards.py
```

Force sync (reimport all):
```bash
python3 scripts/sync_standards.py --force
```

Custom standards directory:
```bash
python3 scripts/sync_standards.py --standards-dir /path/to/standards
```

Verbose output:
```bash
python3 scripts/sync_standards.py --verbose
```

---

## Common Scenarios

### Scenario 1: Adding New Standards File

1. Create new markdown file in standards directory
2. Sync automatically detects it within 1 hour (or trigger manually)
3. Standards are parsed and imported
4. Database updated

**Example**:
```bash
# Add file
echo "## Security Standards..." > standards/python/security_v1.0.0.md

# Trigger sync (optional - will happen automatically)
python3 scripts/sync_standards.py

# Result: New standards added to database
```

### Scenario 2: Modifying Existing Standards

1. Edit markdown file
2. Save changes
3. Sync detects file change (via hash)
4. Old standards from that file are deleted
5. Updated standards are imported

**Note**: Standards are tracked by `file_source` property in Neo4j, allowing clean updates.

### Scenario 3: Deleting Standards File

1. Delete markdown file
2. Sync detects missing file
3. All standards from that file are removed from database
4. Metadata updated

### Scenario 4: Emergency Updates

Need immediate sync?

```bash
# Option 1: Manual script
python3 scripts/sync_standards.py --force

# Option 2: API call
curl -X POST "http://localhost:8000/api/v1/sync/trigger?force=true"

# Option 3: Restart server (triggers initial sync)
```

---

## Configuration

### Sync Interval

Change the sync interval by modifying `test_server.py`:

```python
scheduled_sync = ScheduledSyncService(
    sync_service=sync_service,
    interval_seconds=1800  # 30 minutes instead of 1 hour
)
```

### Standards Directory

Default: Set in `config/settings.py`
```python
STANDARDS_BASE_PATH = "/Volumes/FS001/pythonscripts/standards"
```

Override:
- Environment variable: `STANDARDS_BASE_PATH`
- Command line: `--standards-dir` flag

---

## Monitoring

### Logs

Sync logs are output to console with structured logging:

```json
{
  "event": "Starting standards synchronization",
  "force": false,
  "level": "info"
}
```

```json
{
  "event": "Detected changes",
  "added": 1,
  "modified": 2,
  "deleted": 0,
  "level": "info"
}
```

```json
{
  "event": "Synchronization complete",
  "stats": {
    "files_added": 1,
    "standards_added": 15,
    "duration_seconds": 0.85
  },
  "level": "info"
}
```

### Metrics

Query sync status via API:

```bash
# Get full status
curl http://localhost:8000/api/v1/sync/status | jq

# Check if synchronized
curl http://localhost:8000/api/v1/sync/status | jq '.is_synchronized'

# Get last sync time
curl http://localhost:8000/api/v1/sync/status | jq '.last_sync'
```

---

## Troubleshooting

### Sync Not Running

**Symptoms**: No automatic syncs happening

**Checks**:
1. Is Neo4j connected?
   ```bash
   curl http://localhost:8000/api/v1/health | jq '.services.neo4j'
   ```

2. Is sync service enabled?
   ```bash
   curl http://localhost:8000/api/v1/sync/status | jq '.enabled'
   ```

3. Check logs for errors:
   ```bash
   # Look for "Standards sync initialization failed"
   ```

**Solutions**:
- Verify `STANDARDS_BASE_PATH` exists
- Check Neo4j connection
- Restart server

### Standards Not Updating

**Symptoms**: File changes not reflected in database

**Checks**:
1. Verify file is in standards directory tree
2. Check file has "**Standards**:" sections
3. Verify sync detected changes:
   ```bash
   python3 scripts/sync_standards.py --verbose
   ```

**Solutions**:
- Force sync to rebuild:
  ```bash
  python3 scripts/sync_standards.py --force
  ```
- Check markdown format is correct
- Verify file permissions

### Database Out of Sync

**Symptoms**: `is_synchronized: false` in status

**Cause**: Standards count in files doesn't match database count

**Solutions**:
1. Run force sync:
   ```bash
   python3 scripts/sync_standards.py --force
   ```

2. Check for orphaned standards:
   ```cypher
   MATCH (s:Standard)
   WHERE NOT exists(s.file_source)
   RETURN count(s)
   ```

3. Clean and rebuild:
   ```cypher
   MATCH (s:Standard) DELETE s
   ```
   ```bash
   python3 scripts/import_standards.py
   ```

---

## Performance

### Benchmarks

**Initial Import** (64 standards):
- Time: ~1 second
- Operation: Full parse + import

**Incremental Sync** (no changes):
- Time: ~0.2 seconds
- Operation: File discovery + hash comparison

**Update Sync** (1 file changed):
- Time: ~0.5 seconds
- Operation: Delete old + import new

### Optimization Tips

1. **Reduce Sync Frequency** - If standards rarely change:
   ```python
   interval_seconds=7200  # 2 hours
   ```

2. **Disable When Not Needed** - For production:
   ```bash
   # Run sync only via cron
   # Don't start scheduled sync in server
   ```

3. **Batch Changes** - Make multiple file edits, then trigger once:
   ```bash
   # Edit multiple files
   # Then:
   curl -X POST http://localhost:8000/api/v1/sync/trigger
   ```

---

## Cron Integration

Run sync every 6 hours via cron:

```bash
# Edit crontab
crontab -e

# Add line:
0 */6 * * * cd /path/to/code-standards-auditor && python3 scripts/sync_standards.py >> logs/sync.log 2>&1
```

---

## Best Practices

### Do's ✅

- Use automatic sync for development
- Use cron for production
- Monitor sync logs regularly
- Keep standards files well-formatted
- Use force sync after major changes
- Test sync before committing file changes

### Don'ts ❌

- Don't manually edit Neo4j standards (use files as source of truth)
- Don't delete `.sync_metadata.json` (unless rebuilding)
- Don't set sync interval too low (< 5 minutes)
- Don't modify standards during sync
- Don't ignore sync errors

---

## API Reference

### GET /api/v1/sync/status

Get current synchronization status.

**Response**:
```json
{
  "enabled": true,
  "files_tracked": 8,
  "standards_in_files": 128,
  "standards_in_database": 128,
  "last_sync": "2025-11-04T10:07:36",
  "metadata_file": "/path/.sync_metadata.json",
  "is_synchronized": true,
  "scheduled": true,
  "interval_seconds": 3600,
  "running": true
}
```

### POST /api/v1/sync/trigger

Manually trigger synchronization.

**Query Parameters**:
- `force` (boolean, optional): Force full reimport

**Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/sync/trigger?force=false"
```

**Response**:
```json
{
  "success": true,
  "stats": {
    "files_added": 1,
    "files_updated": 0,
    "files_deleted": 0,
    "standards_added": 15,
    "standards_updated": 0,
    "standards_deleted": 0,
    "last_sync": "2025-11-04T10:15:30",
    "duration_seconds": 0.85
  }
}
```

---

## Current Status

✅ **Operational** - 128 standards synchronized
✅ **Automatic Sync** - Running every hour
✅ **Manual Sync** - Available via API and CLI
✅ **Change Detection** - Working correctly

**Last Full Sync**: 2025-11-04 10:07:36
**Standards Count**: 128
**Files Tracked**: 8
**Sync Interval**: 3600 seconds (1 hour)

---

**Created**: 2025-11-04
**Author**: Code Standards Auditor Team
**Version**: 1.0
