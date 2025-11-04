"""
Standards Synchronization Service

Automatically synchronizes markdown standards files with Neo4j database.
Detects file changes and updates the database incrementally.
"""

import asyncio
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Set, Any
import structlog

from services.neo4j_service import Neo4jService, Standard
from scripts.import_standards import StandardsParser

logger = structlog.get_logger()


class FileMetadata:
    """Track metadata for standards files"""

    def __init__(self, file_path: Path):
        self.path = file_path
        self.last_modified = file_path.stat().st_mtime if file_path.exists() else 0
        self.content_hash = self._calculate_hash() if file_path.exists() else ""
        self.standards_count = 0

    def _calculate_hash(self) -> str:
        """Calculate SHA256 hash of file content"""
        try:
            content = self.path.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except Exception as e:
            logger.warning(f"Failed to hash {self.path}: {e}")
            return ""

    def has_changed(self, other: 'FileMetadata') -> bool:
        """Check if file has changed compared to another metadata"""
        return (self.last_modified != other.last_modified or
                self.content_hash != other.content_hash)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage"""
        return {
            'path': str(self.path),
            'last_modified': self.last_modified,
            'content_hash': self.content_hash,
            'standards_count': self.standards_count
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'FileMetadata':
        """Create from dictionary"""
        metadata = cls(Path(data['path']))
        metadata.last_modified = data.get('last_modified', 0)
        metadata.content_hash = data.get('content_hash', '')
        metadata.standards_count = data.get('standards_count', 0)
        return metadata


class StandardsSyncService:
    """
    Service for synchronizing standards files with Neo4j database
    """

    def __init__(
        self,
        neo4j_service: Neo4jService,
        standards_dir: Path,
        metadata_file: Optional[Path] = None
    ):
        self.neo4j = neo4j_service
        self.standards_dir = Path(standards_dir)
        self.metadata_file = metadata_file or (self.standards_dir / '.sync_metadata.json')
        self.parser = StandardsParser()

        # Load cached metadata
        self.file_metadata: Dict[str, FileMetadata] = self._load_metadata()

        # Statistics
        self.stats = {
            'files_added': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'standards_added': 0,
            'standards_updated': 0,
            'standards_deleted': 0,
            'last_sync': None
        }

    def _load_metadata(self) -> Dict[str, FileMetadata]:
        """Load cached file metadata from disk"""
        if not self.metadata_file.exists():
            return {}

        try:
            data = json.loads(self.metadata_file.read_text())
            return {
                path: FileMetadata.from_dict(meta)
                for path, meta in data.items()
            }
        except Exception as e:
            logger.warning(f"Failed to load metadata: {e}")
            return {}

    def _save_metadata(self):
        """Save file metadata to disk"""
        try:
            data = {
                path: meta.to_dict()
                for path, meta in self.file_metadata.items()
            }
            self.metadata_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save metadata: {e}")

    async def sync_all(self, force: bool = False) -> Dict[str, Any]:
        """
        Synchronize all standards files with database

        Args:
            force: If True, reimport all files regardless of changes

        Returns:
            Dictionary with sync statistics
        """
        logger.info("Starting standards synchronization", force=force)
        start_time = datetime.now()

        # Reset statistics
        self.stats = {
            'files_added': 0,
            'files_updated': 0,
            'files_deleted': 0,
            'standards_added': 0,
            'standards_updated': 0,
            'standards_deleted': 0,
            'last_sync': start_time.isoformat()
        }

        try:
            # Find all markdown files
            current_files = self._discover_files()

            # Detect changes
            changes = self._detect_changes(current_files, force)

            # Process changes
            await self._process_additions(changes['added'])
            await self._process_updates(changes['modified'])
            await self._process_deletions(changes['deleted'])

            # Save metadata
            self._save_metadata()

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds()
            self.stats['duration_seconds'] = duration

            logger.info("Synchronization complete", stats=self.stats)

        except Exception as e:
            logger.error("Synchronization failed", error=str(e))
            raise

        return self.stats

    def _discover_files(self) -> Dict[str, Path]:
        """Discover all markdown files in standards directory"""
        files = {}

        for language_dir in self.standards_dir.iterdir():
            if not language_dir.is_dir():
                continue

            # Find markdown files
            for md_file in language_dir.glob('*.md'):
                # Skip hidden files and metadata
                if md_file.name.startswith('.'):
                    continue

                # Use relative path as key
                rel_path = str(md_file.relative_to(self.standards_dir))
                files[rel_path] = md_file

        logger.info(f"Discovered {len(files)} markdown files")
        return files

    def _detect_changes(
        self,
        current_files: Dict[str, Path],
        force: bool
    ) -> Dict[str, List[str]]:
        """
        Detect which files have been added, modified, or deleted

        Returns:
            Dictionary with 'added', 'modified', 'deleted' file lists
        """
        changes = {
            'added': [],
            'modified': [],
            'deleted': []
        }

        # Find new and modified files
        for rel_path, file_path in current_files.items():
            current_meta = FileMetadata(file_path)

            if rel_path not in self.file_metadata:
                # New file
                changes['added'].append(rel_path)
                self.file_metadata[rel_path] = current_meta
            elif force or current_meta.has_changed(self.file_metadata[rel_path]):
                # Modified file
                changes['modified'].append(rel_path)
                self.file_metadata[rel_path] = current_meta

        # Find deleted files
        cached_paths = set(self.file_metadata.keys())
        current_paths = set(current_files.keys())
        deleted_paths = cached_paths - current_paths

        for rel_path in deleted_paths:
            changes['deleted'].append(rel_path)

        logger.info(
            "Detected changes",
            added=len(changes['added']),
            modified=len(changes['modified']),
            deleted=len(changes['deleted'])
        )

        return changes

    async def _process_additions(self, file_paths: List[str]):
        """Process newly added files"""
        for rel_path in file_paths:
            try:
                file_path = self.standards_dir / rel_path
                language = self._detect_language(file_path)

                await self._import_file(file_path, language)
                self.stats['files_added'] += 1

                logger.info(f"Added standards from {rel_path}")

            except Exception as e:
                logger.error(f"Failed to process addition: {rel_path}", error=str(e))

    async def _process_updates(self, file_paths: List[str]):
        """Process modified files"""
        for rel_path in file_paths:
            try:
                file_path = self.standards_dir / rel_path
                language = self._detect_language(file_path)

                # Delete old standards from this file
                await self._delete_standards_from_file(str(file_path))

                # Re-import updated standards
                await self._import_file(file_path, language)
                self.stats['files_updated'] += 1

                logger.info(f"Updated standards from {rel_path}")

            except Exception as e:
                logger.error(f"Failed to process update: {rel_path}", error=str(e))

    async def _process_deletions(self, file_paths: List[str]):
        """Process deleted files"""
        for rel_path in file_paths:
            try:
                file_path = self.standards_dir / rel_path

                # Delete standards from this file
                await self._delete_standards_from_file(str(file_path))

                # Remove from metadata
                if rel_path in self.file_metadata:
                    del self.file_metadata[rel_path]

                self.stats['files_deleted'] += 1
                logger.info(f"Deleted standards from {rel_path}")

            except Exception as e:
                logger.error(f"Failed to process deletion: {rel_path}", error=str(e))

    async def _import_file(self, file_path: Path, language: str):
        """Import standards from a file"""
        # Parse the file
        standards_data = self.parser.parse_file(file_path, language)

        # Store file source in each standard
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

                # Add file_source as a property (we'll need to modify the Standard model)
                await self._create_standard_with_source(standard, str(file_path))
                self.stats['standards_added'] += 1

            except Exception as e:
                logger.warning(f"Failed to import standard: {std_data.get('name')}", error=str(e))

        # Update metadata
        rel_path = str(file_path.relative_to(self.standards_dir))
        if rel_path in self.file_metadata:
            self.file_metadata[rel_path].standards_count = len(standards_data)

    async def _create_standard_with_source(self, standard: Standard, file_source: str):
        """Create standard with file source tracking"""
        async with self.neo4j.driver.session(database=self.neo4j.database) as session:
            query = """
            CREATE (s:Standard {
                id: $id,
                name: $name,
                language: $language,
                category: $category,
                description: $description,
                severity: $severity,
                examples: $examples,
                created_at: $created_at,
                updated_at: $updated_at,
                version: $version,
                active: $active,
                file_source: $file_source
            })
            RETURN s
            """

            await session.run(
                query,
                id=standard.id,
                name=standard.name,
                language=standard.language,
                category=standard.category,
                description=standard.description,
                severity=standard.severity,
                examples=json.dumps(standard.examples),
                created_at=standard.created_at.isoformat(),
                updated_at=standard.updated_at.isoformat(),
                version=standard.version,
                active=standard.active,
                file_source=file_source
            )

    async def _delete_standards_from_file(self, file_path: str):
        """Delete all standards that came from a specific file"""
        async with self.neo4j.driver.session(database=self.neo4j.database) as session:
            query = """
            MATCH (s:Standard {file_source: $file_source})
            DELETE s
            RETURN count(s) as deleted_count
            """

            result = await session.run(query, file_source=file_path)
            record = await result.single()

            if record:
                deleted = record['deleted_count']
                self.stats['standards_deleted'] += deleted
                logger.info(f"Deleted {deleted} standards from {file_path}")

    def _detect_language(self, file_path: Path) -> str:
        """Detect language from file path"""
        # Language is the parent directory name
        return file_path.parent.name

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get current synchronization status"""
        # Count files and standards
        total_files = len(self.file_metadata)
        total_standards = sum(
            meta.standards_count
            for meta in self.file_metadata.values()
        )

        # Get database counts
        async with self.neo4j.driver.session(database=self.neo4j.database) as session:
            result = await session.run('MATCH (s:Standard) RETURN count(s) as count')
            record = await result.single()
            db_standards = record['count'] if record else 0

        return {
            'files_tracked': total_files,
            'standards_in_files': total_standards,
            'standards_in_database': db_standards,
            'last_sync': self.stats.get('last_sync'),
            'metadata_file': str(self.metadata_file),
            'is_synchronized': total_standards == db_standards
        }


class ScheduledSyncService:
    """
    Scheduled synchronization service for background tasks
    """

    def __init__(
        self,
        sync_service: StandardsSyncService,
        interval_seconds: int = 3600  # Default: 1 hour
    ):
        self.sync_service = sync_service
        self.interval_seconds = interval_seconds
        self.task: Optional[asyncio.Task] = None
        self.running = False

    async def start(self):
        """Start the scheduled synchronization"""
        if self.running:
            logger.warning("Sync service already running")
            return

        self.running = True
        self.task = asyncio.create_task(self._run_loop())
        logger.info(f"Started scheduled sync (interval: {self.interval_seconds}s)")

    async def stop(self):
        """Stop the scheduled synchronization"""
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
        logger.info("Stopped scheduled sync")

    async def _run_loop(self):
        """Main synchronization loop"""
        while self.running:
            try:
                # Run synchronization
                stats = await self.sync_service.sync_all()

                # Log results
                if any(v > 0 for k, v in stats.items() if k.startswith(('files_', 'standards_'))):
                    logger.info("Sync detected changes", stats=stats)
                else:
                    logger.debug("Sync: no changes detected")

            except Exception as e:
                logger.error("Sync loop error", error=str(e))

            # Wait for next sync
            try:
                await asyncio.sleep(self.interval_seconds)
            except asyncio.CancelledError:
                break
