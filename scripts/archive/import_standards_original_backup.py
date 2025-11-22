#!/usr/bin/env python3
"""
Import Standards from Markdown Files to Neo4j

Parses markdown standards files and imports them into Neo4j database.
"""

import asyncio
import re
import uuid
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import sys
from dotenv import load_dotenv

# Add parent directory to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Load .env file before importing Settings
env_file = project_root / '.env'
if env_file.exists():
    load_dotenv(env_file, override=True)

from services.neo4j_service import Neo4jService, Standard
from config.settings import Settings


class StandardsParser:
    """Parse markdown standards files"""

    def __init__(self):
        self.severity_keywords = {
            'critical': ['security', 'vulnerability', 'injection', 'authentication', 'authorization'],
            'high': ['error', 'exception', 'failure', 'crash', 'data loss'],
            'medium': ['performance', 'optimization', 'best practice', 'convention'],
            'low': ['style', 'formatting', 'naming', 'documentation']
        }

    def parse_file(self, file_path: Path, language: str) -> List[Dict[str, Any]]:
        """Parse a markdown file and extract standards"""
        print(f"\n📄 Parsing: {file_path.name}")

        content = file_path.read_text(encoding='utf-8')

        # Extract metadata
        metadata = self._extract_metadata(content)
        version = metadata.get('version', '1.0.0')

        # Parse standards from sections
        standards = []

        # Find all sections with "Standards:" subsections
        sections = self._split_into_sections(content)

        for section in sections:
            section_name = section.get('name', 'General')
            category = self._determine_category(section_name)

            # Find standards bullet points
            rules = self._extract_standards(section.get('content', ''))

            for rule in rules:
                standard = {
                    'id': str(uuid.uuid4()),
                    'name': rule['name'],
                    'description': rule['description'],
                    'language': language,
                    'category': category,
                    'severity': self._determine_severity(rule['description'], category),
                    'version': version,
                    'examples': rule.get('examples', []),
                    'file_source': file_path.name,
                    'section': section_name
                }
                standards.append(standard)

        print(f"  ✓ Extracted {len(standards)} standards")
        return standards

    def _extract_metadata(self, content: str) -> Dict[str, str]:
        """Extract metadata from markdown file"""
        metadata = {}

        # Version
        version_match = re.search(r'##\s+Version\s+([\d.]+)', content)
        if version_match:
            metadata['version'] = version_match.group(1)

        # Last Updated
        updated_match = re.search(r'\*\*Last Updated\*\*:\s*(.+)', content)
        if updated_match:
            metadata['last_updated'] = updated_match.group(1)

        # Status
        status_match = re.search(r'\*\*Status\*\*:\s*(.+)', content)
        if status_match:
            metadata['status'] = status_match.group(1)

        return metadata

    def _split_into_sections(self, content: str) -> List[Dict[str, Any]]:
        """Split content into major sections"""
        sections = []

        # Find all ## headers
        pattern = r'^##\s+(.+?)$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))

        for i, match in enumerate(matches):
            section_name = match.group(1).strip()
            start = match.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(content)
            section_content = content[start:end].strip()

            # Skip TOC and metadata sections
            if section_name.lower() not in ['table of contents', 'version']:
                sections.append({
                    'name': section_name,
                    'content': section_content
                })

        return sections

    def _extract_standards(self, content: str) -> List[Dict[str, Any]]:
        """Extract individual standards from section content"""
        standards = []

        # Look for "**Standards**:" or "Standards:" followed by bullet points
        standards_pattern = r'\*\*Standards\*\*:(.+?)(?=\n#{2,}|\n\*\*|$)'
        matches = re.finditer(standards_pattern, content, re.DOTALL)

        for match in matches:
            standards_text = match.group(1)

            # Extract bullet points
            bullets = re.findall(r'^[\-\*]\s+(.+)$', standards_text, re.MULTILINE)

            for bullet in bullets:
                # Clean up the text
                bullet = bullet.strip()
                if not bullet or bullet.startswith('```'):
                    continue

                # Extract rule name and description
                name, description = self._parse_bullet(bullet)

                standards.append({
                    'name': name,
                    'description': description,
                    'examples': []
                })

        return standards

    def _parse_bullet(self, bullet: str) -> tuple[str, str]:
        """Parse a bullet point into name and description"""
        # Try to extract a clear rule name
        # Pattern: "Use X for Y" or "Never do X" or "Always do Y"

        # If it's short (< 80 chars), use as name
        if len(bullet) < 80:
            name = bullet
            description = bullet
        else:
            # Take first sentence as name
            first_sentence = re.split(r'[.!?]', bullet)[0]
            name = first_sentence[:80] + '...' if len(first_sentence) > 80 else first_sentence
            description = bullet

        return name, description

    def _determine_category(self, section_name: str) -> str:
        """Determine category from section name"""
        section_lower = section_name.lower()

        if any(kw in section_lower for kw in ['error', 'exception', 'handling']):
            return 'error-handling'
        elif any(kw in section_lower for kw in ['security', 'auth', 'validation']):
            return 'security'
        elif any(kw in section_lower for kw in ['performance', 'optimization', 'async']):
            return 'performance'
        elif any(kw in section_lower for kw in ['test', 'testing']):
            return 'testing'
        elif any(kw in section_lower for kw in ['structure', 'organization', 'architecture']):
            return 'architecture'
        elif any(kw in section_lower for kw in ['style', 'format', 'naming']):
            return 'style'
        else:
            return 'best-practices'

    def _determine_severity(self, text: str, category: str) -> str:
        """Determine severity based on keywords and category"""
        text_lower = text.lower()

        # Check for explicit severity keywords
        for severity, keywords in self.severity_keywords.items():
            if any(kw in text_lower for kw in keywords):
                return severity

        # Default based on category
        if category == 'security':
            return 'critical'
        elif category in ['error-handling', 'performance']:
            return 'high'
        elif category in ['best-practices', 'architecture']:
            return 'medium'
        else:
            return 'low'


class StandardsImporter:
    """Import standards into Neo4j"""

    def __init__(self, neo4j_service: Neo4jService):
        self.neo4j = neo4j_service
        self.parser = StandardsParser()
        self.imported_count = 0
        self.failed_count = 0

    async def import_from_directory(
        self,
        directory: Path,
        language: str,
        recursive: bool = False
    ):
        """Import all markdown files from a directory"""
        print(f"\n{'='*60}")
        print(f"Importing {language.upper()} standards from: {directory}")
        print(f"{'='*60}")

        # Find all markdown files
        pattern = '**/*.md' if recursive else '*.md'
        md_files = list(directory.glob(pattern))

        print(f"\nFound {len(md_files)} markdown files")

        for md_file in md_files:
            await self.import_file(md_file, language)

        print(f"\n{'='*60}")
        print(f"Import Summary:")
        print(f"  ✅ Successfully imported: {self.imported_count}")
        if self.failed_count > 0:
            print(f"  ❌ Failed: {self.failed_count}")
        print(f"{'='*60}")

    async def import_file(self, file_path: Path, language: str):
        """Import standards from a single file"""
        try:
            # Parse the file
            standards_data = self.parser.parse_file(file_path, language)

            # Import each standard
            for std_data in standards_data:
                try:
                    standard = Standard(
                        id=std_data['id'],
                        name=std_data['name'],
                        language=std_data['language'],
                        category=std_data['category'],
                        description=std_data['description'],
                        severity=std_data['severity'],
                        examples=std_data['examples'],
                        created_at=datetime.now(),
                        updated_at=datetime.now(),
                        version=std_data['version'],
                        active=True
                    )

                    await self.neo4j.create_standard(standard)
                    self.imported_count += 1

                except Exception as e:
                    print(f"  ❌ Failed to import: {std_data['name'][:50]}... - {e}")
                    self.failed_count += 1

        except Exception as e:
            print(f"  ❌ Failed to parse file: {e}")
            self.failed_count += 1


async def main():
    """Main import script"""
    print("\n" + "="*60)
    print("  STANDARDS IMPORT SCRIPT")
    print("  Import markdown standards into Neo4j")
    print("="*60)

    # Load settings
    settings = Settings()

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

        # Create importer
        importer = StandardsImporter(neo4j)

        # Import standards for all languages (recursively to find subdirectories)
        standards_base = Path(settings.STANDARDS_BASE_PATH)

        # Discover all language directories
        if standards_base.exists():
            for lang_dir in sorted(standards_base.iterdir()):
                if lang_dir.is_dir() and not lang_dir.name.startswith('.'):
                    language = lang_dir.name
                    await importer.import_from_directory(lang_dir, language, recursive=True)
        else:
            print(f"❌ Standards directory not found: {standards_base}")

        print("\n✅ Import complete!")

        # Show summary
        async with neo4j.driver.session(database=settings.NEO4J_DATABASE) as session:
            result = await session.run('MATCH (s:Standard) RETURN count(s) as count')
            record = await result.single()
            total = record['count'] if record else 0
            print(f"\n📊 Total standards in database: {total}")

            # Show breakdown by category
            result = await session.run('''
                MATCH (s:Standard)
                RETURN s.category as category, count(s) as count
                ORDER BY count DESC
            ''')
            print("\nStandards by category:")
            async for record in result:
                print(f"  {record['category']}: {record['count']}")

            # Show breakdown by severity
            result = await session.run('''
                MATCH (s:Standard)
                RETURN s.severity as severity, count(s) as count
                ORDER BY
                    CASE s.severity
                        WHEN 'critical' THEN 1
                        WHEN 'high' THEN 2
                        WHEN 'medium' THEN 3
                        WHEN 'low' THEN 4
                    END
            ''')
            print("\nStandards by severity:")
            async for record in result:
                print(f"  {record['severity']}: {record['count']}")

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    finally:
        await neo4j.disconnect()
        print("\n👋 Disconnected from Neo4j")


if __name__ == '__main__':
    asyncio.run(main())
