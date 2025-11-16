"""
Unit Tests for Standards Access Service

Tests auto-refresh functionality including:
- Access tracking
- Freshness detection
- Blocking and background refresh modes
- Retry logic
- Metrics tracking

Author: Code Standards Auditor
Date: November 16, 2025
Version: 1.0.0 (v4.2.2)
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from services.standards_access_service import (
    StandardsAccessService,
    StandardMetadata,
    RefreshMetrics,
    BackgroundRefreshQueue
)
from services.standards_research_service import StandardsResearchService


@pytest.fixture
def temp_standards_dir(tmp_path):
    """Create temporary standards directory"""
    standards_dir = tmp_path / "standards"
    standards_dir.mkdir()

    # Create a sample standard
    python_dir = standards_dir / "python"
    python_dir.mkdir()

    standard_file = python_dir / "test_standard_v1.0.0.md"
    standard_file.write_text("# Test Standard\n\nThis is a test standard.")

    # Create metadata file
    metadata = {
        "python/test_standard_v1.0.0.md": {
            "path": str(standard_file),
            "last_modified": standard_file.stat().st_mtime,
            "content_hash": "abc123",
            "standards_count": 1
        }
    }

    metadata_file = standards_dir / ".sync_metadata.json"
    metadata_file.write_text(json.dumps(metadata, indent=2))

    return standards_dir


@pytest.fixture
def mock_research_service():
    """Create mock research service"""
    service = AsyncMock(spec=StandardsResearchService)
    service.update_standard = AsyncMock(return_value={"version": "1.1.0"})
    return service


@pytest.fixture
async def access_service(temp_standards_dir, mock_research_service):
    """Create StandardsAccessService with mocked dependencies"""
    with patch('services.standards_access_service.settings') as mock_settings:
        mock_settings.STANDARDS_BASE_PATH = str(temp_standards_dir)
        mock_settings.ENABLE_AUTO_REFRESH_ON_ACCESS = True
        mock_settings.STANDARD_FRESHNESS_THRESHOLD_DAYS = 30
        mock_settings.AUTO_REFRESH_MODE = "blocking"
        mock_settings.AUTO_REFRESH_MAX_CONCURRENT = 3
        mock_settings.AUTO_REFRESH_RETRY_ATTEMPTS = 2
        mock_settings.AUTO_REFRESH_RETRY_DELAY_SECONDS = 1
        mock_settings.AUTO_REFRESH_USE_DEEP_RESEARCH = True

        service = StandardsAccessService(research_service=mock_research_service)
        yield service
        await service.stop()


class TestStandardMetadata:
    """Test StandardMetadata dataclass"""

    def test_to_dict(self):
        """Test conversion to dictionary"""
        metadata = StandardMetadata(
            path="/path/to/standard.md",
            last_modified=1700000000.0,
            content_hash="abc123",
            standards_count=5,
            last_accessed="2025-11-16T10:00:00",
            access_count=10
        )

        data = metadata.to_dict()

        assert data["path"] == "/path/to/standard.md"
        assert data["access_count"] == 10
        assert data["last_accessed"] == "2025-11-16T10:00:00"

    def test_from_dict(self):
        """Test creation from dictionary"""
        data = {
            "path": "/path/to/standard.md",
            "last_modified": 1700000000.0,
            "content_hash": "abc123",
            "standards_count": 5,
            "auto_update_enabled": True,
            "freshness_threshold_days": 30
        }

        metadata = StandardMetadata.from_dict(data)

        assert metadata.path == "/path/to/standard.md"
        assert metadata.auto_update_enabled is True
        assert metadata.freshness_threshold_days == 30


class TestRefreshMetrics:
    """Test RefreshMetrics tracking"""

    def test_avg_refresh_duration(self):
        """Test average refresh duration calculation"""
        metrics = RefreshMetrics()
        metrics.refresh_successes = 3
        metrics.total_refresh_duration_seconds = 90.0

        assert metrics.avg_refresh_duration_seconds == 30.0

    def test_avg_refresh_duration_no_successes(self):
        """Test average duration when no successes"""
        metrics = RefreshMetrics()
        assert metrics.avg_refresh_duration_seconds == 0.0

    def test_success_rate(self):
        """Test success rate calculation"""
        metrics = RefreshMetrics()
        metrics.refresh_attempts = 10
        metrics.refresh_successes = 8

        assert metrics.success_rate == 80.0

    def test_success_rate_no_attempts(self):
        """Test success rate when no attempts"""
        metrics = RefreshMetrics()
        assert metrics.success_rate == 0.0

    def test_to_dict(self):
        """Test conversion to dictionary"""
        metrics = RefreshMetrics(
            total_accesses=100,
            stale_standards_detected=5,
            refresh_attempts=5,
            refresh_successes=4,
            total_refresh_duration_seconds=120.0
        )

        data = metrics.to_dict()

        assert data["total_accesses"] == 100
        assert data["refresh_successes"] == 4
        assert data["avg_refresh_duration_seconds"] == 30.0
        assert data["success_rate"] == 80.0


class TestStandardsAccessService:
    """Test StandardsAccessService core functionality"""

    @pytest.mark.asyncio
    async def test_get_standard_fresh(self, access_service, temp_standards_dir):
        """Test getting a fresh standard (no refresh needed)"""
        standard_id = "python/test_standard_v1.0.0.md"

        # Standard is fresh (just created)
        result = await access_service.get_standard(standard_id)

        assert result["standard_id"] == standard_id
        assert "# Test Standard" in result["content"]
        assert result["was_refreshed"] is False
        assert result["metadata"]["access_count"] == 1
        assert result["metadata"]["last_accessed"] is not None

    @pytest.mark.asyncio
    async def test_get_standard_stale_blocking(
        self,
        access_service,
        temp_standards_dir,
        mock_research_service
    ):
        """Test getting a stale standard with blocking refresh"""
        standard_id = "python/test_standard_v1.0.0.md"

        # Make standard stale by backdating modification time
        standard_path = temp_standards_dir / standard_id
        old_timestamp = (datetime.now() - timedelta(days=35)).timestamp()

        # Update metadata to reflect old timestamp
        metadata = access_service.metadata_cache[standard_id]
        metadata.last_modified = old_timestamp

        result = await access_service.get_standard(standard_id)

        # Should have triggered refresh
        assert result["was_refreshed"] is True
        mock_research_service.update_standard.assert_called_once_with(
            standard_id=standard_id,
            use_deep_research=True
        )

        # Metrics should be updated
        assert access_service.metrics.stale_standards_detected == 1
        assert access_service.metrics.refresh_attempts == 1
        assert access_service.metrics.refresh_successes == 1

    @pytest.mark.asyncio
    async def test_get_standard_force_refresh(
        self,
        access_service,
        mock_research_service
    ):
        """Test force refresh regardless of age"""
        standard_id = "python/test_standard_v1.0.0.md"

        result = await access_service.get_standard(
            standard_id,
            force_refresh=True
        )

        # Should have refreshed even though standard is fresh
        assert result["was_refreshed"] is True
        mock_research_service.update_standard.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_standard_skip_auto_refresh(self, access_service, temp_standards_dir):
        """Test skipping auto-refresh"""
        standard_id = "python/test_standard_v1.0.0.md"

        # Make standard stale
        metadata = access_service.metadata_cache[standard_id]
        old_timestamp = (datetime.now() - timedelta(days=35)).timestamp()
        metadata.last_modified = old_timestamp

        result = await access_service.get_standard(
            standard_id,
            skip_auto_refresh=True
        )

        # Should NOT have refreshed
        assert result["was_refreshed"] is False
        assert access_service.metrics.stale_standards_detected == 0

    @pytest.mark.asyncio
    async def test_get_standard_not_found(self, access_service):
        """Test getting non-existent standard"""
        with pytest.raises(ValueError, match="Standard not found"):
            await access_service.get_standard("nonexistent/standard.md")

    @pytest.mark.asyncio
    async def test_access_tracking(self, access_service):
        """Test access count and timestamp tracking"""
        standard_id = "python/test_standard_v1.0.0.md"

        # Access standard multiple times
        for i in range(5):
            result = await access_service.get_standard(standard_id)
            assert result["metadata"]["access_count"] == i + 1

        # Verify last_accessed is recent
        last_accessed = result["metadata"]["last_accessed"]
        last_accessed_dt = datetime.fromisoformat(last_accessed)
        assert (datetime.now() - last_accessed_dt).seconds < 5

    @pytest.mark.asyncio
    async def test_needs_refresh_threshold(self, access_service):
        """Test freshness threshold logic"""
        metadata = StandardMetadata(
            path="/path/to/standard.md",
            last_modified=(datetime.now() - timedelta(days=35)).timestamp(),
            content_hash="abc123",
            standards_count=1,
            freshness_threshold_days=30
        )

        # Should need refresh (35 days > 30 day threshold)
        assert await access_service._needs_refresh(metadata) is True

    @pytest.mark.asyncio
    async def test_needs_refresh_fresh(self, access_service):
        """Test fresh standard doesn't need refresh"""
        metadata = StandardMetadata(
            path="/path/to/standard.md",
            last_modified=(datetime.now() - timedelta(days=15)).timestamp(),
            content_hash="abc123",
            standards_count=1,
            freshness_threshold_days=30
        )

        # Should NOT need refresh (15 days < 30 day threshold)
        assert await access_service._needs_refresh(metadata) is False

    @pytest.mark.asyncio
    async def test_needs_refresh_custom_threshold(self, access_service):
        """Test custom per-standard freshness threshold"""
        metadata = StandardMetadata(
            path="/path/to/standard.md",
            last_modified=(datetime.now() - timedelta(days=50)).timestamp(),
            content_hash="abc123",
            standards_count=1,
            freshness_threshold_days=90  # Custom threshold
        )

        # Should NOT need refresh (50 days < 90 day threshold)
        assert await access_service._needs_refresh(metadata) is False

    @pytest.mark.asyncio
    async def test_update_standard_settings(self, access_service):
        """Test updating auto-refresh settings for a standard"""
        standard_id = "python/test_standard_v1.0.0.md"

        # Update settings
        updated = access_service.update_standard_settings(
            standard_id,
            auto_update_enabled=False,
            freshness_threshold_days=60
        )

        assert updated["auto_update_enabled"] is False
        assert updated["freshness_threshold_days"] == 60

        # Verify in cache
        metadata = access_service.metadata_cache[standard_id]
        assert metadata.auto_update_enabled is False
        assert metadata.freshness_threshold_days == 60

    def test_update_standard_settings_not_found(self, access_service):
        """Test updating settings for non-existent standard"""
        with pytest.raises(ValueError, match="Standard not found"):
            access_service.update_standard_settings(
                "nonexistent/standard.md",
                auto_update_enabled=False
            )

    def test_get_metrics(self, access_service):
        """Test getting metrics"""
        # Simulate some activity
        access_service.metrics.total_accesses = 100
        access_service.metrics.stale_standards_detected = 5
        access_service.metrics.refresh_attempts = 5
        access_service.metrics.refresh_successes = 4

        metrics = access_service.get_metrics()

        assert metrics["total_accesses"] == 100
        assert metrics["stale_standards_detected"] == 5
        assert metrics["success_rate"] == 80.0

    def test_get_standard_metadata(self, access_service):
        """Test getting metadata for a standard"""
        standard_id = "python/test_standard_v1.0.0.md"

        metadata = access_service.get_standard_metadata(standard_id)

        assert metadata is not None
        assert metadata["path"].endswith("test_standard_v1.0.0.md")

    def test_get_standard_metadata_not_found(self, access_service):
        """Test getting metadata for non-existent standard"""
        metadata = access_service.get_standard_metadata("nonexistent/standard.md")
        assert metadata is None

    @pytest.mark.asyncio
    async def test_auto_update_disabled_per_standard(self, access_service):
        """Test that auto-update can be disabled per-standard"""
        standard_id = "python/test_standard_v1.0.0.md"

        # Disable auto-update for this standard
        access_service.update_standard_settings(
            standard_id,
            auto_update_enabled=False
        )

        # Make standard stale
        metadata = access_service.metadata_cache[standard_id]
        old_timestamp = (datetime.now() - timedelta(days=35)).timestamp()
        metadata.last_modified = old_timestamp

        result = await access_service.get_standard(standard_id)

        # Should NOT have refreshed (disabled)
        assert result["was_refreshed"] is False
        assert access_service.metrics.stale_standards_detected == 0


class TestBackgroundRefreshQueue:
    """Test background refresh queue functionality"""

    @pytest.fixture
    async def background_queue(self, mock_research_service):
        """Create background refresh queue"""
        queue = BackgroundRefreshQueue(max_concurrent=2)
        await queue.start(mock_research_service)
        yield queue
        await queue.stop()

    @pytest.mark.asyncio
    async def test_schedule_refresh(self, background_queue):
        """Test scheduling a refresh task"""
        standard_id = "python/test_standard_v1.0.0.md"
        metadata = StandardMetadata(
            path="/path/to/standard.md",
            last_modified=1700000000.0,
            content_hash="abc123",
            standards_count=1
        )

        task_id = await background_queue.schedule_refresh(standard_id, metadata)

        assert task_id is not None
        assert standard_id in task_id
        assert background_queue.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_worker_processes_task(self, background_queue, mock_research_service):
        """Test that worker processes queued tasks"""
        standard_id = "python/test_standard_v1.0.0.md"
        metadata = StandardMetadata(
            path="/path/to/standard.md",
            last_modified=1700000000.0,
            content_hash="abc123",
            standards_count=1
        )

        await background_queue.schedule_refresh(standard_id, metadata)

        # Wait for worker to process (with timeout)
        await asyncio.wait_for(background_queue.queue.join(), timeout=5.0)

        # Verify update_standard was called
        mock_research_service.update_standard.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_refresh_prevented(self, background_queue):
        """Test that duplicate refreshes are prevented"""
        standard_id = "python/test_standard_v1.0.0.md"
        metadata = StandardMetadata(
            path="/path/to/standard.md",
            last_modified=1700000000.0,
            content_hash="abc123",
            standards_count=1
        )

        # Schedule twice
        task_id1 = await background_queue.schedule_refresh(standard_id, metadata)
        task_id2 = await background_queue.schedule_refresh(standard_id, metadata)

        # First one queued, second one should be same ID
        assert task_id1 == task_id2
        assert background_queue.queue.qsize() == 1

    @pytest.mark.asyncio
    async def test_get_status(self, background_queue):
        """Test getting queue status"""
        status = background_queue.get_status()

        assert "queue_size" in status
        assert "active_workers" in status
        assert "active_refreshes" in status
        assert status["active_workers"] == 2  # max_concurrent

    @pytest.mark.asyncio
    async def test_retry_logic(self, mock_research_service):
        """Test retry logic on failure"""
        # Make first attempt fail, second succeed
        mock_research_service.update_standard.side_effect = [
            Exception("Temporary failure"),
            {"version": "1.1.0"}  # Success on second try
        ]

        queue = BackgroundRefreshQueue(max_concurrent=1)
        await queue.start(mock_research_service)

        try:
            standard_id = "python/test_standard_v1.0.0.md"
            metadata = StandardMetadata(
                path="/path/to/standard.md",
                last_modified=1700000000.0,
                content_hash="abc123",
                standards_count=1
            )

            await queue.schedule_refresh(standard_id, metadata)

            # Wait for processing with retry delay
            await asyncio.wait_for(queue.queue.join(), timeout=10.0)

            # Should have been called twice (initial + 1 retry)
            assert mock_research_service.update_standard.call_count == 2

        finally:
            await queue.stop()


@pytest.mark.integration
class TestStandardsAccessServiceIntegration:
    """Integration tests for full auto-refresh flow"""

    @pytest.mark.asyncio
    async def test_end_to_end_blocking_refresh(
        self,
        temp_standards_dir,
        mock_research_service
    ):
        """Test complete flow with blocking refresh"""
        with patch('services.standards_access_service.settings') as mock_settings:
            mock_settings.STANDARDS_BASE_PATH = str(temp_standards_dir)
            mock_settings.ENABLE_AUTO_REFRESH_ON_ACCESS = True
            mock_settings.STANDARD_FRESHNESS_THRESHOLD_DAYS = 30
            mock_settings.AUTO_REFRESH_MODE = "blocking"
            mock_settings.AUTO_REFRESH_USE_DEEP_RESEARCH = True

            service = StandardsAccessService(research_service=mock_research_service)

            try:
                standard_id = "python/test_standard_v1.0.0.md"

                # Make stale
                metadata = service.metadata_cache[standard_id]
                old_timestamp = (datetime.now() - timedelta(days=35)).timestamp()
                metadata.last_modified = old_timestamp

                # Access should trigger blocking refresh
                result = await service.get_standard(standard_id)

                assert result["was_refreshed"] is True
                assert service.metrics.refresh_successes == 1

            finally:
                await service.stop()

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_end_to_end_background_refresh(
        self,
        temp_standards_dir,
        mock_research_service
    ):
        """Test complete flow with background refresh"""
        with patch('services.standards_access_service.settings') as mock_settings:
            mock_settings.STANDARDS_BASE_PATH = str(temp_standards_dir)
            mock_settings.ENABLE_AUTO_REFRESH_ON_ACCESS = True
            mock_settings.STANDARD_FRESHNESS_THRESHOLD_DAYS = 30
            mock_settings.AUTO_REFRESH_MODE = "background"
            mock_settings.AUTO_REFRESH_MAX_CONCURRENT = 2
            mock_settings.AUTO_REFRESH_RETRY_ATTEMPTS = 1
            mock_settings.AUTO_REFRESH_USE_DEEP_RESEARCH = True

            service = StandardsAccessService(research_service=mock_research_service)
            await service.start()

            try:
                standard_id = "python/test_standard_v1.0.0.md"

                # Make stale
                metadata = service.metadata_cache[standard_id]
                old_timestamp = (datetime.now() - timedelta(days=35)).timestamp()
                metadata.last_modified = old_timestamp

                # Access should schedule background refresh
                result = await service.get_standard(standard_id)

                assert result["was_refreshed"] is True

                # Wait for background processing
                if service.background_queue:
                    await asyncio.wait_for(
                        service.background_queue.queue.join(),
                        timeout=10.0
                    )

                # Verify refresh was called
                mock_research_service.update_standard.assert_called_once()

            finally:
                await service.stop()
