"""
Core LLM Module

Provides LLM provider abstraction, prompt management, caching,
and batch processing capabilities.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from .provider import (
    ProviderType,
    ModelTier,
    LLMRequest,
    LLMResponse,
    LLMProvider,
    GeminiProvider,
    AnthropicProvider,
    LLMProviderManager,
    get_llm_provider_manager
)
from .prompt_manager import (
    PromptTemplate,
    PromptManager,
    get_prompt_manager
)
from .cache_decorator import (
    LLMCache,
    get_llm_cache,
    cached_llm_call,
    CacheStats,
    get_cache_stats
)
from .batch_processor import (
    BatchStatus,
    BatchItem,
    BatchJob,
    BatchProcessor,
    get_batch_processor
)

__all__ = [
    # Provider
    "ProviderType",
    "ModelTier",
    "LLMRequest",
    "LLMResponse",
    "LLMProvider",
    "GeminiProvider",
    "AnthropicProvider",
    "LLMProviderManager",
    "get_llm_provider_manager",
    # Prompt Manager
    "PromptTemplate",
    "PromptManager",
    "get_prompt_manager",
    # Cache
    "LLMCache",
    "get_llm_cache",
    "cached_llm_call",
    "CacheStats",
    "get_cache_stats",
    # Batch Processor
    "BatchStatus",
    "BatchItem",
    "BatchJob",
    "BatchProcessor",
    "get_batch_processor"
]
