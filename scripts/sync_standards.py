#!/usr/bin/env python3
"""
Standards Synchronization Script

Manually synchronize markdown standards files with Neo4j database.
Can be run as a standalone script or scheduled with cron.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from services.neo4j_service import Neo4jService
from services.standards_sync_service import StandardsSyncService
from config.settings import Settings


async def main():
    """Main synchronization function"""
    import argparse

    parser = argparse.ArgumentParser(description='Synchronize standards files with Neo4j')
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force reimport of all files regardless of changes'
    )
    parser.add_argument(
        '--standards-dir',
        type=Path,
        help='Standards directory path (default: from settings)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )

    args = parser.parse_args()

    print("\n" + "="*60)
    print("  STANDARDS SYNCHRONIZATION")
    print("="*60)

    # Load settings
    settings = Settings()

    # Determine standards directory
    standards_dir = args.standards_dir or Path(settings.STANDARDS_BASE_PATH)

    if not standards_dir.exists():
        print(f"\n❌ Error: Standards directory not found: {standards_dir}")
        sys.exit(1)

    print(f"\n📁 Standards directory: {standards_dir}")
    print(f"🔄 Force sync: {args.force}")

    # Connect to Neo4j
    print("\n🔌 Connecting to Neo4j...")
    neo4j = Neo4jService(
        uri=settings.NEO4J_URI,
        user=settings.NEO4J_USER,
        password=settings.NEO4J_PASSWORD,
        database=settings.NEO4J_DATABASE
    )

    try:
        await neo4j.connect()
        print("✅ Connected to Neo4j")

        # Create sync service
        sync_service = StandardsSyncService(
            neo4j_service=neo4j,
            standards_dir=standards_dir
        )

        # Get status before sync
        print("\n📊 Current status:")
        status_before = await sync_service.get_sync_status()
        print(f"  Files tracked: {status_before['files_tracked']}")
        print(f"  Standards in database: {status_before['standards_in_database']}")

        if status_before.get('last_sync'):
            print(f"  Last sync: {status_before['last_sync']}")

        # Run synchronization
        print("\n🔄 Synchronizing...")
        stats = await sync_service.sync_all(force=args.force)

        # Display results
        print("\n" + "="*60)
        print("  SYNC RESULTS")
        print("="*60)

        changes_detected = any(
            v > 0
            for k, v in stats.items()
            if k.startswith(('files_', 'standards_'))
        )

        if changes_detected:
            print("\n📝 Changes detected:")

            if stats['files_added'] > 0:
                print(f"  ➕ Files added: {stats['files_added']}")
            if stats['files_updated'] > 0:
                print(f"  ✏️  Files updated: {stats['files_updated']}")
            if stats['files_deleted'] > 0:
                print(f"  🗑️  Files deleted: {stats['files_deleted']}")

            if stats['standards_added'] > 0:
                print(f"  ✅ Standards added: {stats['standards_added']}")
            if stats['standards_updated'] > 0:
                print(f"  🔄 Standards updated: {stats['standards_updated']}")
            if stats['standards_deleted'] > 0:
                print(f"  ❌ Standards deleted: {stats['standards_deleted']}")

            print(f"\n⏱️  Duration: {stats.get('duration_seconds', 0):.2f}s")
        else:
            print("\n✅ No changes detected - database is up to date")

        # Get status after sync
        print("\n📊 Updated status:")
        status_after = await sync_service.get_sync_status()
        print(f"  Files tracked: {status_after['files_tracked']}")
        print(f"  Standards in database: {status_after['standards_in_database']}")
        print(f"  Synchronized: {status_after['is_synchronized']}")

        print("\n" + "="*60)
        print("✅ Synchronization complete!")
        print("="*60 + "\n")

    except Exception as e:
        print(f"\n❌ Synchronization failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

    finally:
        await neo4j.disconnect()
        print("👋 Disconnected from Neo4j\n")


if __name__ == '__main__':
    asyncio.run(main())
