# Auto-Refresh Standards Design (v4.2.2)

## Overview

Automatically refresh coding standards that are older than a configurable threshold (default: 30 days) when they are accessed. This ensures users always receive current best practices without manual intervention.

## Architecture

### Components

1. **StandardsAccessService** - New service layer for all standard access
2. **Enhanced Metadata** - Track `last_accessed` and `last_updated` timestamps
3. **Configuration** - New settings for auto-refresh behavior
4. **Background Task Queue** - Optional async updates to avoid blocking requests

### Data Model Extensions

#### Enhanced Metadata Schema

```python
class StandardMetadata(BaseModel):
    """Extended metadata for standards with access tracking"""

    # Existing fields
    version: str
    created_at: datetime
    last_updated: datetime
    content_hash: str
    standards_count: int

    # New fields for auto-refresh
    last_accessed: Optional[datetime] = None
    access_count: int = 0
    auto_update_enabled: bool = True
    freshness_threshold_days: int = 30
    last_auto_update_attempt: Optional[datetime] = None
    last_auto_update_success: Optional[datetime] = None
    auto_update_failures: int = 0
```

### Service Architecture

```
┌─────────────────────────────────────────┐
│         API Router Layer                │
│  (standards.py, audit.py, etc.)         │
└──────────────────┬──────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────┐
│     StandardsAccessService (NEW)        │
│  ┌──────────────────────────────────┐   │
│  │ get_standard()                   │   │
│  │   ├─ Check freshness             │   │
│  │   ├─ Trigger refresh if stale    │   │
│  │   └─ Update access metadata      │   │
│  ├──────────────────────────────────┤   │
│  │ _needs_refresh()                 │   │
│  │ _schedule_background_refresh()   │   │
│  │ _update_access_metadata()        │   │
│  └──────────────────────────────────┘   │
└──────────────────┬──────────────────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
┌───────────────┐    ┌────────────────────┐
│  Standards    │    │  Standards         │
│  Research     │    │  Sync              │
│  Service      │    │  Service           │
│  (update_     │    │  (metadata         │
│   standard)   │    │   tracking)        │
└───────────────┘    └────────────────────┘
```

## Implementation Details

### 1. Configuration Settings

```python
# config/settings.py

class Settings(BaseSettings):
    # ... existing settings ...

    # Auto-refresh configuration
    ENABLE_AUTO_REFRESH_ON_ACCESS: bool = True
    STANDARD_FRESHNESS_THRESHOLD_DAYS: int = 30
    AUTO_REFRESH_MODE: str = "background"  # or "blocking"
    AUTO_REFRESH_MAX_CONCURRENT: int = 3
    AUTO_REFRESH_RETRY_ATTEMPTS: int = 2
    AUTO_REFRESH_RETRY_DELAY_SECONDS: int = 60
    AUTO_REFRESH_USE_DEEP_RESEARCH: bool = True
```

### 2. StandardsAccessService

**File**: `services/standards_access_service.py`

```python
class StandardsAccessService:
    """Service for accessing standards with automatic refresh"""

    async def get_standard(
        self,
        standard_id: str,
        force_refresh: bool = False,
        skip_auto_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get a standard with automatic freshness checking.

        Args:
            standard_id: Standard identifier
            force_refresh: Force refresh even if not stale
            skip_auto_refresh: Skip auto-refresh (for admin/testing)

        Returns:
            Standard content with metadata
        """

    async def _needs_refresh(self, standard: Dict[str, Any]) -> bool:
        """Check if standard needs refresh based on age"""

    async def _refresh_standard(
        self,
        standard_id: str,
        mode: str = "background"
    ) -> None:
        """Trigger standard refresh (blocking or background)"""

    async def _update_access_metadata(
        self,
        standard_id: str
    ) -> None:
        """Update last_accessed and access_count"""
```

### 3. Metadata Enhancement

Extend `.sync_metadata.json` structure:

```json
{
  "python/coding_standards_v1.0.0.md": {
    "path": "/path/to/standard.md",
    "last_modified": 1756575060.5619895,
    "content_hash": "86973f...",
    "standards_count": 0,

    // NEW FIELDS
    "last_accessed": "2025-11-16T08:00:00Z",
    "access_count": 142,
    "auto_update_enabled": true,
    "freshness_threshold_days": 30,
    "last_auto_update_attempt": "2025-11-15T10:30:00Z",
    "last_auto_update_success": "2025-11-15T10:32:00Z",
    "auto_update_failures": 0
  }
}
```

### 4. Background Task Queue (Optional)

For `AUTO_REFRESH_MODE = "background"`:

```python
# services/background_tasks.py

class BackgroundRefreshQueue:
    """Manage background standard refresh tasks"""

    def __init__(self):
        self.queue = asyncio.Queue()
        self.workers = []
        self.max_concurrent = settings.AUTO_REFRESH_MAX_CONCURRENT

    async def schedule_refresh(self, standard_id: str) -> str:
        """Add refresh task to queue"""

    async def worker(self):
        """Background worker to process refresh tasks"""

    async def get_queue_status(self) -> Dict[str, Any]:
        """Get current queue status and metrics"""
```

## Update Flow

### Blocking Mode (`AUTO_REFRESH_MODE = "blocking"`)

```
1. User requests standard
2. StandardsAccessService.get_standard() called
3. Check: Is standard > 30 days old?
   ├─ No  → Return standard immediately
   └─ Yes →
       4. Log: "Auto-refreshing stale standard: {id}"
       5. Call: research_service.update_standard(use_deep_research=True)
       6. Wait for completion (may take 30-60s with deep research)
       7. Update metadata (last_updated, last_accessed)
       8. Return refreshed standard
9. Update: last_accessed timestamp
```

### Background Mode (`AUTO_REFRESH_MODE = "background"`)

```
1. User requests standard
2. StandardsAccessService.get_standard() called
3. Check: Is standard > 30 days old?
   ├─ No  → Return standard immediately
   └─ Yes →
       4. Schedule: background_queue.schedule_refresh(standard_id)
       5. Return: Current version of standard (don't wait)
6. Update: last_accessed timestamp
7. Return to user

// Meanwhile, in background:
8. Background worker picks up task
9. Call: research_service.update_standard(use_deep_research=True)
10. On success: Update metadata
11. On failure: Increment failure counter, retry if < max_attempts
```

## Configuration Options

### Per-Standard Override

Allow disabling auto-refresh for specific standards:

```python
# In standard frontmatter or metadata
auto_update_enabled: false
freshness_threshold_days: 90  # Override default 30 days
```

### Global Kill Switch

Environment variable to disable all auto-refresh:

```bash
ENABLE_AUTO_REFRESH_ON_ACCESS=false
```

## Metrics & Monitoring

Track auto-refresh metrics:

```python
class AutoRefreshMetrics:
    total_accesses: int
    stale_standards_detected: int
    refresh_attempts: int
    refresh_successes: int
    refresh_failures: int
    avg_refresh_duration_seconds: float
    standards_by_age: Dict[str, int]  # Histogram
```

Expose via `/api/v1/metrics/auto-refresh` endpoint.

## Benefits

1. **Always Current**: Users receive latest best practices
2. **Transparent**: Happens automatically in background
3. **Versioned**: All changes tracked via existing versioning system
4. **Quality**: Uses deep research mode for high-quality updates
5. **Configurable**: Flexible threshold and mode settings
6. **Non-Disruptive**: Background mode returns immediately
7. **Auditable**: Full metrics and logging

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| High API costs (Gemini calls) | Financial | Rate limiting, max concurrent updates |
| Slow response times (blocking mode) | UX | Use background mode by default |
| Update failures | Stale data | Retry logic, failure counting, fallback to current |
| Breaking changes in updates | Compatibility | Version archiving, rollback capability |
| Race conditions (concurrent access) | Data corruption | Locking, transaction handling |

## Testing Strategy

### Unit Tests
- `test_needs_refresh()` - Age calculation logic
- `test_metadata_update()` - Access tracking
- `test_refresh_eligibility()` - Business rules

### Integration Tests
- `test_blocking_refresh_flow()` - Full blocking flow
- `test_background_refresh_flow()` - Background queue
- `test_concurrent_access()` - Race conditions
- `test_failure_handling()` - Error scenarios

### Performance Tests
- `test_response_time_blocking()` - Latency impact
- `test_queue_throughput()` - Background processing
- `test_concurrent_updates()` - Scalability

## Rollout Plan

### Phase 1: Infrastructure (Week 1)
- [ ] Implement StandardsAccessService
- [ ] Enhance metadata schema
- [ ] Add configuration settings
- [ ] Unit tests

### Phase 2: Core Functionality (Week 1)
- [ ] Implement blocking mode
- [ ] Implement background mode
- [ ] Background task queue
- [ ] Integration tests

### Phase 3: API Integration (Week 1)
- [ ] Update standards router
- [ ] Update audit router
- [ ] Metrics endpoint
- [ ] API documentation

### Phase 4: Testing & Deployment (Week 1)
- [ ] Performance testing
- [ ] Security review
- [ ] Documentation
- [ ] Feature flag rollout

## API Changes

### New Endpoints

```python
# Get auto-refresh status for a standard
GET /api/v1/standards/{standard_id}/refresh-status

# Manually trigger refresh
POST /api/v1/standards/{standard_id}/refresh

# Get auto-refresh metrics
GET /api/v1/metrics/auto-refresh

# Update auto-refresh settings for a standard
PATCH /api/v1/standards/{standard_id}/auto-refresh-settings
```

### Modified Endpoints

All existing `GET /api/v1/standards/*` endpoints will:
- Update `last_accessed` timestamp
- Check freshness and trigger refresh if needed
- Return quickly (background mode) or wait (blocking mode)

No breaking changes - all endpoints remain backward compatible.

## Success Criteria

- [ ] Standards >30 days old auto-refresh on access
- [ ] Background mode response time <500ms
- [ ] 95% of refresh attempts succeed
- [ ] Zero data loss from concurrent updates
- [ ] API cost increase <20%
- [ ] Test coverage >80% for new code
- [ ] Documentation complete

## Related Issues

- GitHub Issue #8: Auto-refresh standards older than 30 days on access
- v4.2.0: Deep Research Mode integration
- Standards Versioning System

---

**Version**: 1.0.0
**Author**: Code Standards Auditor Team
**Date**: November 16, 2025
**Status**: Design Approved - Ready for Implementation
