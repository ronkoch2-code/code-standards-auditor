"""
Test Auto-Refresh Feature by Updating the 3 Oldest Standards

This script tests the auto-refresh feature by updating:
1. python/coding_standards_v1.0.0.md (78 days old)
2. java/coding_standards_v1.0.0.md (78 days old)
3. general/coding_standards_v1.0.0.md (78 days old)

Author: Code Standards Auditor
Date: November 16, 2025
Version: 1.0.0 (v4.2.2)
"""

import asyncio
import logging
from datetime import datetime
from services.standards_access_service import StandardsAccessService
from services.standards_research_service import StandardsResearchService
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def update_standard(service: StandardsAccessService, standard_id: str):
    """
    Update a single standard using auto-refresh feature.

    Args:
        service: StandardsAccessService instance
        standard_id: Standard identifier
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Updating: {standard_id}")
    logger.info(f"{'='*80}")

    try:
        # Check current metadata before update
        metadata_before = service.get_standard_metadata(standard_id)
        if metadata_before:
            logger.info(f"Current metadata:")
            logger.info(f"  - Last modified: {datetime.fromtimestamp(metadata_before['last_modified'])}")
            logger.info(f"  - Access count: {metadata_before.get('access_count', 0)}")

        # Force refresh to test the feature
        logger.info(f"\nTriggering force refresh (using deep research mode)...")
        start_time = datetime.now()

        result = await service.get_standard(
            standard_id,
            force_refresh=True  # Force refresh regardless of age
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"\n✅ Update completed in {duration:.2f} seconds")
        logger.info(f"Was refreshed: {result['was_refreshed']}")

        # Check metadata after update
        metadata_after = result['metadata']
        logger.info(f"\nUpdated metadata:")
        logger.info(f"  - Last accessed: {metadata_after.get('last_accessed')}")
        logger.info(f"  - Access count: {metadata_after.get('access_count', 0)}")
        logger.info(f"  - Last auto update attempt: {metadata_after.get('last_auto_update_attempt')}")
        logger.info(f"  - Last auto update success: {metadata_after.get('last_auto_update_success')}")

        return True

    except Exception as e:
        logger.error(f"❌ Failed to update {standard_id}: {e}")
        logger.exception(e)
        return False


async def main():
    """Main function to update the 3 oldest standards"""

    logger.info("\n" + "="*80)
    logger.info("AUTO-REFRESH FEATURE TEST - Updating 3 Oldest Standards")
    logger.info("="*80)
    logger.info(f"Mode: {settings.AUTO_REFRESH_MODE}")
    logger.info(f"Use Deep Research: {settings.AUTO_REFRESH_USE_DEEP_RESEARCH}")
    logger.info(f"Max Iterations: {settings.DEEP_RESEARCH_MAX_ITERATIONS}")
    logger.info(f"Quality Threshold: {settings.DEEP_RESEARCH_QUALITY_THRESHOLD}")
    logger.info("="*80 + "\n")

    # Standards to update (oldest first)
    standards_to_update = [
        "python/coding_standards_v1.0.0.md",
        "java/coding_standards_v1.0.0.md",
        "general/coding_standards_v1.0.0.md"
    ]

    # Create service (with blocking mode for this test)
    research_service = StandardsResearchService()
    service = StandardsAccessService(research_service=research_service)

    try:
        # Update each standard
        results = []
        for standard_id in standards_to_update:
            success = await update_standard(service, standard_id)
            results.append((standard_id, success))

            # Small delay between updates
            if standard_id != standards_to_update[-1]:
                logger.info("\nWaiting 5 seconds before next update...")
                await asyncio.sleep(5)

        # Summary
        logger.info("\n" + "="*80)
        logger.info("UPDATE SUMMARY")
        logger.info("="*80)

        successful = sum(1 for _, success in results if success)
        failed = len(results) - successful

        logger.info(f"\nTotal standards: {len(results)}")
        logger.info(f"Successful: {successful}")
        logger.info(f"Failed: {failed}")

        logger.info("\nDetails:")
        for standard_id, success in results:
            status = "✅ SUCCESS" if success else "❌ FAILED"
            logger.info(f"  {status} - {standard_id}")

        # Get metrics
        metrics = service.get_metrics()
        logger.info(f"\nAuto-Refresh Metrics:")
        logger.info(f"  - Total accesses: {metrics['total_accesses']}")
        logger.info(f"  - Stale standards detected: {metrics['stale_standards_detected']}")
        logger.info(f"  - Refresh attempts: {metrics['refresh_attempts']}")
        logger.info(f"  - Refresh successes: {metrics['refresh_successes']}")
        logger.info(f"  - Refresh failures: {metrics['refresh_failures']}")
        logger.info(f"  - Success rate: {metrics['success_rate']:.2f}%")
        logger.info(f"  - Avg duration: {metrics['avg_refresh_duration_seconds']:.2f}s")

        logger.info("\n" + "="*80)

        # Save metadata
        await service.stop()

        return successful == len(results)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        logger.exception(e)
        await service.stop()
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
