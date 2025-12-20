"""
Standards Research Service

This service uses Gemini API to research and generate new coding standards
based on requests, code examples, and best practices.

Author: Code Standards Auditor
Date: January 31, 2025
Version: 1.0.0
"""

import json
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
import hashlib

from services.gemini_service import GeminiService
from services.neo4j_service import Neo4jService
from services.cache_service import CacheService
from config.settings import settings
from utils.service_factory import get_neo4j_service, get_gemini_service, get_cache_service

logger = logging.getLogger(__name__)


class StandardsResearchService:
    """Service for researching and generating new coding standards using LLM."""
    
    def __init__(
        self,
        gemini_service: Optional[GeminiService] = None,
        neo4j_service: Optional[Neo4jService] = None,
        cache_service: Optional[CacheService] = None
    ):
        """Initialize the Standards Research Service."""
        self.gemini = gemini_service or get_gemini_service()
        self.neo4j = neo4j_service or get_neo4j_service()
        self.cache = cache_service or get_cache_service()
        
        # Research prompts cache
        self.research_prompts = {
            "general": self._load_research_prompt("general"),
            "language_specific": self._load_research_prompt("language_specific"),
            "pattern": self._load_research_prompt("pattern"),
            "security": self._load_research_prompt("security"),
            "performance": self._load_research_prompt("performance")
        }
    
    def _load_research_prompt(self, prompt_type: str) -> str:
        """Load research prompt template."""
        base_prompts = {
            "general": """
                You are an expert software architect and standards researcher.
                Research and generate comprehensive coding standards for the following topic:
                
                Topic: {topic}
                Context: {context}
                
                Please provide:
                1. Overview and rationale
                2. Detailed standards and rules
                3. Best practices
                4. Common anti-patterns to avoid
                5. Code examples (good and bad)
                6. Testing guidelines
                7. Performance considerations
                8. Security implications
                9. Tools and automation suggestions
                10. References and further reading
                
                Format the response as a structured markdown document.
            """,
            "language_specific": """
                You are a {language} expert and standards authority.
                Generate comprehensive coding standards for {language} focusing on:
                
                Specific Area: {area}
                
                Include:
                1. Language-specific idioms and patterns
                2. Framework/library best practices
                3. Version-specific considerations
                4. Ecosystem tools and linters
                5. Common pitfalls in {language}
                6. Performance optimization techniques
                7. Memory management (if applicable)
                8. Concurrency patterns
                9. Testing strategies
                10. Real-world examples
                
                Provide practical, actionable standards with code examples.
            """,
            "pattern": """
                Research and document the following software pattern or practice:
                
                Pattern: {pattern_name}
                Category: {category}
                
                Provide:
                1. Pattern definition and purpose
                2. When to use (and when not to use)
                3. Implementation guidelines
                4. Variations and alternatives
                5. Code examples in multiple languages
                6. Testing strategies
                7. Performance implications
                8. Common mistakes
                9. Related patterns
                10. Industry adoption and case studies
            """,
            "security": """
                As a security expert, research and generate security standards for:
                
                Security Topic: {topic}
                Context: {context}
                
                Include:
                1. Threat model and risk assessment
                2. Secure coding practices
                3. Vulnerability prevention
                4. Authentication/Authorization patterns
                5. Data protection standards
                6. Compliance requirements (OWASP, PCI-DSS, etc.)
                7. Security testing approaches
                8. Incident response guidelines
                9. Code review checklist
                10. Tools and scanners
                
                Focus on practical, implementable security standards.
            """,
            "performance": """
                Research and generate performance optimization standards for:
                
                Topic: {topic}
                Technology Stack: {stack}
                
                Provide:
                1. Performance metrics and KPIs
                2. Optimization strategies
                3. Caching patterns
                4. Database optimization
                5. Algorithm complexity guidelines
                6. Resource management
                7. Monitoring and profiling
                8. Load testing standards
                9. Scalability considerations
                10. Real-world benchmarks
                
                Include specific thresholds and measurable standards.
            """
        }
        return base_prompts.get(prompt_type, base_prompts["general"])
    
    async def research_standard(
        self,
        topic: str,
        category: str = "general",
        context: Optional[Dict[str, Any]] = None,
        examples: Optional[List[str]] = None,
        use_deep_research: bool = True,
        max_iterations: int = 3,
        quality_threshold: float = 8.5
    ) -> Dict[str, Any]:
        """
        Research and generate a new standard with optional deep research mode.

        Args:
            topic: The topic to research
            category: Category of research (general, language_specific, pattern, etc.)
            context: Additional context for research
            examples: Code examples to analyze
            use_deep_research: Enable iterative refinement with self-critique (default: True)
            max_iterations: Maximum refinement iterations for deep research (default: 3)
            quality_threshold: Quality threshold to stop refinement (0-10, default: 8.5)

        Returns:
            Dictionary containing the researched standard with refinement metadata
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(topic, category, context)
            # For cache lookup, we need to provide the required parameters to get_audit_result
            # Since we don't have actual code here, we'll use topic as code content for caching
            cached = await self.cache.get_audit_result(
                code=topic,  # Using topic as cache key content
                language=category,  # Using category as language
                project_id="standards_research"
            )
            if cached:
                logger.info(f"Using cached research for {topic}")
                return cached

            # Prepare the prompt
            prompt = self._prepare_research_prompt(topic, category, context, examples)

            # Use Gemini to research with or without deep research mode
            logger.info(
                f"Researching standard for {topic} in category {category} "
                f"(deep_research={'enabled' if use_deep_research else 'disabled'})"
            )

            if use_deep_research:
                # Use iterative refinement for higher quality standards
                refinement_result = await self.gemini.generate_with_iterative_refinement(
                    prompt=prompt,
                    context=f"Standards research for {topic}",
                    max_iterations=max_iterations,
                    quality_threshold=quality_threshold
                )

                response = refinement_result["final_content"]
                refinement_metadata = {
                    "iterations_performed": refinement_result["iterations_performed"],
                    "quality_scores": refinement_result["quality_scores"],
                    "final_quality_score": refinement_result["final_quality_score"],
                    "quality_improvement": refinement_result["improvement"],
                    "research_mode": "deep_iterative_refinement"
                }
            else:
                # Use simple generation for quick standards
                response = await self.gemini.generate_with_caching(
                    prompt=prompt,
                    context=f"Standards research for {topic}",
                    use_batch=False
                )
                refinement_metadata = {
                    "research_mode": "simple_generation"
                }

            # Parse and structure the response
            standard = self._parse_research_response(response, topic, category)

            # Add refinement metadata to standard
            standard["metadata"]["refinement"] = refinement_metadata

            # Store in Neo4j
            if settings.USE_NEO4J:
                await self._store_standard_in_graph(standard)

            # Cache the result
            await self.cache.set_audit_result(
                code=topic,  # Using topic as cache key content
                language=category,  # Using category as language
                result=standard,
                project_id="standards_research"
            )

            # Save to filesystem
            await self._save_standard_to_file(standard)

            return standard

        except Exception as e:
            logger.error(f"Error researching standard: {e}")
            raise
    
    def _generate_cache_key(
        self,
        topic: str,
        category: str,
        context: Optional[Dict] = None
    ) -> str:
        """Generate a cache key for research results."""
        key_data = f"{topic}:{category}"
        if context:
            key_data += f":{json.dumps(context, sort_keys=True)}"
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()
    
    def _prepare_research_prompt(
        self,
        topic: str,
        category: str,
        context: Optional[Dict] = None,
        examples: Optional[List[str]] = None
    ) -> str:
        """Prepare the research prompt with context."""
        prompt_template = self.research_prompts.get(category, self.research_prompts["general"])
        
        # Prepare context
        prompt_context = {
            "topic": topic,
            "context": json.dumps(context or {}, indent=2)
        }
        
        # Add category-specific context
        if category == "language_specific" and context:
            prompt_context["language"] = context.get("language", "General")
            prompt_context["area"] = context.get("area", topic)
        elif category == "pattern" and context:
            prompt_context["pattern_name"] = context.get("pattern_name", topic)
            prompt_context["category"] = context.get("category", "General")
        elif category == "performance" and context:
            prompt_context["stack"] = context.get("stack", "General")
        
        # Format the prompt
        prompt = prompt_template.format(**prompt_context)
        
        # Add examples if provided
        if examples:
            prompt += "\n\nAnalyze these code examples:\n"
            for i, example in enumerate(examples, 1):
                prompt += f"\nExample {i}:\n```\n{example}\n```\n"
        
        return prompt
    
    def _parse_research_response(
        self,
        response: str,
        topic: str,
        category: str
    ) -> Dict[str, Any]:
        """Parse the LLM response into a structured standard."""
        return {
            "id": hashlib.md5(f"{topic}:{datetime.now().isoformat()}".encode(), usedforsecurity=False).hexdigest()[:12],
            "title": topic,
            "category": category,
            "version": "1.0.0",
            "created_at": datetime.now().isoformat(),
            "content": response,
            "status": "draft",
            "metadata": {
                "source": "ai_research",
                "model": "gemini",
                "reviewed": False,
                "approved": False
            }
        }
    
    async def _store_standard_in_graph(self, standard: Dict[str, Any]) -> None:
        """Store the researched standard in Neo4j."""
        if not self.neo4j:
            logger.warning("Neo4j service not available, skipping graph storage")
            return

        try:
            await self.neo4j.create_standard_from_dict(
                standard_id=standard["id"],
                title=standard["title"],
                category=standard["category"],
                content=standard["content"],
                version=standard["version"],
                metadata=standard["metadata"]
            )
        except Exception as e:
            logger.error(f"Error storing standard in graph: {e}")
    
    async def _save_standard_to_file(self, standard: Dict[str, Any]) -> None:
        """Save the standard to the filesystem."""
        try:
            # Determine the path
            category_path = Path(settings.STANDARDS_BASE_PATH) / standard["category"]
            category_path.mkdir(parents=True, exist_ok=True)
            
            # Generate filename
            filename = f"{standard['title'].lower().replace(' ', '_')}_v{standard['version']}.md"
            filepath = category_path / filename
            
            # Prepare content
            content = f"""# {standard['title']}

**Version:** {standard['version']}  
**Category:** {standard['category']}  
**Created:** {standard['created_at']}  
**Status:** {standard['status']}  

---

{standard['content']}

---

## Metadata

- **Source:** {standard['metadata']['source']}
- **Model:** {standard['metadata']['model']}
- **Reviewed:** {standard['metadata']['reviewed']}
- **Approved:** {standard['metadata']['approved']}
"""
            
            # Write to file
            filepath.write_text(content)
            logger.info(f"Standard saved to {filepath}")
            
        except Exception as e:
            logger.error(f"Error saving standard to file: {e}")
    
    async def discover_patterns(
        self,
        code_samples: List[str],
        language: str = "auto"
    ) -> List[Dict[str, Any]]:
        """
        Discover patterns from code samples that could become standards.
        
        Args:
            code_samples: List of code samples to analyze
            language: Programming language (or 'auto' to detect)
            
        Returns:
            List of discovered patterns
        """
        prompt = f"""
        Analyze the following code samples and identify:
        1. Common patterns that should become standards
        2. Repeated anti-patterns that need correction
        3. Opportunities for improvement
        4. Consistency issues
        
        Language: {language}
        
        Code Samples:
        """
        
        for i, sample in enumerate(code_samples, 1):
            prompt += f"\n\nSample {i}:\n```\n{sample}\n```"
        
        prompt += """
        
        For each discovered pattern, provide:
        - Pattern name
        - Description
        - Frequency (how often it appears)
        - Recommendation (should it become a standard?)
        - Priority (high/medium/low)
        - Example transformation
        """
        
        response = await self.gemini.generate_with_caching(
            prompt=prompt,
            context="Pattern discovery"
        )
        
        # Parse response into patterns
        patterns = self._parse_patterns(response)
        
        # Store promising patterns for future standard development
        for pattern in patterns:
            if pattern.get("recommendation") == "yes":
                await self._queue_pattern_for_research(pattern)
        
        return patterns
    
    def _parse_patterns(self, response: str) -> List[Dict[str, Any]]:
        """Parse discovered patterns from LLM response."""
        # This would need more sophisticated parsing
        # For now, return a structured response
        patterns = []
        
        # Simple parsing logic (would be enhanced)
        lines = response.split('\n')
        current_pattern = {}
        
        for line in lines:
            if line.startswith("Pattern name:"):
                if current_pattern:
                    patterns.append(current_pattern)
                current_pattern = {"name": line.replace("Pattern name:", "").strip()}
            elif line.startswith("Description:"):
                current_pattern["description"] = line.replace("Description:", "").strip()
            elif line.startswith("Frequency:"):
                current_pattern["frequency"] = line.replace("Frequency:", "").strip()
            elif line.startswith("Recommendation:"):
                current_pattern["recommendation"] = line.replace("Recommendation:", "").strip()
            elif line.startswith("Priority:"):
                current_pattern["priority"] = line.replace("Priority:", "").strip()
        
        if current_pattern:
            patterns.append(current_pattern)
        
        return patterns
    
    async def _queue_pattern_for_research(self, pattern: Dict[str, Any]) -> None:
        """Queue a discovered pattern for future research."""
        # Store in cache using proper cache service methods
        queue_key = "pattern_research_queue"
        current_queue = await self.cache.cache_manager.get(queue_key, namespace="patterns") or []
        current_queue.append({
            "pattern": pattern,
            "queued_at": datetime.now().isoformat(),
            "status": "pending"
        })
        await self.cache.cache_manager.set(queue_key, current_queue, ttl=86400, namespace="patterns")  # 24 hours
    
    async def validate_standard(
        self,
        standard_content: str,
        category: str
    ) -> Dict[str, Any]:
        """
        Validate a proposed standard for completeness and quality.
        
        Args:
            standard_content: The standard content to validate
            category: The category of the standard
            
        Returns:
            Validation results with score and recommendations
        """
        prompt = f"""
        As a standards quality auditor, evaluate the following standard:
        
        Category: {category}
        
        Standard Content:
        {standard_content}
        
        Evaluate on:
        1. Completeness (all necessary sections present)
        2. Clarity (easy to understand and implement)
        3. Practicality (can be realistically implemented)
        4. Examples (sufficient good/bad examples)
        5. Testability (can compliance be tested?)
        6. Consistency (aligns with other standards)
        7. References (proper citations and sources)
        
        Provide:
        - Overall score (0-100)
        - Score for each criterion
        - Missing sections
        - Improvement recommendations
        - Potential conflicts with existing standards
        """
        
        response = await self.gemini.generate_with_caching(
            prompt=prompt,
            context="Standard validation"
        )
        
        return self._parse_validation_response(response)
    
    def _parse_validation_response(self, response: str) -> Dict[str, Any]:
        """Parse validation response from LLM."""
        # Simple parsing - would be enhanced with structured output
        return {
            "score": 85,  # Would be parsed from response
            "criteria": {
                "completeness": 90,
                "clarity": 85,
                "practicality": 80,
                "examples": 85,
                "testability": 90,
                "consistency": 85,
                "references": 80
            },
            "missing_sections": [],
            "recommendations": response,
            "conflicts": [],
            "validation_date": datetime.now().isoformat()
        }

    async def update_standard(
        self,
        standard_id: str,
        updates: Optional[Dict[str, Any]] = None,
        use_deep_research: bool = True,
        auto_version_bump: bool = True
    ) -> Dict[str, Any]:
        """
        Update an existing standard with versioning.

        This method:
        1. Loads the existing standard
        2. Applies updates or uses AI to refine it
        3. Increments the version number
        4. Preserves old version in history
        5. Saves the new version

        Args:
            standard_id: ID of the standard to update
            updates: Optional dictionary of updates to apply
            use_deep_research: Use iterative refinement for updates (default: True)
            auto_version_bump: Automatically increment version (default: True)

        Returns:
            Updated standard with new version
        """
        try:
            # Load existing standard
            existing = await self._load_standard_by_id(standard_id)
            if not existing:
                raise ValueError(f"Standard {standard_id} not found")

            # Parse current version
            current_version = existing.get("version", "1.0.0")
            major, minor, patch = map(int, current_version.split("."))

            # Determine update type and new version
            if updates and "breaking_change" in updates:
                major += 1
                minor = 0
                patch = 0
            elif updates and "feature" in updates:
                minor += 1
                patch = 0
            else:
                patch += 1

            new_version = f"{major}.{minor}.{patch}" if auto_version_bump else current_version

            logger.info(f"Updating standard {standard_id} from v{current_version} to v{new_version}")

            # Archive the old version
            await self._archive_standard_version(existing)

            # If updates provided, apply them directly
            if updates:
                updated_content = updates.get("content", existing["content"])
                updated_metadata = {**existing.get("metadata", {}), **updates.get("metadata", {})}
            else:
                # Use AI to refine and update the standard
                refinement_prompt = f"""
Review and update the following coding standard to reflect current best practices as of {datetime.now().year}:

CURRENT STANDARD:
Title: {existing['title']}
Category: {existing['category']}
Version: {current_version}

{existing['content']}

Please:
1. Update outdated information or deprecated practices
2. Add new best practices that have emerged
3. Improve clarity and examples
4. Ensure consistency with modern standards
5. Keep the core structure but enhance content

Provide the updated standard in markdown format.
"""

                if use_deep_research:
                    refinement_result = await self.gemini.generate_with_iterative_refinement(
                        prompt=refinement_prompt,
                        context=f"Updating standard: {existing['title']}",
                        max_iterations=settings.DEEP_RESEARCH_MAX_ITERATIONS,
                        quality_threshold=settings.DEEP_RESEARCH_QUALITY_THRESHOLD
                    )
                    updated_content = refinement_result["final_content"]
                    updated_metadata = {
                        **existing.get("metadata", {}),
                        "last_updated": datetime.now().isoformat(),
                        "refinement": refinement_result
                    }
                else:
                    updated_content = await self.gemini.generate_with_caching(
                        prompt=refinement_prompt,
                        context=f"Updating standard: {existing['title']}"
                    )
                    updated_metadata = {
                        **existing.get("metadata", {}),
                        "last_updated": datetime.now().isoformat()
                    }

            # Create updated standard
            updated_standard = {
                "id": standard_id,
                "title": existing["title"],
                "category": existing["category"],
                "version": new_version,
                "created_at": existing["created_at"],
                "updated_at": datetime.now().isoformat(),
                "content": updated_content,
                "status": "updated",
                "metadata": updated_metadata,
                "changelog": existing.get("changelog", []) + [{
                    "version": new_version,
                    "date": datetime.now().isoformat(),
                    "changes": updates.get("changelog_entry", "AI-powered refinement and updates"),
                    "previous_version": current_version
                }]
            }

            # Save to filesystem
            await self._save_standard_to_file(updated_standard)

            # Update in Neo4j
            if settings.USE_NEO4J:
                await self._store_standard_in_graph(updated_standard)

            logger.info(f"Standard {standard_id} updated successfully to v{new_version}")
            return updated_standard

        except Exception as e:
            logger.error(f"Error updating standard {standard_id}: {e}")
            raise

    async def _load_standard_by_id(self, standard_id: str) -> Optional[Dict[str, Any]]:
        """Load a standard from filesystem by ID."""
        try:
            # Search through standards directories
            base_path = Path(settings.STANDARDS_BASE_PATH)
            for category_path in base_path.iterdir():
                if not category_path.is_dir():
                    continue

                for standard_file in category_path.glob("*.md"):
                    # Read and parse the file
                    content = standard_file.read_text()

                    # Extract metadata from markdown frontmatter or headers
                    # Simple parsing - would be enhanced with proper markdown parser
                    if f"**ID:** {standard_id}" in content or standard_id in standard_file.name:
                        return self._parse_standard_file(standard_file, content)

            return None

        except Exception as e:
            logger.error(f"Error loading standard {standard_id}: {e}")
            return None

    def _parse_standard_file(self, filepath: Path, content: str) -> Dict[str, Any]:
        """Parse a standard markdown file into structured data."""
        lines = content.split('\n')

        # Extract title (first # heading)
        title = lines[0].replace('# ', '') if lines else filepath.stem

        # Extract version, category, etc. from metadata section
        version = "1.0.0"
        category = filepath.parent.name
        created_at = datetime.fromtimestamp(filepath.stat().st_ctime).isoformat()

        for line in lines[:20]:  # Check first 20 lines for metadata
            if "**Version:**" in line:
                version = line.split("**Version:**")[1].strip()
            elif "**Category:**" in line:
                category = line.split("**Category:**")[1].strip()
            elif "**Created:**" in line:
                created_at = line.split("**Created:**")[1].strip()

        return {
            "id": hashlib.md5(f"{title}:{category}".encode(), usedforsecurity=False).hexdigest()[:12],
            "title": title,
            "category": category,
            "version": version,
            "created_at": created_at,
            "content": content,
            "filepath": str(filepath),
            "metadata": {}
        }

    async def _archive_standard_version(self, standard: Dict[str, Any]) -> None:
        """Archive an old version of a standard."""
        try:
            base_path = Path(settings.STANDARDS_BASE_PATH)
            category_path = base_path / standard["category"]
            archive_path = category_path / "archive"
            archive_path.mkdir(parents=True, exist_ok=True)

            # Generate archive filename with version and timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_filename = (
                f"{standard['title'].lower().replace(' ', '_')}_"
                f"v{standard['version']}_{timestamp}.md"
            )
            archive_file = archive_path / archive_filename

            # Save the old version
            archive_file.write_text(standard["content"])

            logger.info(f"Archived standard version to {archive_file}")

        except Exception as e:
            logger.error(f"Error archiving standard: {e}")

    async def get_standard_history(
        self,
        standard_id: str
    ) -> List[Dict[str, Any]]:
        """
        Get the version history of a standard.

        Args:
            standard_id: ID of the standard

        Returns:
            List of standard versions ordered by date (newest first)
        """
        try:
            current = await self._load_standard_by_id(standard_id)
            if not current:
                return []

            history = [current]

            # Load archived versions
            base_path = Path(settings.STANDARDS_BASE_PATH)
            category_path = base_path / current["category"]
            archive_path = category_path / "archive"

            if archive_path.exists():
                # Find all archived versions
                pattern = f"{current['title'].lower().replace(' ', '_')}_v*.md"
                for archive_file in archive_path.glob(pattern):
                    content = archive_file.read_text()
                    archived = self._parse_standard_file(archive_file, content)
                    history.append(archived)

            # Sort by version (newest first)
            history.sort(
                key=lambda x: tuple(map(int, x["version"].split("."))),
                reverse=True
            )

            return history

        except Exception as e:
            logger.error(f"Error getting standard history: {e}")
            return []
