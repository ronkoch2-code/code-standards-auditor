"""
Standards Access Service with Auto-Refresh

This service provides intelligent access to coding standards with automatic
freshness checking and background refresh capabilities.

Features:
- Access tracking (last_accessed, access_count)
- Automatic freshness detection
- Background or blocking refresh modes
- Deep research integration
- Retry logic with exponential backoff
- Comprehensive metrics and logging

Author: Code Standards Auditor
Date: November 16, 2025
Version: 1.0.0 (v4.2.2)
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from services.standards_research_service import StandardsResearchService
from services.standards_sync_service import StandardsSyncService
from config.settings import settings

logger = logging.getLogger(__name__)


@dataclass
class RefreshMetrics:
    """Metrics for auto-refresh operations"""
    total_accesses: int = 0
    stale_standards_detected: int = 0
    refresh_attempts: int = 0
    refresh_successes: int = 0
    refresh_failures: int = 0
    total_refresh_duration_seconds: float = 0.0
    background_queue_size: int = 0

    @property
    def avg_refresh_duration_seconds(self) -> float:
        """Calculate average refresh duration"""
        if self.refresh_successes == 0:
            return 0.0
        return self.total_refresh_duration_seconds / self.refresh_successes

    @property
    def success_rate(self) -> float:
        """Calculate refresh success rate"""
        if self.refresh_attempts == 0:
            return 0.0
        return (self.refresh_successes / self.refresh_attempts) * 100

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        data = asdict(self)
        data['avg_refresh_duration_seconds'] = self.avg_refresh_duration_seconds
        data['success_rate'] = self.success_rate
        return data


@dataclass
class StandardMetadata:
    """Enhanced metadata for standards with access tracking"""
    path: str
    last_modified: float
    content_hash: str
    standards_count: int

    # Auto-refresh fields
    last_accessed: Optional[str] = None
    access_count: int = 0
    auto_update_enabled: bool = True
    freshness_threshold_days: int = 30
    last_auto_update_attempt: Optional[str] = None
    last_auto_update_success: Optional[str] = None
    auto_update_failures: int = 0

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StandardMetadata':
        """Create from dictionary"""
        return cls(**data)


class BackgroundRefreshQueue:
    """Manages background standard refresh tasks"""

    def __init__(self, max_concurrent: int = 3):
        """
        Initialize background refresh queue.

        Args:
            max_concurrent: Maximum concurrent refresh operations
        """
        self.queue: asyncio.Queue = asyncio.Queue()
        self.max_concurrent = max_concurrent
        self.workers: List[asyncio.Task] = []
        self.active_refreshes: Dict[str, asyncio.Task] = {}
        self.research_service: Optional[StandardsResearchService] = None
        self._running = False

    async def start(self, research_service: StandardsResearchService):
        """Start background workers"""
        self.research_service = research_service
        self._running = True

        for i in range(self.max_concurrent):
            worker = asyncio.create_task(self._worker(i))
            self.workers.append(worker)

        logger.info(f"Started {self.max_concurrent} background refresh workers")

    async def stop(self):
        """Stop background workers"""
        self._running = False

        # Wait for queue to empty
        await self.queue.join()

        # Cancel workers
        for worker in self.workers:
            worker.cancel()

        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)

        logger.info("Stopped background refresh workers")

    async def schedule_refresh(self, standard_id: str, metadata: StandardMetadata) -> str:
        """
        Schedule a refresh task.

        Args:
            standard_id: Standard identifier
            metadata: Standard metadata

        Returns:
            Task ID for tracking
        """
        task_id = f"{standard_id}_{datetime.now().isoformat()}"

        # Don't queue if already refreshing this standard
        if standard_id in self.active_refreshes:
            logger.info(f"Standard {standard_id} already queued for refresh")
            return task_id

        await self.queue.put((task_id, standard_id, metadata))
        logger.info(f"Queued refresh task: {task_id} (queue size: {self.queue.qsize()})")

        return task_id

    async def _worker(self, worker_id: int):
        """
        Background worker that processes refresh tasks.

        Args:
            worker_id: Worker identifier
        """
        logger.info(f"Refresh worker {worker_id} started")

        while self._running:
            try:
                # Get task from queue (with timeout)
                task_id, standard_id, metadata = await asyncio.wait_for(
                    self.queue.get(),
                    timeout=1.0
                )

                # Mark as active
                self.active_refreshes[standard_id] = asyncio.current_task()

                logger.info(f"Worker {worker_id} processing: {task_id}")

                try:
                    # Perform refresh with retries
                    await self._refresh_with_retry(standard_id, metadata)
                except Exception as e:
                    logger.error(f"Worker {worker_id} failed to refresh {standard_id}: {e}")
                finally:
                    # Remove from active refreshes
                    self.active_refreshes.pop(standard_id, None)
                    self.queue.task_done()

            except asyncio.TimeoutError:
                # No tasks in queue, continue waiting
                continue
            except asyncio.CancelledError:
                logger.info(f"Worker {worker_id} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_id} error: {e}")

    async def _refresh_with_retry(
        self,
        standard_id: str,
        metadata: StandardMetadata,
        max_attempts: int = None
    ):
        """
        Refresh standard with retry logic.

        Args:
            standard_id: Standard identifier
            metadata: Standard metadata
            max_attempts: Maximum retry attempts (default from settings)
        """
        if max_attempts is None:
            max_attempts = settings.AUTO_REFRESH_RETRY_ATTEMPTS

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Refreshing {standard_id} (attempt {attempt}/{max_attempts})")

                # Call update_standard with deep research
                await self.research_service.update_standard(
                    standard_id=standard_id,
                    use_deep_research=settings.AUTO_REFRESH_USE_DEEP_RESEARCH
                )

                logger.info(f"Successfully refreshed {standard_id}")
                return

            except Exception as e:
                logger.error(f"Attempt {attempt} failed for {standard_id}: {e}")

                if attempt < max_attempts:
                    # Wait before retry (exponential backoff)
                    delay = settings.AUTO_REFRESH_RETRY_DELAY_SECONDS * (2 ** (attempt - 1))
                    logger.info(f"Retrying {standard_id} in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    # All attempts failed
                    logger.error(f"All refresh attempts failed for {standard_id}")
                    raise

    def get_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        return {
            "queue_size": self.queue.qsize(),
            "active_workers": len(self.workers),
            "active_refreshes": len(self.active_refreshes),
            "refreshing_standards": list(self.active_refreshes.keys())
        }


class StandardsAccessService:
    """
    Service for accessing standards with automatic freshness checking and refresh.

    This service wraps access to coding standards and provides:
    - Automatic tracking of access times
    - Freshness detection based on configurable threshold
    - Background or blocking refresh modes
    - Integration with deep research mode
    - Comprehensive metrics and logging
    """

    def __init__(
        self,
        research_service: Optional[StandardsResearchService] = None,
        sync_service: Optional[StandardsSyncService] = None
    ):
        """
        Initialize Standards Access Service.

        Args:
            research_service: Optional research service (will be created if not provided)
            sync_service: Optional sync service (will be created if not provided)
        """
        self.research_service = research_service or StandardsResearchService()
        self.sync_service = sync_service  # May be None - that's okay

        # Metrics tracking
        self.metrics = RefreshMetrics()

        # Background refresh queue
        self.background_queue: Optional[BackgroundRefreshQueue] = None
        if settings.AUTO_REFRESH_MODE == "background":
            self.background_queue = BackgroundRefreshQueue(
                max_concurrent=settings.AUTO_REFRESH_MAX_CONCURRENT
            )

        # Metadata cache
        self.metadata_file = Path(settings.STANDARDS_BASE_PATH) / ".sync_metadata.json"
        self.metadata_cache: Dict[str, StandardMetadata] = {}
        self._load_metadata()

        logger.info(
            f"StandardsAccessService initialized "
            f"(mode: {settings.AUTO_REFRESH_MODE}, "
            f"enabled: {settings.ENABLE_AUTO_REFRESH_ON_ACCESS})"
        )

    async def start(self):
        """Start background services"""
        if self.background_queue:
            await self.background_queue.start(self.research_service)

    async def stop(self):
        """Stop background services"""
        if self.background_queue:
            await self.background_queue.stop()

        # Save metadata
        self._save_metadata()

    def _load_metadata(self):
        """Load metadata from file"""
        try:
            if self.metadata_file.exists():
                with open(self.metadata_file, 'r') as f:
                    data = json.load(f)

                # Convert to StandardMetadata objects
                for key, value in data.items():
                    try:
                        # Add missing fields with defaults
                        if 'last_accessed' not in value:
                            value['last_accessed'] = None
                        if 'access_count' not in value:
                            value['access_count'] = 0
                        if 'auto_update_enabled' not in value:
                            value['auto_update_enabled'] = True
                        if 'freshness_threshold_days' not in value:
                            value['freshness_threshold_days'] = settings.STANDARD_FRESHNESS_THRESHOLD_DAYS
                        if 'last_auto_update_attempt' not in value:
                            value['last_auto_update_attempt'] = None
                        if 'last_auto_update_success' not in value:
                            value['last_auto_update_success'] = None
                        if 'auto_update_failures' not in value:
                            value['auto_update_failures'] = 0

                        self.metadata_cache[key] = StandardMetadata.from_dict(value)
                    except Exception as e:
                        logger.warning(f"Failed to parse metadata for {key}: {e}")

                logger.info(f"Loaded metadata for {len(self.metadata_cache)} standards")
        except Exception as e:
            logger.error(f"Failed to load metadata: {e}")

    def _save_metadata(self):
        """Save metadata to file"""
        try:
            # Convert to dictionaries
            data = {
                key: metadata.to_dict()
                for key, metadata in self.metadata_cache.items()
            }

            # Ensure directory exists
            self.metadata_file.parent.mkdir(parents=True, exist_ok=True)

            # Write atomically
            temp_file = self.metadata_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(data, f, indent=2)

            temp_file.replace(self.metadata_file)
            logger.debug(f"Saved metadata for {len(self.metadata_cache)} standards")

        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    async def get_standard(
        self,
        standard_id: str,
        force_refresh: bool = False,
        skip_auto_refresh: bool = False
    ) -> Dict[str, Any]:
        """
        Get a standard with automatic freshness checking and optional refresh.

        Args:
            standard_id: Standard identifier (e.g., "python/coding_standards_v1.0.0.md")
            force_refresh: Force refresh even if not stale
            skip_auto_refresh: Skip auto-refresh (for admin/testing purposes)

        Returns:
            Standard content with metadata

        Raises:
            ValueError: If standard not found
        """
        # Track access
        self.metrics.total_accesses += 1

        # Get or create metadata
        metadata = self.metadata_cache.get(standard_id)
        if not metadata:
            # Try to load from filesystem
            standard_path = Path(settings.STANDARDS_BASE_PATH) / standard_id
            if not standard_path.exists():
                raise ValueError(f"Standard not found: {standard_id}")

            # Create new metadata
            metadata = StandardMetadata(
                path=str(standard_path),
                last_modified=standard_path.stat().st_mtime,
                content_hash="",  # Will be calculated by sync service
                standards_count=0
            )
            self.metadata_cache[standard_id] = metadata

        # Update access tracking
        await self._update_access_metadata(standard_id, metadata)

        # Check if refresh needed
        should_refresh = force_refresh or (
            not skip_auto_refresh and
            settings.ENABLE_AUTO_REFRESH_ON_ACCESS and
            metadata.auto_update_enabled and
            await self._needs_refresh(metadata)
        )

        if should_refresh:
            self.metrics.stale_standards_detected += 1

            # Refresh based on configured mode
            if settings.AUTO_REFRESH_MODE == "blocking" or force_refresh:
                await self._refresh_blocking(standard_id, metadata)
            else:  # background mode
                await self._refresh_background(standard_id, metadata)

        # Load and return standard
        standard_path = Path(metadata.path)
        with open(standard_path, 'r') as f:
            content = f.read()

        return {
            "standard_id": standard_id,
            "content": content,
            "metadata": metadata.to_dict(),
            "was_refreshed": should_refresh
        }

    async def _needs_refresh(self, metadata: StandardMetadata) -> bool:
        """
        Check if standard needs refresh based on age and settings.

        Args:
            metadata: Standard metadata

        Returns:
            True if refresh is needed
        """
        # Never refreshed or no last_modified timestamp
        if not metadata.last_modified:
            return False

        # Calculate age in days
        last_modified_dt = datetime.fromtimestamp(metadata.last_modified)
        age_days = (datetime.now() - last_modified_dt).days

        # Use per-standard threshold or global default
        threshold_days = metadata.freshness_threshold_days or settings.STANDARD_FRESHNESS_THRESHOLD_DAYS

        needs_refresh = age_days >= threshold_days

        if needs_refresh:
            logger.info(
                f"Standard needs refresh: age={age_days} days, "
                f"threshold={threshold_days} days"
            )

        return needs_refresh

    async def _refresh_blocking(self, standard_id: str, metadata: StandardMetadata):
        """
        Refresh standard in blocking mode (wait for completion).

        Args:
            standard_id: Standard identifier
            metadata: Standard metadata
        """
        logger.info(f"Starting blocking refresh for {standard_id}")

        start_time = datetime.now()
        self.metrics.refresh_attempts += 1
        metadata.last_auto_update_attempt = start_time.isoformat()

        try:
            # Update standard using deep research
            await self.research_service.update_standard(
                standard_id=standard_id,
                use_deep_research=settings.AUTO_REFRESH_USE_DEEP_RESEARCH
            )

            # Track success
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()

            self.metrics.refresh_successes += 1
            self.metrics.total_refresh_duration_seconds += duration
            metadata.last_auto_update_success = end_time.isoformat()
            metadata.auto_update_failures = 0

            logger.info(f"Completed blocking refresh for {standard_id} in {duration:.2f}s")

        except Exception as e:
            self.metrics.refresh_failures += 1
            metadata.auto_update_failures += 1
            logger.error(f"Blocking refresh failed for {standard_id}: {e}")
            raise
        finally:
            self._save_metadata()

    async def _refresh_background(self, standard_id: str, metadata: StandardMetadata):
        """
        Refresh standard in background mode (return immediately).

        Args:
            standard_id: Standard identifier
            metadata: Standard metadata
        """
        if not self.background_queue:
            logger.warning("Background queue not initialized, falling back to blocking mode")
            await self._refresh_blocking(standard_id, metadata)
            return

        logger.info(f"Scheduling background refresh for {standard_id}")

        # Update attempt timestamp
        metadata.last_auto_update_attempt = datetime.now().isoformat()
        self.metrics.refresh_attempts += 1
        self._save_metadata()

        # Schedule refresh
        await self.background_queue.schedule_refresh(standard_id, metadata)
        self.metrics.background_queue_size = self.background_queue.queue.qsize()

    async def _update_access_metadata(self, standard_id: str, metadata: StandardMetadata):
        """
        Update access tracking metadata.

        Args:
            standard_id: Standard identifier
            metadata: Standard metadata
        """
        metadata.last_accessed = datetime.now().isoformat()
        metadata.access_count += 1

        # Save periodically (every 10 accesses to reduce I/O)
        if metadata.access_count % 10 == 0:
            self._save_metadata()

    def get_metrics(self) -> Dict[str, Any]:
        """Get auto-refresh metrics"""
        metrics = self.metrics.to_dict()

        if self.background_queue:
            metrics['background_queue'] = self.background_queue.get_status()

        return metrics

    def get_standard_metadata(self, standard_id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a specific standard"""
        metadata = self.metadata_cache.get(standard_id)
        if metadata:
            return metadata.to_dict()
        return None

    def update_standard_settings(
        self,
        standard_id: str,
        auto_update_enabled: Optional[bool] = None,
        freshness_threshold_days: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Update auto-refresh settings for a specific standard.

        Args:
            standard_id: Standard identifier
            auto_update_enabled: Enable/disable auto-update
            freshness_threshold_days: Custom freshness threshold

        Returns:
            Updated metadata
        """
        metadata = self.metadata_cache.get(standard_id)
        if not metadata:
            raise ValueError(f"Standard not found: {standard_id}")

        if auto_update_enabled is not None:
            metadata.auto_update_enabled = auto_update_enabled

        if freshness_threshold_days is not None:
            metadata.freshness_threshold_days = freshness_threshold_days

        self._save_metadata()

        logger.info(f"Updated settings for {standard_id}")
        return metadata.to_dict()
