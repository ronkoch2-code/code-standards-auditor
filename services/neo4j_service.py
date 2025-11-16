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
            WHERE $active_only = false OR s.active = true
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
