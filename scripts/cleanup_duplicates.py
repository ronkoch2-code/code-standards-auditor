#!/usr/bin/env python3
"""
Cleanup Duplicate Standards in Neo4j
Identifies and removes duplicate standards based on (language, category, name)
"""

import asyncio
import sys
import os

# Add parent directory to path for imports
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Load .env file explicitly before importing settings
from dotenv import load_dotenv
load_dotenv(os.path.join(project_root, '.env'))

from neo4j import AsyncGraphDatabase
from config.settings import settings


async def find_duplicates(driver):
    """Find all duplicate standards by language, category, and name"""
    query = """
    MATCH (s:Standard)
    WITH s.language AS language, s.category AS category, s.name AS name,
         COLLECT(s) AS standards, COUNT(s) AS count
    WHERE count > 1
    RETURN language, category, name, count,
           [std IN standards | {id: std.id, created_at: std.created_at, file_source: std.file_source}] AS duplicates
    ORDER BY count DESC, language, category, name
    """
    async with driver.session() as session:
        result = await session.run(query)
        records = await result.data()
        return records


async def find_exact_description_duplicates(driver):
    """Find duplicates with identical descriptions"""
    query = """
    MATCH (s:Standard)
    WITH s.description AS desc, COLLECT(s) AS standards, COUNT(s) AS count
    WHERE count > 1
    RETURN LEFT(desc, 100) AS description_preview, count,
           [std IN standards | {id: std.id, name: std.name, language: std.language, category: std.category}] AS duplicates
    ORDER BY count DESC
    LIMIT 50
    """
    async with driver.session() as session:
        result = await session.run(query)
        records = await result.data()
        return records


async def get_total_standards_count(driver):
    """Get total count of standards"""
    query = "MATCH (s:Standard) RETURN COUNT(s) AS count"
    async with driver.session() as session:
        result = await session.run(query)
        record = await result.single()
        return record["count"] if record else 0


async def delete_duplicate_standards(driver, keep_strategy="newest"):
    """
    Delete duplicate standards, keeping one based on strategy.

    keep_strategy: "newest" keeps the most recently created, "oldest" keeps the first created
    """
    # Find duplicates and delete all but one (keeping based on strategy)
    if keep_strategy == "newest":
        query = """
        MATCH (s:Standard)
        WITH s.language AS language, s.category AS category, s.name AS name,
             COLLECT(s) AS standards, COUNT(s) AS count
        WHERE count > 1
        WITH language, category, name, standards, count,
             HEAD(apoc.coll.sortNodes(standards, 'created_at')[count-1..]) AS keeper,
             TAIL(apoc.coll.sortNodes(standards, 'created_at')[..count-1]) AS toDelete
        UNWIND toDelete AS dup
        DETACH DELETE dup
        RETURN count(*) AS deleted_count
        """
    else:
        query = """
        MATCH (s:Standard)
        WITH s.language AS language, s.category AS category, s.name AS name,
             COLLECT(s) AS standards, COUNT(s) AS count
        WHERE count > 1
        WITH language, category, name, standards[1..] AS toDelete
        UNWIND toDelete AS dup
        DETACH DELETE dup
        RETURN count(*) AS deleted_count
        """

    async with driver.session() as session:
        result = await session.run(query)
        record = await result.single()
        return record["deleted_count"] if record else 0


async def delete_duplicates_simple(driver):
    """
    Simple duplicate deletion without APOC - keeps first occurrence.
    Deletes duplicates based on (language, category, name).
    """
    # First get all duplicate groups
    find_query = """
    MATCH (s:Standard)
    WITH s.language AS language, s.category AS category, s.name AS name,
         COLLECT(s.id) AS ids, COUNT(s) AS count
    WHERE count > 1
    RETURN language, category, name, ids, count
    """

    deleted_total = 0

    async with driver.session() as session:
        result = await session.run(find_query)
        duplicates = await result.data()

        for dup in duplicates:
            # Keep the first ID, delete the rest
            ids_to_delete = dup['ids'][1:]  # Skip first one

            delete_query = """
            MATCH (s:Standard)
            WHERE s.id IN $ids
            DETACH DELETE s
            RETURN count(*) AS deleted
            """

            del_result = await session.run(delete_query, ids=ids_to_delete)
            del_record = await del_result.single()
            deleted_total += del_record["deleted"] if del_record else 0

    return deleted_total


async def main():
    print("=" * 60)
    print("Neo4j Duplicate Standards Cleanup")
    print("=" * 60)

    # Connect to Neo4j - use bolt:// for direct connection
    uri = settings.NEO4J_URI.replace("neo4j://", "bolt://")
    user = settings.NEO4J_USER
    password = settings.NEO4J_PASSWORD

    print(f"\nConnecting to Neo4j at {uri}...")
    print(f"User: {user}, Password: {'*' * len(password) if password else 'NOT SET'}")

    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))

    try:
        # Verify connection - use default database first
        async with driver.session(database="neo4j") as session:
            await session.run("RETURN 1")
        print("✓ Connected successfully")

        # Get total count
        total = await get_total_standards_count(driver)
        print(f"\nTotal standards in database: {total}")

        # Find duplicates by name/language/category
        print("\n" + "-" * 60)
        print("Finding duplicates by (language, category, name)...")
        print("-" * 60)

        duplicates = await find_duplicates(driver)

        if not duplicates:
            print("✓ No duplicates found!")
        else:
            print(f"\nFound {len(duplicates)} duplicate groups:\n")

            total_extra = 0
            for dup in duplicates:
                extra = dup['count'] - 1
                total_extra += extra
                print(f"  [{dup['language']}] {dup['category']}/{dup['name']}")
                print(f"    → {dup['count']} copies ({extra} extra)")
                for d in dup['duplicates'][:3]:  # Show first 3
                    print(f"      - ID: {d['id'][:8]}... | Source: {d.get('file_source', 'N/A')}")
                if len(dup['duplicates']) > 3:
                    print(f"      ... and {len(dup['duplicates']) - 3} more")
                print()

            print(f"\nSummary: {total_extra} duplicate standards to remove")

            # Ask for confirmation
            if len(sys.argv) > 1 and sys.argv[1] == "--delete":
                print("\n" + "=" * 60)
                print("DELETING DUPLICATES...")
                print("=" * 60)

                deleted = await delete_duplicates_simple(driver)
                print(f"\n✓ Deleted {deleted} duplicate standards")

                # Verify
                new_total = await get_total_standards_count(driver)
                print(f"Standards remaining: {new_total}")
            else:
                print("\nTo delete duplicates, run with --delete flag:")
                print("  python3 scripts/cleanup_duplicates.py --delete")

        # Also check for description duplicates
        print("\n" + "-" * 60)
        print("Checking for identical description duplicates...")
        print("-" * 60)

        desc_dups = await find_exact_description_duplicates(driver)
        if desc_dups:
            print(f"\nFound {len(desc_dups)} groups with identical descriptions:\n")
            for dd in desc_dups[:10]:  # Show first 10
                print(f"  Description: \"{dd['description_preview']}...\"")
                print(f"    → {dd['count']} copies")
                for d in dd['duplicates'][:2]:
                    print(f"      - {d['language']}/{d['category']}: {d['name']}")
                print()
        else:
            print("✓ No identical description duplicates found")

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await driver.close()
        print("\nConnection closed.")


if __name__ == "__main__":
    asyncio.run(main())
