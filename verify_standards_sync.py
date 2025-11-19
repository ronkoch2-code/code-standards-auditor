#!/usr/bin/env python3
"""
Verify Standards Synchronization between Filesystem and Neo4j

Compares all markdown standards files with Neo4j database to ensure they're in sync.
"""

import asyncio
import sys
import os
from pathlib import Path
from typing import Set, List, Dict, Any
from datetime import datetime
from dotenv import load_dotenv

# Add parent directory to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load .env file before importing Settings
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file, override=True)
    print(f"✓ Loaded environment from {env_file}")

from services.neo4j_service import Neo4jService
from config.settings import Settings


class StandardsVerifier:
    """Verify standards sync between filesystem and Neo4j"""

    def __init__(self, standards_base_dir: Path):
        self.standards_dir = standards_base_dir
        self.settings = Settings()
        self.neo4j_service = None

    async def initialize(self):
        """Initialize Neo4j connection"""
        print(f"\n🔧 Neo4j Configuration:")
        print(f"   URI: {self.settings.NEO4J_URI}")
        print(f"   User: {self.settings.NEO4J_USER}")
        print(f"   Database: {self.settings.NEO4J_DATABASE}")
        pwd = self.settings.NEO4J_PASSWORD
        if pwd:
            print(f"   Password: {pwd[:4]}...{pwd[-2:]} (length: {len(pwd)})")

        self.neo4j_service = Neo4jService(
            uri=self.settings.NEO4J_URI,
            user=self.settings.NEO4J_USER,
            password=self.settings.NEO4J_PASSWORD,
            database=self.settings.NEO4J_DATABASE
        )
        await self.neo4j_service.connect()

    async def get_filesystem_standards(self) -> Dict[str, List[Path]]:
        """Get all standards files from filesystem organized by language"""
        standards = {}

        if not self.standards_dir.exists():
            print(f"❌ Standards directory not found: {self.standards_dir}")
            return standards

        # Find all language directories
        for lang_dir in self.standards_dir.iterdir():
            if lang_dir.is_dir() and not lang_dir.name.startswith('.'):
                language = lang_dir.name
                files = []

                # Recursively find all .md files
                for md_file in lang_dir.rglob("*.md"):
                    if not md_file.name.startswith('.'):
                        files.append(md_file)

                if files:
                    standards[language] = files

        return standards

    async def get_neo4j_standards(self) -> Dict[str, List[Dict[str, Any]]]:
        """Get all standards from Neo4j organized by language"""
        standards = {}

        try:
            # Query all unique languages
            languages_query = """
            MATCH (s:Standard)
            RETURN DISTINCT s.language as language
            ORDER BY language
            """

            async with self.neo4j_service.driver.session(database=self.neo4j_service.database) as session:
                result = await session.run(languages_query)
                languages = [record["language"] async for record in result]

                # For each language, get all standards
                for language in languages:
                    standards_query = """
                    MATCH (s:Standard {language: $language})
                    RETURN s.id as id, s.name as name, s.file_source as file_source, s.category as category
                    ORDER BY s.file_source, s.name
                    """

                    result = await session.run(standards_query, language=language)
                    lang_standards = []
                    async for record in result:
                        lang_standards.append({
                            'id': record['id'],
                            'name': record['name'],
                            'file_source': record.get('file_source', 'unknown'),
                            'category': record.get('category', 'general')
                        })

                    if lang_standards:
                        standards[language] = lang_standards

        except Exception as e:
            print(f"❌ Error querying Neo4j: {e}")
            return {}

        return standards

    async def verify_sync(self):
        """Verify that all filesystem standards exist in Neo4j"""
        print("\n" + "="*80)
        print("📊 STANDARDS SYNCHRONIZATION VERIFICATION")
        print("="*80)
        print(f"\n🕐 Timestamp: {datetime.now().isoformat()}")
        print(f"📁 Standards Directory: {self.standards_dir}")
        print(f"🔗 Neo4j URI: {self.settings.NEO4J_URI}")

        # Get filesystem standards
        print("\n\n📂 SCANNING FILESYSTEM...")
        print("-" * 80)
        fs_standards = await self.get_filesystem_standards()

        total_fs_files = 0
        for language, files in sorted(fs_standards.items()):
            print(f"  {language:20s}: {len(files):3d} files")
            total_fs_files += len(files)

        print(f"\n  {'TOTAL':20s}: {total_fs_files:3d} files")

        # Get Neo4j standards
        print("\n\n💾 QUERYING NEO4J...")
        print("-" * 80)
        neo4j_standards = await self.get_neo4j_standards()

        total_neo4j_standards = 0
        for language, standards in sorted(neo4j_standards.items()):
            print(f"  {language:20s}: {len(standards):3d} standards")
            total_neo4j_standards += len(standards)

        print(f"\n  {'TOTAL':20s}: {total_neo4j_standards:3d} standards")

        # Compare languages
        print("\n\n🔍 COMPARISON BY LANGUAGE")
        print("="*80)

        fs_languages = set(fs_standards.keys())
        neo4j_languages = set(neo4j_standards.keys())

        all_languages = fs_languages | neo4j_languages

        issues_found = False

        for language in sorted(all_languages):
            print(f"\n📚 Language: {language}")
            print("-" * 80)

            if language not in fs_standards:
                print(f"  ⚠️  WARNING: Language exists in Neo4j but not on filesystem")
                print(f"      Neo4j has {len(neo4j_standards[language])} standards for {language}")
                issues_found = True
                continue

            if language not in neo4j_standards:
                print(f"  ❌ ERROR: Language exists on filesystem but not in Neo4j")
                print(f"      Filesystem has {len(fs_standards[language])} files for {language}")
                issues_found = True
                continue

            # Both exist - compare file sources
            fs_files = {f.name for f in fs_standards[language]}
            neo4j_files = {s['file_source'] for s in neo4j_standards[language] if s['file_source'] and s['file_source'] != 'unknown'}

            print(f"  Filesystem files: {len(fs_files)}")
            print(f"  Neo4j sources:    {len(neo4j_files)}")

            # Files in filesystem but not in Neo4j
            missing_in_neo4j = fs_files - neo4j_files
            if missing_in_neo4j:
                print(f"\n  ❌ Files on filesystem NOT in Neo4j ({len(missing_in_neo4j)}):")
                for file in sorted(missing_in_neo4j):
                    print(f"      - {file}")
                issues_found = True

            # Files in Neo4j but not on filesystem
            missing_in_fs = neo4j_files - fs_files
            if missing_in_fs:
                print(f"\n  ⚠️  Files in Neo4j NOT on filesystem ({len(missing_in_fs)}):")
                for file in sorted([f for f in missing_in_fs if f is not None]):
                    print(f"      - {file}")
                issues_found = True

            # All synced
            if not missing_in_neo4j and not missing_in_fs:
                print(f"  ✅ All files synced")

        # Summary
        print("\n\n" + "="*80)
        print("📋 SUMMARY")
        print("="*80)
        print(f"  Filesystem:  {len(fs_languages)} languages, {total_fs_files} files")
        print(f"  Neo4j:       {len(neo4j_languages)} languages, {total_neo4j_standards} standards")

        if not issues_found:
            print("\n  ✅ SUCCESS: All filesystem standards are in sync with Neo4j!")
        else:
            print("\n  ❌ ISSUES FOUND: Some standards are out of sync")
            print("\n  💡 Recommendation: Run the sync script to fix:")
            print("     python3 scripts/sync_standards.py")

        print("="*80 + "\n")

        return not issues_found

    async def cleanup(self):
        """Cleanup resources"""
        if self.neo4j_service:
            await self.neo4j_service.disconnect()


async def main():
    """Main verification function"""
    # Determine standards directory
    standards_dir = Path("/Volumes/FS001/pythonscripts/standards")

    if not standards_dir.exists():
        # Try relative path
        standards_dir = Path(__file__).parent / "standards"

    verifier = StandardsVerifier(standards_dir)
    success = False

    try:
        await verifier.initialize()
        success = await verifier.verify_sync()
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await verifier.cleanup()
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
