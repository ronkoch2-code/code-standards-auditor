"""
LLM Provider Abstraction

Provides a unified interface for different LLM providers (Gemini, Anthropic, OpenAI, etc.)
with automatic fallback and retry logic.

Author: Code Standards Auditor
Date: November 4, 2025
Version: 1.0.0
"""

from typing import Dict, List, Optional, Any, AsyncGenerator
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum
import logging
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)


class ProviderType(str, Enum):
    """Supported LLM provider types."""
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    LOCAL = "local"


class ModelTier(str, Enum):
    """Model performance tiers."""
    FAST = "fast"  # Fast, cheap models for simple tasks
    BALANCED = "balanced"  # Balance of performance and cost
    ADVANCED = "advanced"  # Most capable models for complex tasks


@dataclass
class LLMResponse:
    """Response from an LLM provider."""
    content: str
    provider: ProviderType
    model: str
    usage: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "content": self.content,
            "provider": self.provider.value,
            "model": self.model,
            "usage": self.usage,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


@dataclass
class LLMRequest:
    """Request to an LLM provider."""
    prompt: str
    system_prompt: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: List[str] = field(default_factory=list)
    model_tier: ModelTier = ModelTier.BALANCED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert request to dictionary."""
        return {
            "prompt": self.prompt,
            "system_prompt": self.system_prompt,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "stop_sequences": self.stop_sequences,
            "model_tier": self.model_tier.value,
            "metadata": self.metadata
        }


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    Each provider implements the specific API interactions for their service.
    """

    def __init__(
        self,
        provider_type: ProviderType,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.provider_type = provider_type
        self.api_key = api_key
        self.config = config or {}
        self.available = True
        self.error_count = 0
        self.last_error: Optional[str] = None

    @abstractmethod
    async def generate(self, request: LLMRequest) -> LLMResponse:
        """
        Generate a response from the LLM.

        Args:
            request: LLM request

        Returns:
            LLM response
        """
        pass

    @abstractmethod
    async def stream_generate(
        self,
        request: LLMRequest
    ) -> AsyncGenerator[str, None]:
        """
        Stream a response from the LLM.

        Args:
            request: LLM request

        Yields:
            Response chunks
        """
        pass

    def mark_error(self, error: str) -> None:
        """Mark an error occurred with this provider."""
        self.error_count += 1
        self.last_error = error
        if self.error_count >= 3:
            self.available = False
            logger.warning(f"Provider {self.provider_type.value} marked as unavailable after {self.error_count} errors")

    def reset_errors(self) -> None:
        """Reset error count and availability."""
        self.error_count = 0
        self.last_error = None
        self.available = True

    def get_model_for_tier(self, tier: ModelTier) -> str:
        """Get the model name for a given tier."""
        models = self.config.get("models", {})
        return models.get(tier.value, self._get_default_model(tier))

    @abstractmethod
    def _get_default_model(self, tier: ModelTier) -> str:
        """Get default model for tier."""
        pass


class GeminiProvider(LLMProvider):
    """Google Gemini provider."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(ProviderType.GEMINI, api_key, config)

        try:
            import google.generativeai as genai
            if self.api_key:
                genai.configure(api_key=self.api_key)
            self.genai = genai
        except ImportError:
            logger.error("google-generativeai package not installed")
            self.available = False
        except Exception as e:
            logger.error(f"Error initializing Gemini provider: {e}")
            self.available = False

    def _get_default_model(self, tier: ModelTier) -> str:
        """Get default Gemini model for tier."""
        models = {
            ModelTier.FAST: "gemini-1.5-flash",
            ModelTier.BALANCED: "gemini-1.5-pro",
            ModelTier.ADVANCED: "gemini-1.5-pro"
        }
        return models.get(tier, "gemini-1.5-pro")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Gemini."""
        if not self.available:
            raise RuntimeError(f"Gemini provider is not available: {self.last_error}")

        try:
            model_name = self.get_model_for_tier(request.model_tier)
            model = self.genai.GenerativeModel(model_name)

            # Prepare prompt
            prompt = request.prompt
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"

            # Generate
            response = await asyncio.to_thread(
                model.generate_content,
                prompt,
                generation_config={
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens,
                    "stop_sequences": request.stop_sequences or None
                }
            )

            # Extract usage info
            usage = {}
            if hasattr(response, 'usage_metadata'):
                usage = {
                    "prompt_tokens": getattr(response.usage_metadata, 'prompt_token_count', 0),
                    "completion_tokens": getattr(response.usage_metadata, 'candidates_token_count', 0),
                    "total_tokens": getattr(response.usage_metadata, 'total_token_count', 0)
                }

            return LLMResponse(
                content=response.text,
                provider=self.provider_type,
                model=model_name,
                usage=usage,
                metadata={"finish_reason": getattr(response, 'finish_reason', None)}
            )

        except Exception as e:
            self.mark_error(str(e))
            raise

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream response using Gemini."""
        if not self.available:
            raise RuntimeError(f"Gemini provider is not available: {self.last_error}")

        try:
            model_name = self.get_model_for_tier(request.model_tier)
            model = self.genai.GenerativeModel(model_name)

            prompt = request.prompt
            if request.system_prompt:
                prompt = f"{request.system_prompt}\n\n{prompt}"

            response = model.generate_content(
                prompt,
                generation_config={
                    "temperature": request.temperature,
                    "max_output_tokens": request.max_tokens
                },
                stream=True
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            self.mark_error(str(e))
            raise


class AnthropicProvider(LLMProvider):
    """Anthropic Claude provider."""

    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        super().__init__(ProviderType.ANTHROPIC, api_key, config)

        try:
            import anthropic
            self.client = anthropic.AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            logger.error("anthropic package not installed")
            self.available = False
        except Exception as e:
            logger.error(f"Error initializing Anthropic provider: {e}")
            self.available = False

    def _get_default_model(self, tier: ModelTier) -> str:
        """Get default Anthropic model for tier."""
        models = {
            ModelTier.FAST: "claude-3-haiku-20240307",
            ModelTier.BALANCED: "claude-3-sonnet-20240229",
            ModelTier.ADVANCED: "claude-3-opus-20240229"
        }
        return models.get(tier, "claude-3-sonnet-20240229")

    async def generate(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic."""
        if not self.available:
            raise RuntimeError(f"Anthropic provider is not available: {self.last_error}")

        try:
            model_name = self.get_model_for_tier(request.model_tier)

            response = await self.client.messages.create(
                model=model_name,
                max_tokens=request.max_tokens or 4096,
                temperature=request.temperature,
                system=request.system_prompt or "",
                messages=[
                    {"role": "user", "content": request.prompt}
                ]
            )

            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens
            }

            return LLMResponse(
                content=response.content[0].text,
                provider=self.provider_type,
                model=model_name,
                usage=usage,
                metadata={"stop_reason": response.stop_reason}
            )

        except Exception as e:
            self.mark_error(str(e))
            raise

    async def stream_generate(self, request: LLMRequest) -> AsyncGenerator[str, None]:
        """Stream response using Anthropic."""
        if not self.available:
            raise RuntimeError(f"Anthropic provider is not available: {self.last_error}")

        try:
            model_name = self.get_model_for_tier(request.model_tier)

            async with self.client.messages.stream(
                model=model_name,
                max_tokens=request.max_tokens or 4096,
                temperature=request.temperature,
                system=request.system_prompt or "",
                messages=[
                    {"role": "user", "content": request.prompt}
                ]
            ) as stream:
                async for text in stream.text_stream:
                    yield text

        except Exception as e:
            self.mark_error(str(e))
            raise


class LLMProviderManager:
    """
    Manages multiple LLM providers with fallback and load balancing.
    """

    def __init__(self):
        self.providers: Dict[ProviderType, LLMProvider] = {}
        self.preferred_order: List[ProviderType] = [
            ProviderType.GEMINI,
            ProviderType.ANTHROPIC
        ]

    def register_provider(self, provider: LLMProvider) -> None:
        """Register an LLM provider."""
        self.providers[provider.provider_type] = provider
        logger.info(f"Registered LLM provider: {provider.provider_type.value}")

    def set_preferred_order(self, order: List[ProviderType]) -> None:
        """Set the preferred order of providers."""
        self.preferred_order = order

    async def generate(
        self,
        request: LLMRequest,
        preferred_provider: Optional[ProviderType] = None
    ) -> LLMResponse:
        """
        Generate response with automatic fallback.

        Args:
            request: LLM request
            preferred_provider: Preferred provider to try first

        Returns:
            LLM response

        Raises:
            RuntimeError: If all providers fail
        """
        # Build provider list
        providers_to_try = []

        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)

        for provider_type in self.preferred_order:
            if provider_type not in providers_to_try and provider_type in self.providers:
                providers_to_try.append(provider_type)

        # Try each provider
        errors = []
        for provider_type in providers_to_try:
            provider = self.providers[provider_type]

            if not provider.available:
                logger.debug(f"Skipping unavailable provider: {provider_type.value}")
                continue

            try:
                logger.debug(f"Trying provider: {provider_type.value}")
                response = await provider.generate(request)
                return response

            except Exception as e:
                error_msg = f"{provider_type.value}: {str(e)}"
                errors.append(error_msg)
                logger.warning(f"Provider {provider_type.value} failed: {e}")

        # All providers failed
        raise RuntimeError(f"All LLM providers failed: {'; '.join(errors)}")

    async def stream_generate(
        self,
        request: LLMRequest,
        preferred_provider: Optional[ProviderType] = None
    ) -> AsyncGenerator[str, None]:
        """Stream generate with automatic fallback."""
        # Similar logic to generate but for streaming
        providers_to_try = []

        if preferred_provider and preferred_provider in self.providers:
            providers_to_try.append(preferred_provider)

        for provider_type in self.preferred_order:
            if provider_type not in providers_to_try and provider_type in self.providers:
                providers_to_try.append(provider_type)

        for provider_type in providers_to_try:
            provider = self.providers[provider_type]

            if not provider.available:
                continue

            try:
                async for chunk in provider.stream_generate(request):
                    yield chunk
                return

            except Exception as e:
                logger.warning(f"Provider {provider_type.value} streaming failed: {e}")

        raise RuntimeError("All LLM providers failed for streaming")

    def get_available_providers(self) -> List[ProviderType]:
        """Get list of available providers."""
        return [
            provider_type
            for provider_type, provider in self.providers.items()
            if provider.available
        ]

    def get_provider_status(self) -> Dict[str, Any]:
        """Get status of all providers."""
        return {
            provider_type.value: {
                "available": provider.available,
                "error_count": provider.error_count,
                "last_error": provider.last_error
            }
            for provider_type, provider in self.providers.items()
        }


# Singleton instance
_manager_instance: Optional[LLMProviderManager] = None


def get_llm_provider_manager() -> LLMProviderManager:
    """Get the singleton LLM provider manager."""
    global _manager_instance
    if _manager_instance is None:
        _manager_instance = LLMProviderManager()
    return _manager_instance
