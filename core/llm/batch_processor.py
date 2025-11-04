"""
LLM Batch Processor

Provides efficient batch processing of multiple LLM requests with
rate limiting, concurrency control, and error handling.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
import asyncio
import logging
from datetime import datetime
from enum import Enum

from .provider import LLMRequest, LLMResponse, LLMProviderManager, ProviderType
from .cache_decorator import LLMCache, get_llm_cache

logger = logging.getLogger(__name__)


class BatchStatus(str, Enum):
    """Status of a batch job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class BatchItem:
    """A single item in a batch."""
    id: str
    request: LLMRequest
    status: BatchStatus = BatchStatus.PENDING
    response: Optional[LLMResponse] = None
    error: Optional[str] = None
    retries: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "response": self.response.to_dict() if self.response else None,
            "error": self.error,
            "retries": self.retries,
            "metadata": self.metadata
        }


@dataclass
class BatchJob:
    """A batch processing job."""
    id: str
    items: List[BatchItem]
    status: BatchStatus = BatchStatus.PENDING
    progress: float = 0.0
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    config: Dict[str, Any] = field(default_factory=dict)

    def get_completed_count(self) -> int:
        """Get number of completed items."""
        return sum(1 for item in self.items if item.status == BatchStatus.COMPLETED)

    def get_failed_count(self) -> int:
        """Get number of failed items."""
        return sum(1 for item in self.items if item.status == BatchStatus.FAILED)

    def calculate_progress(self) -> float:
        """Calculate completion progress (0.0 to 1.0)."""
        if not self.items:
            return 1.0

        completed = sum(
            1 for item in self.items
            if item.status in [BatchStatus.COMPLETED, BatchStatus.FAILED]
        )
        return completed / len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "status": self.status.value,
            "total_items": len(self.items),
            "completed_items": self.get_completed_count(),
            "failed_items": self.get_failed_count(),
            "progress": self.calculate_progress(),
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "config": self.config
        }


class BatchProcessor:
    """
    Processes multiple LLM requests efficiently in batches.

    Features:
    - Concurrent processing with rate limiting
    - Automatic retry on failures
    - Progress tracking
    - Result caching
    - Error handling
    """

    def __init__(
        self,
        provider_manager: LLMProviderManager,
        max_concurrent: int = 5,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        rate_limit_per_minute: Optional[int] = None,
        cache: Optional[LLMCache] = None
    ):
        self.provider_manager = provider_manager
        self.max_concurrent = max_concurrent
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.rate_limit_per_minute = rate_limit_per_minute
        self.cache = cache or get_llm_cache()

        self.jobs: Dict[str, BatchJob] = {}
        self.progress_callbacks: List[Callable] = []

        # Rate limiting
        self._request_times: List[datetime] = []
        self._rate_limit_lock = asyncio.Lock()

    def register_progress_callback(self, callback: Callable) -> None:
        """Register a callback for progress updates."""
        self.progress_callbacks.append(callback)

    async def _notify_progress(self, job_id: str, progress: Dict[str, Any]) -> None:
        """Notify all progress callbacks."""
        for callback in self.progress_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(job_id, progress)
                else:
                    callback(job_id, progress)
            except Exception as e:
                logger.error(f"Error in progress callback: {e}")

    async def _check_rate_limit(self) -> None:
        """Check and enforce rate limiting."""
        if not self.rate_limit_per_minute:
            return

        async with self._rate_limit_lock:
            now = datetime.now()

            # Remove timestamps older than 1 minute
            self._request_times = [
                t for t in self._request_times
                if (now - t).total_seconds() < 60
            ]

            # Check if we've hit the limit
            if len(self._request_times) >= self.rate_limit_per_minute:
                # Calculate how long to wait
                oldest = min(self._request_times)
                wait_time = 60 - (now - oldest).total_seconds()

                if wait_time > 0:
                    logger.debug(f"Rate limit reached, waiting {wait_time:.1f}s")
                    await asyncio.sleep(wait_time)

            # Record this request
            self._request_times.append(now)

    async def _process_item(
        self,
        item: BatchItem,
        job: BatchJob
    ) -> None:
        """Process a single batch item."""
        for attempt in range(self.max_retries + 1):
            try:
                # Check rate limit
                await self._check_rate_limit()

                # Try to get from cache
                cache_key = self.cache._generate_cache_key(
                    prompt=item.request.prompt,
                    model=item.request.model_tier.value,
                    temperature=item.request.temperature
                )

                cached_response = await self.cache.get(cache_key)
                if cached_response:
                    item.response = LLMResponse(**cached_response)
                    item.status = BatchStatus.COMPLETED
                    logger.debug(f"Item {item.id} completed from cache")
                    return

                # Generate response
                response = await self.provider_manager.generate(item.request)

                # Cache the response
                await self.cache.set(cache_key, response.to_dict())

                item.response = response
                item.status = BatchStatus.COMPLETED
                logger.debug(f"Item {item.id} completed successfully")
                return

            except Exception as e:
                item.retries = attempt + 1
                error_msg = f"Attempt {attempt + 1} failed: {str(e)}"
                logger.warning(f"Item {item.id}: {error_msg}")

                if attempt < self.max_retries:
                    # Wait before retry
                    await asyncio.sleep(self.retry_delay * (attempt + 1))
                else:
                    # Final failure
                    item.status = BatchStatus.FAILED
                    item.error = error_msg
                    logger.error(f"Item {item.id} failed after {self.max_retries} retries")

    async def process_batch(
        self,
        job_id: str,
        requests: List[LLMRequest],
        config: Optional[Dict[str, Any]] = None
    ) -> BatchJob:
        """
        Process a batch of LLM requests.

        Args:
            job_id: Unique identifier for this batch job
            requests: List of LLM requests to process
            config: Optional configuration for this batch

        Returns:
            Completed batch job with results
        """
        # Create batch job
        items = [
            BatchItem(id=f"{job_id}_{i}", request=req)
            for i, req in enumerate(requests)
        ]

        job = BatchJob(
            id=job_id,
            items=items,
            config=config or {},
            started_at=datetime.now().isoformat()
        )

        self.jobs[job_id] = job
        job.status = BatchStatus.PROCESSING

        logger.info(f"Starting batch job {job_id} with {len(items)} items")

        # Notify start
        await self._notify_progress(job_id, {
            "phase": "started",
            "total_items": len(items)
        })

        try:
            # Process items concurrently with semaphore
            semaphore = asyncio.Semaphore(self.max_concurrent)

            async def process_with_semaphore(item: BatchItem):
                async with semaphore:
                    await self._process_item(item, job)

                    # Update progress
                    job.progress = job.calculate_progress()

                    # Notify progress
                    await self._notify_progress(job_id, {
                        "phase": "processing",
                        "progress": job.progress,
                        "completed": job.get_completed_count(),
                        "failed": job.get_failed_count()
                    })

            # Process all items
            await asyncio.gather(
                *[process_with_semaphore(item) for item in items],
                return_exceptions=True
            )

            # Mark as completed
            job.status = BatchStatus.COMPLETED
            job.completed_at = datetime.now().isoformat()
            job.progress = 1.0

            logger.info(
                f"Batch job {job_id} completed: "
                f"{job.get_completed_count()} succeeded, "
                f"{job.get_failed_count()} failed"
            )

            # Notify completion
            await self._notify_progress(job_id, {
                "phase": "completed",
                "progress": 1.0,
                "completed": job.get_completed_count(),
                "failed": job.get_failed_count()
            })

        except Exception as e:
            job.status = BatchStatus.FAILED
            job.completed_at = datetime.now().isoformat()
            logger.error(f"Batch job {job_id} failed: {e}")

            await self._notify_progress(job_id, {
                "phase": "failed",
                "error": str(e)
            })

        return job

    def get_job(self, job_id: str) -> Optional[BatchJob]:
        """Get a batch job by ID."""
        return self.jobs.get(job_id)

    def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get the status of a batch job."""
        job = self.jobs.get(job_id)
        if not job:
            return None

        return job.to_dict()

    def get_job_results(self, job_id: str) -> Optional[List[Dict[str, Any]]]:
        """Get the results of a completed batch job."""
        job = self.jobs.get(job_id)
        if not job:
            return None

        return [item.to_dict() for item in job.items]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running batch job."""
        job = self.jobs.get(job_id)
        if not job:
            return False

        if job.status == BatchStatus.PROCESSING:
            job.status = BatchStatus.CANCELLED
            job.completed_at = datetime.now().isoformat()
            logger.info(f"Cancelled batch job {job_id}")
            return True

        return False

    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all batch jobs."""
        return [job.to_dict() for job in self.jobs.values()]

    def cleanup_completed_jobs(self, keep_recent: int = 10) -> int:
        """Clean up old completed jobs."""
        completed = [
            (job_id, job) for job_id, job in self.jobs.items()
            if job.status in [BatchStatus.COMPLETED, BatchStatus.FAILED, BatchStatus.CANCELLED]
        ]

        # Sort by completion time
        completed.sort(key=lambda x: x[1].completed_at or "", reverse=True)

        # Remove old jobs
        removed_count = 0
        for job_id, _ in completed[keep_recent:]:
            del self.jobs[job_id]
            removed_count += 1

        return removed_count

    def get_statistics(self) -> Dict[str, Any]:
        """Get batch processing statistics."""
        total_jobs = len(self.jobs)
        completed_jobs = sum(1 for job in self.jobs.values() if job.status == BatchStatus.COMPLETED)
        failed_jobs = sum(1 for job in self.jobs.values() if job.status == BatchStatus.FAILED)
        processing_jobs = sum(1 for job in self.jobs.values() if job.status == BatchStatus.PROCESSING)

        total_items = sum(len(job.items) for job in self.jobs.values())
        completed_items = sum(job.get_completed_count() for job in self.jobs.values())
        failed_items = sum(job.get_failed_count() for job in self.jobs.values())

        return {
            "total_jobs": total_jobs,
            "completed_jobs": completed_jobs,
            "failed_jobs": failed_jobs,
            "processing_jobs": processing_jobs,
            "total_items": total_items,
            "completed_items": completed_items,
            "failed_items": failed_items,
            "success_rate": completed_items / total_items if total_items > 0 else 0.0
        }


# Singleton instance
_batch_processor_instance: Optional[BatchProcessor] = None


def get_batch_processor(
    provider_manager: Optional[LLMProviderManager] = None,
    **kwargs
) -> BatchProcessor:
    """Get or create the global batch processor instance."""
    global _batch_processor_instance

    if _batch_processor_instance is None:
        if not provider_manager:
            from .provider import get_llm_provider_manager
            provider_manager = get_llm_provider_manager()

        _batch_processor_instance = BatchProcessor(
            provider_manager=provider_manager,
            **kwargs
        )

    return _batch_processor_instance
