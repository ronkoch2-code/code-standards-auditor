"""
Gemini API Service with Prompt Caching and Batch Processing
Implements cost-optimized LLM interactions for code auditing
"""

import os
import asyncio
import hashlib
import json
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

# Load .env file before configuring Gemini API
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        load_dotenv(env_path, override=True)
except ImportError:
    pass  # dotenv not available, rely on system env vars

import google.generativeai as genai
from google.generativeai import caching
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.ai.generativelanguage import Content, Part

from utils.cache_manager import CacheManager

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))


class ModelType(Enum):
    """Available Gemini models"""
    GEMINI_PRO = "gemini-2.5-pro"
    GEMINI_FLASH = "gemini-2.5-flash"
    GEMINI_PRO_002 = "gemini-2.5-pro-preview-05-06"
    GEMINI_FLASH_002 = "gemini-2.5-flash-preview-05-20"
    GEMINI_2_FLASH_THINKING = "gemini-2.0-flash-thinking-exp"  # Extended reasoning mode


@dataclass
class AuditRequest:
    """Structure for code audit requests"""
    code: str
    language: str
    project_id: Optional[str] = None
    custom_rules: Optional[List[str]] = None
    severity_threshold: str = "warning"
    use_cache: bool = True
    request_id: Optional[str] = None


@dataclass
class AuditResponse:
    """Structure for audit responses"""
    request_id: str
    score: float
    violations: List[Dict[str, Any]]
    suggestions: List[Dict[str, Any]]
    processing_time: float
    tokens_used: int
    cache_hit: bool
    model_used: str


class GeminiService:
    """
    Service for interacting with Google Gemini API
    Implements prompt caching and batch processing for cost optimization
    """
    
    def __init__(
        self,
        model_type: ModelType = ModelType.GEMINI_PRO,
        cache_ttl_minutes: int = 60,
        enable_caching: bool = True,
        batch_size: int = 10
    ):
        self.model_type = model_type
        self.cache_ttl = timedelta(minutes=cache_ttl_minutes)
        self.enable_caching = enable_caching
        self.batch_size = batch_size
        
        # Initialize cache manager
        self.cache_manager = CacheManager() if enable_caching else None
        
        # Initialize model with safety settings
        self.model = genai.GenerativeModel(
            model_name=model_type.value,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        # Cache for system prompts (prompt caching)
        self.cached_prompts = {}
        self.cached_contexts = {}
        
        # Batch processing queue
        self.batch_queue = []
        self.batch_lock = asyncio.Lock()
        
        logger.info(f"GeminiService initialized with model: {model_type.value}")
    
    def _generate_cache_key(self, content: str, prefix: str = "audit") -> str:
        """Generate a cache key for content"""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        return f"{prefix}:{content_hash}"
    
    async def _get_or_create_cached_content(
        self,
        system_instruction: str,
        context: Optional[str] = None
    ) -> Optional[Any]:
        """
        Create or retrieve cached content for prompt caching
        This leverages Gemini's context caching feature for cost optimization
        """
        if not self.enable_caching:
            return None
        
        cache_key = self._generate_cache_key(
            system_instruction + (context or ""),
            prefix="context"
        )
        
        # Check if we already have this cached
        if cache_key in self.cached_contexts:
            cached = self.cached_contexts[cache_key]
            # Check if cache is still valid
            if cached['expires_at'] > datetime.now():
                logger.info(f"Using cached context: {cache_key}")
                return cached['content']
        
        try:
            # Create new cached content using Gemini's caching API
            cache_content = caching.CachedContent.create(
                model=self.model_type.value,
                display_name=f"code_audit_{cache_key}",
                system_instruction=system_instruction,
                contents=[context] if context else [],
                ttl=self.cache_ttl
            )
            
            # Store in local cache
            self.cached_contexts[cache_key] = {
                'content': cache_content,
                'expires_at': datetime.now() + self.cache_ttl
            }
            
            logger.info(f"Created new cached context: {cache_key}")
            return cache_content
            
        except Exception as e:
            logger.error(f"Failed to create cached content: {e}")
            return None
    
    def _build_audit_prompt(
        self,
        request: AuditRequest,
        standards: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build the audit prompt for code analysis"""
        
        # Base system instruction for code auditing
        system_instruction = f"""You are an expert code auditor specializing in {request.language} development.
Your task is to analyze code for quality, standards compliance, and best practices.

Evaluate the code based on:
1. Code style and formatting standards
2. Naming conventions
3. Error handling and robustness
4. Performance considerations
5. Security vulnerabilities
6. Documentation and comments
7. Design patterns and architecture
8. Test coverage implications

Severity Levels:
- CRITICAL: Security vulnerabilities, data loss risks
- ERROR: Bugs, logic errors, standards violations
- WARNING: Poor practices, performance issues
- INFO: Suggestions for improvement

Return a structured JSON response with:
- overall_score: 0-100 quality score
- violations: array of identified issues
- suggestions: array of improvement recommendations
"""
        
        # Add custom rules if provided
        if request.custom_rules:
            rules_text = "\n".join(f"- {rule}" for rule in request.custom_rules)
            system_instruction += f"\n\nAdditional project-specific rules:\n{rules_text}"
        
        # Add standards if provided
        if standards:
            system_instruction += f"\n\nLanguage-specific standards:\n{json.dumps(standards, indent=2)}"
        
        return system_instruction
    
    async def audit_code(
        self,
        request: AuditRequest,
        standards: Optional[Dict[str, Any]] = None
    ) -> AuditResponse:
        """
        Perform a single code audit with caching
        """
        start_time = datetime.now()
        cache_hit = False
        
        # Check cache first
        if request.use_cache and self.cache_manager:
            cache_key = self._generate_cache_key(request.code)
            cached_result = await self.cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"Cache hit for request: {request.request_id}")
                cache_hit = True
                return AuditResponse(**cached_result, cache_hit=True)
        
        # Build the audit prompt
        system_instruction = self._build_audit_prompt(request, standards)
        
        # Try to use cached context for cost optimization
        cached_content = await self._get_or_create_cached_content(
            system_instruction,
            context=f"Language: {request.language}"
        )
        
        # Prepare the user prompt
        user_prompt = f"""Analyze the following {request.language} code:

```{request.language}
{request.code}
```

Provide a comprehensive audit report in JSON format with the structure:
{{
    "overall_score": <0-100>,
    "violations": [
        {{
            "line": <line_number>,
            "column": <column_number>,
            "severity": "<CRITICAL|ERROR|WARNING|INFO>",
            "rule": "<rule_name>",
            "message": "<description>",
            "suggestion": "<fix_suggestion>"
        }}
    ],
    "suggestions": [
        {{
            "category": "<category>",
            "message": "<suggestion>",
            "impact": "<HIGH|MEDIUM|LOW>"
        }}
    ],
    "summary": {{
        "strengths": ["<strength1>", "<strength2>"],
        "areas_for_improvement": ["<area1>", "<area2>"]
    }}
}}"""
        
        try:
            # Generate response using cached content if available
            if cached_content:
                model = genai.GenerativeModel.from_cached_content(cached_content)
                response = model.generate_content(user_prompt)
            else:
                response = self.model.generate_content(
                    [system_instruction, user_prompt]
                )
            
            # Parse the response
            result_text = response.text
            
            # Extract JSON from the response
            json_start = result_text.find('{')
            json_end = result_text.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = result_text[json_start:json_end]
                audit_result = json.loads(json_str)
            else:
                raise ValueError("No valid JSON found in response")
            
            # Calculate processing time
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # Create response
            audit_response = AuditResponse(
                request_id=request.request_id or self._generate_cache_key(request.code),
                score=audit_result.get('overall_score', 0),
                violations=audit_result.get('violations', []),
                suggestions=audit_result.get('suggestions', []),
                processing_time=processing_time,
                tokens_used=response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else 0,
                cache_hit=cache_hit,
                model_used=self.model_type.value
            )
            
            # Cache the result
            if request.use_cache and self.cache_manager and not cache_hit:
                cache_key = self._generate_cache_key(request.code)
                await self.cache_manager.set(cache_key, asdict(audit_response), ttl=3600)
            
            logger.info(f"Audit completed for request: {request.request_id}")
            return audit_response
            
        except Exception as e:
            logger.error(f"Audit failed for request {request.request_id}: {e}")
            raise
    
    async def batch_audit(
        self,
        requests: List[AuditRequest],
        standards: Optional[Dict[str, Any]] = None
    ) -> List[AuditResponse]:
        """
        Process multiple audit requests in batch for cost optimization
        Uses Gemini's batch API when available
        """
        logger.info(f"Starting batch audit for {len(requests)} requests")
        
        # Process in chunks based on batch_size
        results = []
        for i in range(0, len(requests), self.batch_size):
            chunk = requests[i:i + self.batch_size]
            
            # Process chunk concurrently
            chunk_tasks = [
                self.audit_code(req, standards)
                for req in chunk
            ]
            
            chunk_results = await asyncio.gather(*chunk_tasks, return_exceptions=True)
            
            # Handle results and exceptions
            for idx, result in enumerate(chunk_results):
                if isinstance(result, Exception):
                    logger.error(f"Batch item {i+idx} failed: {result}")
                    # Create error response
                    results.append(AuditResponse(
                        request_id=chunk[idx].request_id or f"batch_{i+idx}",
                        score=0,
                        violations=[],
                        suggestions=[],
                        processing_time=0,
                        tokens_used=0,
                        cache_hit=False,
                        model_used=self.model_type.value
                    ))
                else:
                    results.append(result)
        
        logger.info(f"Batch audit completed: {len(results)} processed")
        return results
    
    async def generate_content_async(
        self,
        prompt: str,
        context: Optional[str] = None,
        use_caching: bool = True
    ) -> str:
        """
        Generate content using Gemini with optional caching.
        
        Args:
            prompt: The prompt to send to Gemini
            context: Optional context for the prompt
            use_caching: Whether to use prompt caching for cost optimization
            
        Returns:
            Generated text content
        """
        try:
            # Build the full prompt
            if context:
                full_prompt = f"Context: {context}\n\nRequest: {prompt}"
            else:
                full_prompt = prompt
            
            # Check cache first if enabled
            cache_key = None
            if use_caching and self.cache_manager:
                cache_key = self._generate_cache_key(full_prompt, prefix="content")
                cached_result = await self.cache_manager.get(cache_key, namespace="content")
                if cached_result:
                    logger.info(f"Using cached content generation for prompt hash: {cache_key[:8]}")
                    return cached_result
            
            # Generate content
            response = self.model.generate_content(full_prompt)
            result_text = response.text
            
            # Cache the result if caching is enabled
            if use_caching and self.cache_manager and cache_key:
                await self.cache_manager.set(cache_key, result_text, ttl=3600, namespace="content")
                logger.info(f"Cached content generation result: {cache_key[:8]}")
            
            return result_text
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
    
    async def generate_with_caching(
        self,
        prompt: str,
        context: Optional[str] = None,
        use_batch: bool = False
    ) -> str:
        """
        Backward compatibility method for generate_with_caching calls.
        This method was referenced in other services.
        """
        return await self.generate_content_async(
            prompt=prompt,
            context=context,
            use_caching=True
        )
    async def generate_content_async(
        self,
        prompt: str,
        context: Optional[str] = None,
        use_caching: bool = True
    ) -> str:
        """
        Generate content using Gemini with optional caching.
        
        Args:
            prompt: The prompt to send to Gemini
            context: Optional context for the prompt
            use_caching: Whether to use prompt caching for cost optimization
            
        Returns:
            Generated text content
        """
        try:
            # Build the full prompt
            if context:
                full_prompt = f"Context: {context}\n\nRequest: {prompt}"
            else:
                full_prompt = prompt
            
            # Check cache first if enabled
            cache_key = None
            if use_caching and self.cache_manager:
                cache_key = self._generate_cache_key(full_prompt, prefix="content")
                cached_result = await self.cache_manager.get(cache_key, namespace="content")
                if cached_result:
                    logger.info(f"Using cached content generation for prompt hash: {cache_key[:8]}")
                    return cached_result
            
            # Generate content
            response = await self.model.generate_content_async(full_prompt)
            result_text = response.text
            
            # Cache the result if caching is enabled
            if use_caching and self.cache_manager and cache_key:
                await self.cache_manager.set(cache_key, result_text, ttl=3600, namespace="content")
                logger.info(f"Cached content generation result: {cache_key[:8]}")
            
            return result_text
            
        except Exception as e:
            logger.error(f"Content generation failed: {e}")
            raise
    
    async def generate_with_caching(
        self,
        prompt: str,
        context: Optional[str] = None,
        use_batch: bool = False
    ) -> str:
        """
        Backward compatibility method for generate_with_caching calls.
        This method was referenced in other services.
        """
        return await self.generate_content_async(
            prompt=prompt,
            context=context,
            use_caching=True
        )
    
    async def generate_with_iterative_refinement(
        self,
        prompt: str,
        context: Optional[str] = None,
        max_iterations: int = 3,
        quality_threshold: float = 8.5,
        temperature_schedule: Optional[List[float]] = None
    ) -> Dict[str, Any]:
        """
        Generate content with iterative refinement and self-critique.

        This implements a multi-pass approach:
        1. Initial generation (higher temperature for creativity)
        2. Self-critique to identify gaps and weaknesses
        3. Refinement based on critique
        4. Repeat until quality threshold met or max iterations reached

        Args:
            prompt: The initial prompt
            context: Optional context for the generation
            max_iterations: Maximum refinement iterations (default: 3)
            quality_threshold: Quality score to stop refinement (0-10 scale, default: 8.5)
            temperature_schedule: Custom temperature for each iteration

        Returns:
            Dictionary containing:
            - final_content: The refined content
            - iterations: Number of iterations performed
            - quality_scores: Quality score from each iteration
            - critique_history: All critiques generated
        """
        if temperature_schedule is None:
            # Default schedule: start creative, end precise
            temperature_schedule = [0.8, 0.6, 0.4][:max_iterations]

        iteration_results = []
        current_content = None

        logger.info(f"Starting iterative refinement (max {max_iterations} iterations)")

        for iteration in range(max_iterations):
            temp = temperature_schedule[iteration] if iteration < len(temperature_schedule) else 0.4

            # Step 1: Generate or refine content
            if iteration == 0:
                # Initial generation
                generation_prompt = prompt
                if context:
                    generation_prompt = f"Context: {context}\n\n{prompt}"

                logger.info(f"Iteration {iteration + 1}: Initial generation (temp={temp})")
            else:
                # Refinement based on previous critique
                previous_critique = iteration_results[-1]["critique"]
                generation_prompt = f"""
Based on the following critique, refine and improve the content:

CRITIQUE:
{previous_critique}

CURRENT CONTENT:
{current_content}

ORIGINAL REQUEST:
{prompt}

Please provide an improved version that addresses all the points raised in the critique.
Make substantial improvements while maintaining the core structure and intent.
"""
                logger.info(f"Iteration {iteration + 1}: Refinement based on critique (temp={temp})")

            # Generate content with appropriate temperature
            current_content = await self._generate_with_temperature(
                generation_prompt,
                temperature=temp
            )

            # Step 2: Self-critique the generated content
            critique_result = await self._critique_content(
                content=current_content,
                original_prompt=prompt,
                iteration=iteration + 1
            )

            # Store iteration results
            iteration_results.append({
                "iteration": iteration + 1,
                "content": current_content,
                "critique": critique_result["critique"],
                "quality_score": critique_result["quality_score"],
                "strengths": critique_result["strengths"],
                "weaknesses": critique_result["weaknesses"],
                "temperature": temp
            })

            logger.info(
                f"Iteration {iteration + 1} complete: "
                f"Quality Score = {critique_result['quality_score']}/10"
            )

            # Step 3: Check if quality threshold met
            if critique_result["quality_score"] >= quality_threshold:
                logger.info(
                    f"Quality threshold met ({critique_result['quality_score']} >= {quality_threshold}). "
                    f"Stopping after {iteration + 1} iterations."
                )
                break

        # Compile final results
        final_result = {
            "final_content": current_content,
            "iterations_performed": len(iteration_results),
            "quality_scores": [r["quality_score"] for r in iteration_results],
            "iteration_history": iteration_results,
            "final_quality_score": iteration_results[-1]["quality_score"],
            "improvement": iteration_results[-1]["quality_score"] - iteration_results[0]["quality_score"]
        }

        logger.info(
            f"Refinement complete: {len(iteration_results)} iterations, "
            f"Quality improved from {iteration_results[0]['quality_score']} to "
            f"{iteration_results[-1]['quality_score']} (+{final_result['improvement']:.1f})"
        )

        return final_result

    async def _generate_with_temperature(
        self,
        prompt: str,
        temperature: float = 0.7
    ) -> str:
        """
        Generate content with a specific temperature setting.

        Args:
            prompt: The prompt to generate from
            temperature: Temperature setting (0.0-1.0)

        Returns:
            Generated content as string
        """
        try:
            # Create a temporary model with the specified temperature
            temp_model = genai.GenerativeModel(
                model_name=self.model_type.value,
                safety_settings={
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                },
                generation_config={
                    "temperature": temperature,
                    "top_p": 0.95,
                    "top_k": 40,
                    "max_output_tokens": self.model._generation_config.get("max_output_tokens", 8192) if hasattr(self.model, "_generation_config") else 8192
                }
            )

            response = await temp_model.generate_content_async(prompt)
            return response.text

        except Exception as e:
            logger.error(f"Content generation with temperature {temperature} failed: {e}")
            raise

    async def _critique_content(
        self,
        content: str,
        original_prompt: str,
        iteration: int
    ) -> Dict[str, Any]:
        """
        Generate a detailed critique of the content.

        This uses a separate model call to act as a critic, evaluating:
        - Completeness relative to the original prompt
        - Quality and depth of information
        - Structure and organization
        - Clarity and readability
        - Technical accuracy
        - Practical applicability

        Args:
            content: The content to critique
            original_prompt: The original prompt/request
            iteration: Current iteration number

        Returns:
            Dictionary with critique, quality score, strengths, and weaknesses
        """
        critique_prompt = f"""
You are an expert technical reviewer and standards quality auditor.
Your role is to provide a thorough, constructive critique of the following content.

ORIGINAL REQUEST:
{original_prompt}

GENERATED CONTENT (Iteration {iteration}):
{content}

Please evaluate this content on the following criteria (score each 0-10):

1. **Completeness**: Does it fully address all aspects of the original request?
2. **Depth**: Is the information detailed and comprehensive enough?
3. **Structure**: Is it well-organized and easy to navigate?
4. **Clarity**: Is the writing clear, concise, and understandable?
5. **Technical Accuracy**: Is the technical information correct and up-to-date?
6. **Practical Applicability**: Can this be practically implemented/used?
7. **Examples**: Are there sufficient, high-quality examples?
8. **Best Practices**: Does it reflect current industry best practices?

Provide your response in the following JSON format:
{{
    "overall_quality_score": <0-10>,
    "criteria_scores": {{
        "completeness": <0-10>,
        "depth": <0-10>,
        "structure": <0-10>,
        "clarity": <0-10>,
        "technical_accuracy": <0-10>,
        "practical_applicability": <0-10>,
        "examples": <0-10>,
        "best_practices": <0-10>
    }},
    "strengths": [
        "Strength 1",
        "Strength 2",
        "Strength 3"
    ],
    "weaknesses": [
        "Weakness 1",
        "Weakness 2",
        "Weakness 3"
    ],
    "specific_improvements": [
        "Specific improvement 1 with exact location/section",
        "Specific improvement 2 with exact location/section",
        "Specific improvement 3 with exact location/section"
    ],
    "missing_sections": [
        "Missing section 1",
        "Missing section 2"
    ],
    "critique_summary": "Overall assessment and key recommendations in 2-3 sentences"
}}

Be thorough and constructive. Identify both what works well and what needs improvement.
"""

        try:
            # Use lower temperature for consistent critique
            critique_response = await self._generate_with_temperature(
                critique_prompt,
                temperature=0.3
            )

            # Parse JSON response
            json_start = critique_response.find('{')
            json_end = critique_response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                critique_json = json.loads(critique_response[json_start:json_end])
            else:
                raise ValueError("No valid JSON found in critique response")

            # Build comprehensive critique text
            critique_text = f"""
ITERATION {iteration} CRITIQUE

Overall Quality Score: {critique_json['overall_quality_score']}/10

CRITERIA SCORES:
{json.dumps(critique_json['criteria_scores'], indent=2)}

STRENGTHS:
{chr(10).join(f"✓ {s}" for s in critique_json['strengths'])}

WEAKNESSES:
{chr(10).join(f"✗ {w}" for w in critique_json['weaknesses'])}

SPECIFIC IMPROVEMENTS NEEDED:
{chr(10).join(f"→ {i}" for i in critique_json['specific_improvements'])}

MISSING SECTIONS:
{chr(10).join(f"• {m}" for m in critique_json.get('missing_sections', []))}

SUMMARY:
{critique_json['critique_summary']}
"""

            return {
                "critique": critique_text,
                "quality_score": critique_json['overall_quality_score'],
                "criteria_scores": critique_json['criteria_scores'],
                "strengths": critique_json['strengths'],
                "weaknesses": critique_json['weaknesses'],
                "specific_improvements": critique_json['specific_improvements'],
                "missing_sections": critique_json.get('missing_sections', []),
                "summary": critique_json['critique_summary']
            }

        except Exception as e:
            logger.error(f"Content critique failed: {e}")
            # Return a default critique if parsing fails
            return {
                "critique": f"Critique generation failed: {e}",
                "quality_score": 5.0,
                "criteria_scores": {},
                "strengths": [],
                "weaknesses": ["Critique could not be generated"],
                "specific_improvements": [],
                "missing_sections": [],
                "summary": "Unable to generate critique due to parsing error"
            }

    async def get_usage_stats(self) -> Dict[str, Any]:
        """Get usage statistics for monitoring and optimization"""
        stats = {
            "model": self.model_type.value,
            "caching_enabled": self.enable_caching,
            "cached_contexts": len(self.cached_contexts),
            "batch_queue_size": len(self.batch_queue)
        }

        if self.cache_manager:
            cache_stats = await self.cache_manager.get_stats()
            stats.update(cache_stats)

        return stats

    async def clear_cache(self):
        """Clear all caches"""
        self.cached_contexts.clear()
        self.cached_prompts.clear()
        if self.cache_manager:
            await self.cache_manager.clear()
        logger.info("All caches cleared")
