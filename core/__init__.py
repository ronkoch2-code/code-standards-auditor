"""
Core Module

Core functionality for the Code Standards Auditor including:
- Audit engine for code analysis
- LLM provider abstraction and management
- Prompt management and caching
- Batch processing

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

# Audit imports
from .audit import (
    AuditEngine,
    get_audit_engine,
    AuditContext,
    AuditFinding,
    AuditSeverity,
    AuditCategory,
    FileContext,
    RuleEngine,
    CodeAnalyzer
)

# LLM imports
from .llm import (
    LLMProviderManager,
    get_llm_provider_manager,
    PromptManager,
    get_prompt_manager,
    LLMCache,
    get_llm_cache,
    BatchProcessor,
    get_batch_processor,
    LLMRequest,
    LLMResponse,
    ProviderType,
    ModelTier
)

__all__ = [
    # Audit
    "AuditEngine",
    "get_audit_engine",
    "AuditContext",
    "AuditFinding",
    "AuditSeverity",
    "AuditCategory",
    "FileContext",
    "RuleEngine",
    "CodeAnalyzer",
    # LLM
    "LLMProviderManager",
    "get_llm_provider_manager",
    "PromptManager",
    "get_prompt_manager",
    "LLMCache",
    "get_llm_cache",
    "BatchProcessor",
    "get_batch_processor",
    "LLMRequest",
    "LLMResponse",
    "ProviderType",
    "ModelTier",
    # Submodules
    "audit",
    "standards",
    "llm",
]
