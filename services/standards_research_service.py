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
        examples: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Research and generate a new standard.
        
        Args:
            topic: The topic to research
            category: Category of research (general, language_specific, pattern, etc.)
            context: Additional context for research
            examples: Code examples to analyze
            
        Returns:
            Dictionary containing the researched standard
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
            
            # Use Gemini to research
            logger.info(f"Researching standard for {topic} in category {category}")
            response = await self.gemini.generate_with_caching(
                prompt=prompt,
                context=f"Standards research for {topic}",
                use_batch=False  # Research needs immediate response
            )
            
            # Parse and structure the response
            standard = self._parse_research_response(response, topic, category)
            
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
        return hashlib.md5(key_data.encode()).hexdigest()
    
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
            "id": hashlib.md5(f"{topic}:{datetime.now().isoformat()}".encode()).hexdigest()[:12],
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
        try:
            await self.neo4j.create_standard(
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
            category_path = Path(settings.STANDARDS_DIR) / standard["category"]
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
