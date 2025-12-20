"""
Neo4j Graph Database Service
Manages relationships between standards, code patterns, and violations
"""

import asyncio
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict
import json
import structlog

from neo4j import AsyncGraphDatabase, AsyncDriver, AsyncSession
from neo4j.exceptions import ServiceUnavailable, SessionExpired

logger = structlog.get_logger()


@dataclass
class Standard:
    """Represents a coding standard"""
    id: str
    name: str
    language: str
    category: str
    description: str
    severity: str
    examples: List[Dict[str, str]]
    created_at: datetime
    updated_at: datetime
    version: str
    active: bool = True

    def to_dict(self) -> Dict[str, Any]:
        """Convert Standard to dictionary with content alias for description."""
        result = asdict(self)
        # Add content as alias for description (used by many consumers)
        result["content"] = self.description
        # Convert datetime to ISO format strings
        if isinstance(result.get("created_at"), datetime):
            result["created_at"] = result["created_at"].isoformat()
        if isinstance(result.get("updated_at"), datetime):
            result["updated_at"] = result["updated_at"].isoformat()
        return result

    def get(self, key: str, default: Any = None) -> Any:
        """Dict-like get method for backwards compatibility."""
        return self.to_dict().get(key, default)


@dataclass
class Violation:
    """Represents a code violation"""
    id: str
    standard_id: str
    file_path: str
    line: int
    column: int
    message: str
    severity: str
    suggestion: str
    project_id: str
    timestamp: datetime


@dataclass
class CodePattern:
    """Represents a code pattern"""
    id: str
    pattern: str
    language: str
    description: str
    category: str
    frequency: int
    first_seen: datetime
    last_seen: datetime


class Neo4jService:
    """
    Service for interacting with Neo4j graph database
    Manages relationships between standards, violations, and patterns
    """
    
    def __init__(
        self,
        uri: str,
        user: str,
        password: str,
        database: str = "neo4j",
        max_connection_lifetime: int = 3600,
        max_connection_pool_size: int = 50
    ):
        self.uri = uri
        self.user = user
        self.password = password
        self.database = database
        self.driver: Optional[AsyncDriver] = None
        
        # Connection configuration
        self.config = {
            "max_connection_lifetime": max_connection_lifetime,
            "max_connection_pool_size": max_connection_pool_size,
            "connection_acquisition_timeout": 60,
            "connection_timeout": 30,
            "keep_alive": True
        }
    
    async def connect(self):
        """
        Establish connection to Neo4j database
        """
        try:
            self.driver = AsyncGraphDatabase.driver(
                self.uri,
                auth=(self.user, self.password),
                **self.config
            )
            
            # Verify connectivity
            await self.driver.verify_connectivity()
            
            # Create indexes and constraints
            await self._create_indexes()
            
            logger.info(f"Connected to Neo4j at {self.uri}")
            
        except Exception as e:
            logger.error(f"Failed to connect to Neo4j: {e}")
            raise
    
    async def disconnect(self):
        """
        Close Neo4j connection
        """
        if self.driver:
            await self.driver.close()
            logger.info("Disconnected from Neo4j")
    
    async def health_check(self) -> bool:
        """
        Check Neo4j connection health
        """
        if not self.driver:
            return False

        try:
            await self.driver.verify_connectivity()
            return True
        except (ServiceUnavailable, SessionExpired, OSError, ConnectionError) as e:
            # Neo4j connection/network issues
            logger.debug("Neo4j health check failed", error=str(e))
            return False
    
    async def _create_indexes(self):
        """
        Create necessary indexes and constraints
        """
        async with self.driver.session(database=self.database) as session:
            queries = [
                # Unique constraints
                "CREATE CONSTRAINT standard_id IF NOT EXISTS FOR (s:Standard) REQUIRE s.id IS UNIQUE",
                "CREATE CONSTRAINT violation_id IF NOT EXISTS FOR (v:Violation) REQUIRE v.id IS UNIQUE",
                "CREATE CONSTRAINT pattern_id IF NOT EXISTS FOR (p:CodePattern) REQUIRE p.id IS UNIQUE",
                "CREATE CONSTRAINT project_id IF NOT EXISTS FOR (p:Project) REQUIRE p.id IS UNIQUE",
                
                # Indexes for performance
                "CREATE INDEX standard_language IF NOT EXISTS FOR (s:Standard) ON (s.language)",
                "CREATE INDEX standard_category IF NOT EXISTS FOR (s:Standard) ON (s.category)",
                "CREATE INDEX violation_severity IF NOT EXISTS FOR (v:Violation) ON (v.severity)",
                "CREATE INDEX violation_timestamp IF NOT EXISTS FOR (v:Violation) ON (v.timestamp)",
                "CREATE INDEX pattern_language IF NOT EXISTS FOR (p:CodePattern) ON (p.language)",
                "CREATE INDEX pattern_category IF NOT EXISTS FOR (p:CodePattern) ON (p.category)",
            ]
            
            for query in queries:
                try:
                    await session.run(query)
                except Exception as e:
                    # Index might already exist, log and continue
                    logger.debug(f"Index creation: {e}")
    
    # Standards Management
    
    async def create_standard(self, standard: Standard) -> Standard:
        """
        Create a new coding standard
        """
        async with self.driver.session(database=self.database) as session:
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
                active: $active
            })
            RETURN s
            """
            
            result = await session.run(
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
                active=standard.active
            )
            
            record = await result.single()
            logger.info(f"Created standard: {standard.id}")
            return standard

    async def create_standard_from_dict(
        self,
        standard_id: str = None,
        name: str = None,
        title: str = None,  # Alias for name
        language: str = "general",
        category: str = "general",
        description: str = None,
        content: str = None,  # Alias for description
        severity: str = "info",
        examples: List[Dict[str, str]] = None,
        version: str = "1.0.0",
        metadata: Dict[str, Any] = None,
        active: bool = True
    ) -> Optional[Standard]:
        """
        Create a standard from keyword arguments.

        This method accepts the varied parameter names used by different callers
        and maps them to the Standard dataclass fields.
        """
        import uuid

        # Map aliases
        actual_name = name or title or "Unnamed Standard"
        actual_description = description or content or ""
        actual_id = standard_id or f"std_{uuid.uuid4().hex[:12]}"

        # Create Standard object
        now = datetime.now()
        standard = Standard(
            id=actual_id,
            name=actual_name,
            language=language,
            category=category,
            description=actual_description,
            severity=severity,
            examples=examples or [],
            created_at=now,
            updated_at=now,
            version=version,
            active=active
        )

        # Use the existing create_standard method
        return await self.create_standard(standard)

    async def get_standard(self, standard_id: str) -> Optional[Standard]:
        """
        Get a standard by ID
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (s:Standard {id: $id})
            RETURN s
            """
            
            result = await session.run(query, id=standard_id)
            record = await result.single()
            
            if record:
                node = record["s"]
                return Standard(
                    id=node["id"],
                    name=node["name"],
                    language=node["language"],
                    category=node["category"],
                    description=node["description"],
                    severity=node["severity"],
                    examples=json.loads(node["examples"]),
                    created_at=datetime.fromisoformat(node["created_at"]),
                    updated_at=datetime.fromisoformat(node["updated_at"]),
                    version=node["version"],
                    active=node["active"]
                )
            return None
    
    async def get_standards_by_language(
        self,
        language: str,
        active_only: bool = True
    ) -> List[Standard]:
        """
        Get all standards for a specific language
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (s:Standard {language: $language})
            WHERE $active_only = false OR COALESCE(s.active, true) = true
            RETURN s
            ORDER BY s.category, s.name
            """

            result = await session.run(
                query,
                language=language,
                active_only=active_only
            )

            standards = []
            async for record in result:
                node = record["s"]
                standards.append(Standard(
                    id=node["id"],
                    name=node["name"],
                    language=node["language"],
                    category=node["category"],
                    description=node["description"],
                    severity=node["severity"],
                    examples=json.loads(node["examples"]),
                    created_at=datetime.fromisoformat(node["created_at"]),
                    updated_at=datetime.fromisoformat(node["updated_at"]),
                    version=node["version"],
                    active=node["active"]
                ))

            return standards

    async def get_all_standards(
        self,
        limit: int = 100,
        offset: int = 0,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all standards with pagination.
        Returns standards as dictionaries for flexibility.
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (s:Standard)
            RETURN s
            ORDER BY s.language, s.category, s.name
            SKIP $offset
            LIMIT $limit
            """

            result = await session.run(
                query,
                offset=offset,
                limit=limit
            )

            standards = []
            async for record in result:
                node = record["s"]
                standards.append({
                    "id": node.get("id", ""),
                    "name": node.get("name", ""),
                    "language": node.get("language", ""),
                    "category": node.get("category", ""),
                    "description": node.get("description", ""),
                    "severity": node.get("severity", "medium"),
                    "examples": json.loads(node["examples"]) if isinstance(node.get("examples"), str) else node.get("examples", []),
                    "content": node.get("description", ""),
                    "created_at": node.get("created_at", ""),
                    "updated_at": node.get("updated_at", ""),
                    "version": node.get("version", "1.0.0"),
                    "active": node.get("active", True)
                })

            logger.info(f"Found {len(standards)} standards (limit={limit}, offset={offset})")
            return standards

    async def get_standards_by_category(
        self,
        category: str,
        active_only: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get all standards for a specific category
        Returns standards as dictionaries for flexibility
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (s:Standard {category: $category})
            WHERE $active_only = false OR COALESCE(s.active, true) = true
            RETURN s
            ORDER BY s.language, s.name
            """

            result = await session.run(
                query,
                category=category,
                active_only=active_only
            )

            standards = []
            async for record in result:
                node = record["s"]
                standards.append({
                    "id": node["id"],
                    "name": node["name"],
                    "language": node["language"],
                    "category": node["category"],
                    "description": node["description"],
                    "severity": node["severity"],
                    "examples": json.loads(node["examples"]) if isinstance(node["examples"], str) else node["examples"],
                    "content": node.get("description", ""),  # Using description as content for now
                    "created_at": node["created_at"],
                    "updated_at": node["updated_at"],
                    "version": node["version"],
                    "active": node["active"]
                })

            logger.info(f"Found {len(standards)} standards for category: {category}")
            return standards

    async def find_standards_by_criteria(
        self,
        criteria: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Find standards by flexible criteria
        Supports: language, category, context_type, agent_type, patterns
        """
        async with self.driver.session(database=self.database) as session:
            # Build dynamic query based on criteria
            where_clauses = ["COALESCE(s.active, true) = true"]  # Always filter active standards
            params = {}

            if "language" in criteria:
                where_clauses.append("s.language = $language")
                params["language"] = criteria["language"]

            if "category" in criteria:
                where_clauses.append("s.category = $category")
                params["category"] = criteria["category"]

            if "context_type" in criteria:
                # Match context_type with category (e.g., code_review -> review, testing -> testing)
                where_clauses.append("(s.category = $context_type OR s.category = 'general')")
                params["context_type"] = criteria["context_type"]

            where_clause = " AND ".join(where_clauses) if where_clauses else "true"

            query = f"""
            MATCH (s:Standard)
            WHERE {where_clause}
            RETURN s
            ORDER BY s.severity DESC, s.category, s.name
            LIMIT 50
            """

            result = await session.run(query, **params)

            standards = []
            async for record in result:
                node = record["s"]
                standards.append({
                    "id": node["id"],
                    "name": node["name"],
                    "title": node["name"],
                    "language": node["language"],
                    "category": node["category"],
                    "description": node["description"],
                    "severity": node["severity"],
                    "examples": json.loads(node["examples"]) if isinstance(node["examples"], str) else node["examples"],
                    "content": node.get("description", ""),
                    "created_at": node["created_at"],
                    "updated_at": node["updated_at"],
                    "version": node["version"],
                    "active": node["active"]
                })

            logger.info(f"Found {len(standards)} standards matching criteria: {criteria}")
            return standards

    async def semantic_search(
        self,
        query: str,
        context: Dict[str, Any],
        limit: int = 10,
        threshold: float = 0.5
    ) -> Dict[str, Any]:
        """
        Semantic search for standards
        Returns results with relevance scores
        """
        async with self.driver.session(database=self.database) as session:
            # For now, use text-based matching
            # In future, can integrate vector embeddings

            # Extract search terms
            search_term = query.lower()

            # Build query to match on name, description, or category
            cypher_query = """
            MATCH (s:Standard)
            WHERE COALESCE(s.active, true) = true
            AND (
                toLower(s.name) CONTAINS $search_term
                OR toLower(s.description) CONTAINS $search_term
                OR toLower(s.category) CONTAINS $search_term
            )
            RETURN s,
                   CASE
                     WHEN toLower(s.name) CONTAINS $search_term THEN 1.0
                     WHEN toLower(s.description) CONTAINS $search_term THEN 0.8
                     WHEN toLower(s.category) CONTAINS $search_term THEN 0.6
                     ELSE 0.5
                   END as relevance_score
            ORDER BY relevance_score DESC, s.name
            LIMIT $limit
            """

            result = await session.run(
                cypher_query,
                search_term=search_term,
                limit=limit
            )

            results = []
            async for record in result:
                node = record["s"]
                score = record["relevance_score"]

                if score >= threshold:
                    results.append({
                        "id": node["id"],
                        "name": node["name"],
                        "language": node["language"],
                        "category": node["category"],
                        "description": node["description"],
                        "relevance_score": score,
                        "content": node.get("description", "")
                    })

            logger.info(f"Semantic search for '{query}' returned {len(results)} results")

            return {
                "results": results,
                "metadata": {
                    "query": query,
                    "total_results": len(results),
                    "context": context
                }
            }
    
    async def update_standard(
        self,
        standard_id: str,
        updates: Dict[str, Any]
    ) -> Optional[Standard]:
        """
        Update an existing standard
        """
        async with self.driver.session(database=self.database) as session:
            # Build SET clause dynamically
            set_clauses = []
            params = {"id": standard_id}
            
            for key, value in updates.items():
                if key not in ["id", "created_at"]:  # Don't update these fields
                    set_clauses.append(f"s.{key} = ${key}")
                    if key == "examples":
                        params[key] = json.dumps(value)
                    elif isinstance(value, datetime):
                        params[key] = value.isoformat()
                    else:
                        params[key] = value
            
            # Always update the updated_at timestamp
            set_clauses.append("s.updated_at = $updated_at")
            params["updated_at"] = datetime.now().isoformat()
            
            query = f"""
            MATCH (s:Standard {{id: $id}})
            SET {', '.join(set_clauses)}
            RETURN s
            """
            
            result = await session.run(query, **params)
            record = await result.single()
            
            if record:
                return await self.get_standard(standard_id)
            return None
    
    # Violations Management
    
    async def record_violation(self, violation: Violation) -> Violation:
        """
        Record a code violation
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (s:Standard {id: $standard_id})
            MERGE (p:Project {id: $project_id})
            CREATE (v:Violation {
                id: $id,
                file_path: $file_path,
                line: $line,
                column: $column,
                message: $message,
                severity: $severity,
                suggestion: $suggestion,
                timestamp: $timestamp
            })
            CREATE (v)-[:VIOLATES]->(s)
            CREATE (v)-[:IN_PROJECT]->(p)
            RETURN v
            """
            
            result = await session.run(
                query,
                id=violation.id,
                standard_id=violation.standard_id,
                project_id=violation.project_id,
                file_path=violation.file_path,
                line=violation.line,
                column=violation.column,
                message=violation.message,
                severity=violation.severity,
                suggestion=violation.suggestion,
                timestamp=violation.timestamp.isoformat()
            )
            
            record = await result.single()
            logger.info(f"Recorded violation: {violation.id}")
            return violation
    
    async def get_project_violations(
        self,
        project_id: str,
        severity: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Get violations for a project
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (v:Violation)-[:IN_PROJECT]->(p:Project {id: $project_id})
            MATCH (v)-[:VIOLATES]->(s:Standard)
            WHERE $severity IS NULL OR v.severity = $severity
            RETURN v, s
            ORDER BY v.timestamp DESC
            LIMIT $limit
            """
            
            result = await session.run(
                query,
                project_id=project_id,
                severity=severity,
                limit=limit
            )
            
            violations = []
            async for record in result:
                v_node = record["v"]
                s_node = record["s"]
                violations.append({
                    "violation": {
                        "id": v_node["id"],
                        "file_path": v_node["file_path"],
                        "line": v_node["line"],
                        "column": v_node["column"],
                        "message": v_node["message"],
                        "severity": v_node["severity"],
                        "suggestion": v_node["suggestion"],
                        "timestamp": v_node["timestamp"]
                    },
                    "standard": {
                        "id": s_node["id"],
                        "name": s_node["name"],
                        "category": s_node["category"]
                    }
                })
            
            return violations
    
    # Pattern Management
    
    async def record_pattern(self, pattern: CodePattern) -> CodePattern:
        """
        Record a detected code pattern
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MERGE (p:CodePattern {id: $id})
            ON CREATE SET
                p.pattern = $pattern,
                p.language = $language,
                p.description = $description,
                p.category = $category,
                p.frequency = $frequency,
                p.first_seen = $first_seen,
                p.last_seen = $last_seen
            ON MATCH SET
                p.frequency = p.frequency + $frequency,
                p.last_seen = $last_seen
            RETURN p
            """
            
            result = await session.run(
                query,
                id=pattern.id,
                pattern=pattern.pattern,
                language=pattern.language,
                description=pattern.description,
                category=pattern.category,
                frequency=pattern.frequency,
                first_seen=pattern.first_seen.isoformat(),
                last_seen=pattern.last_seen.isoformat()
            )
            
            record = await result.single()
            logger.info(f"Recorded pattern: {pattern.id}")
            return pattern
    
    async def get_emerging_patterns(
        self,
        language: str,
        min_frequency: int = 10,
        days: int = 30
    ) -> List[CodePattern]:
        """
        Get emerging patterns that might become new standards
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (p:CodePattern {language: $language})
            WHERE p.frequency >= $min_frequency
            AND datetime(p.last_seen) >= datetime() - duration({days: $days})
            AND NOT EXISTS {
                MATCH (p)-[:EVOLVED_INTO]->(:Standard)
            }
            RETURN p
            ORDER BY p.frequency DESC
            """
            
            result = await session.run(
                query,
                language=language,
                min_frequency=min_frequency,
                days=days
            )
            
            patterns = []
            async for record in result:
                node = record["p"]
                patterns.append(CodePattern(
                    id=node["id"],
                    pattern=node["pattern"],
                    language=node["language"],
                    description=node["description"],
                    category=node["category"],
                    frequency=node["frequency"],
                    first_seen=datetime.fromisoformat(node["first_seen"]),
                    last_seen=datetime.fromisoformat(node["last_seen"])
                ))
            
            return patterns
    
    async def evolve_pattern_to_standard(
        self,
        pattern_id: str,
        standard: Standard
    ) -> bool:
        """
        Mark a pattern as evolved into a standard
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (p:CodePattern {id: $pattern_id})
            CREATE (s:Standard {
                id: $standard_id,
                name: $name,
                language: $language,
                category: $category,
                description: $description,
                severity: $severity,
                examples: $examples,
                created_at: $created_at,
                updated_at: $updated_at,
                version: $version,
                active: $active
            })
            CREATE (p)-[:EVOLVED_INTO {timestamp: $timestamp}]->(s)
            RETURN s
            """
            
            result = await session.run(
                query,
                pattern_id=pattern_id,
                standard_id=standard.id,
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
                timestamp=datetime.now().isoformat()
            )
            
            record = await result.single()
            return record is not None
    
    # Analytics and Reporting
    
    async def get_violation_statistics(
        self,
        project_id: Optional[str] = None,
        language: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get violation statistics
        """
        async with self.driver.session(database=self.database) as session:
            # Build query conditionally
            match_clause = "MATCH (v:Violation)"
            where_clauses = []
            params = {}
            
            if project_id:
                match_clause += "-[:IN_PROJECT]->(p:Project {id: $project_id})"
                params["project_id"] = project_id
            
            if language:
                match_clause += "-[:VIOLATES]->(s:Standard {language: $language})"
                params["language"] = language
            elif not project_id:
                match_clause += "-[:VIOLATES]->(s:Standard)"
            
            query = f"""
            {match_clause}
            WITH v.severity as severity, count(v) as count
            RETURN severity, count
            ORDER BY count DESC
            """
            
            result = await session.run(query, **params)
            
            stats = {
                "by_severity": {},
                "total": 0
            }
            
            async for record in result:
                severity = record["severity"]
                count = record["count"]
                stats["by_severity"][severity] = count
                stats["total"] += count
            
            return stats
    
    async def get_standards_evolution_graph(
        self,
        language: str,
        days: int = 90
    ) -> Dict[str, Any]:
        """
        Get the evolution graph of standards over time
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (s:Standard {language: $language})
            WHERE datetime(s.created_at) >= datetime() - duration({days: $days})
            OPTIONAL MATCH (p:CodePattern)-[:EVOLVED_INTO]->(s)
            RETURN s, collect(p) as patterns
            ORDER BY s.created_at DESC
            """
            
            result = await session.run(
                query,
                language=language,
                days=days
            )
            
            evolution_data = {
                "standards": [],
                "patterns_evolved": 0,
                "timeline": []
            }
            
            async for record in result:
                s_node = record["s"]
                patterns = record["patterns"]
                
                standard_data = {
                    "id": s_node["id"],
                    "name": s_node["name"],
                    "created_at": s_node["created_at"],
                    "evolved_from_patterns": len(patterns)
                }
                
                evolution_data["standards"].append(standard_data)
                if patterns:
                    evolution_data["patterns_evolved"] += len(patterns)
            
            return evolution_data

    # Duplicate Management

    async def find_duplicate_standards(self) -> List[Dict[str, Any]]:
        """
        Find duplicate standards based on (language, category, name).
        Returns groups of duplicates with their IDs.
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MATCH (s:Standard)
            WITH s.language AS language, s.category AS category, s.name AS name,
                 COLLECT(s.id) AS ids, COUNT(s) AS count
            WHERE count > 1
            RETURN language, category, name, ids, count
            ORDER BY count DESC, language, category, name
            """

            result = await session.run(query)
            duplicates = []
            async for record in result:
                duplicates.append({
                    "language": record["language"],
                    "category": record["category"],
                    "name": record["name"],
                    "ids": record["ids"],
                    "count": record["count"]
                })

            logger.info(f"Found {len(duplicates)} duplicate groups")
            return duplicates

    async def cleanup_duplicate_standards(self, keep_strategy: str = "first") -> Dict[str, Any]:
        """
        Remove duplicate standards, keeping one per (language, category, name) group.

        Args:
            keep_strategy: "first" keeps first occurrence, "newest" keeps most recent

        Returns:
            Summary of cleanup operation
        """
        duplicates = await self.find_duplicate_standards()

        if not duplicates:
            return {
                "deleted_count": 0,
                "duplicate_groups": 0,
                "message": "No duplicates found"
            }

        deleted_total = 0

        async with self.driver.session(database=self.database) as session:
            for dup in duplicates:
                # Keep first ID, delete the rest
                ids_to_delete = dup["ids"][1:]  # Skip first one

                delete_query = """
                MATCH (s:Standard)
                WHERE s.id IN $ids
                DETACH DELETE s
                RETURN count(*) AS deleted
                """

                result = await session.run(delete_query, ids=ids_to_delete)
                record = await result.single()
                deleted_total += record["deleted"] if record else 0

        logger.info(f"Cleanup complete: deleted {deleted_total} duplicate standards from {len(duplicates)} groups")

        return {
            "deleted_count": deleted_total,
            "duplicate_groups": len(duplicates),
            "message": f"Deleted {deleted_total} duplicate standards"
        }

    async def upsert_standard(self, standard: Standard) -> Standard:
        """
        Insert or update a standard using MERGE to prevent duplicates.
        Uses (language, category, name) as the unique key.
        """
        async with self.driver.session(database=self.database) as session:
            query = """
            MERGE (s:Standard {language: $language, category: $category, name: $name})
            ON CREATE SET
                s.id = $id,
                s.description = $description,
                s.severity = $severity,
                s.examples = $examples,
                s.created_at = $created_at,
                s.updated_at = $updated_at,
                s.version = $version,
                s.active = $active
            ON MATCH SET
                s.description = $description,
                s.severity = $severity,
                s.examples = $examples,
                s.updated_at = $updated_at,
                s.version = $version,
                s.active = $active
            RETURN s
            """

            result = await session.run(
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
                active=standard.active
            )

            record = await result.single()
            logger.info(f"Upserted standard: {standard.language}/{standard.category}/{standard.name}")
            return standard
