#!/usr/bin/env python3
"""
Test LLM Layer

Quick test to verify LLM provider manager and prompt manager work.
"""

import asyncio
import sys

from core.llm import (
    LLMProviderManager,
    PromptManager,
    get_prompt_manager,
    LLMCache,
    get_llm_cache,
    GeminiProvider,
    AnthropicProvider,
    ProviderType,
    ModelTier,
    LLMRequest
)


def test_prompt_manager():
    """Test the prompt manager."""
    print('=' * 60)
    print('TESTING PROMPT MANAGER')
    print('=' * 60)
    print()

    # Get prompt manager
    pm = get_prompt_manager()
    print('✅ Created PromptManager instance')

    # List templates
    templates = pm.list_templates()
    print(f'✅ Found {len(templates)} built-in templates:')
    for template in templates[:5]:  # Show first 5
        print(f'   - {template["id"]}: {template["name"]}')
        print(f'     Variables: {", ".join(template["variables"])}')

    # Test template rendering
    print()
    print('Testing template rendering...')
    prompt, system = pm.render_prompt(
        'code_analysis',
        language='python',
        code='def hello(): pass'
    )
    print('✅ Template rendered successfully')
    print(f'   Prompt length: {len(prompt)} chars')
    print(f'   System prompt: {system[:50]}...' if system else '   No system prompt')

    # Test custom prompt
    print()
    print('Testing custom prompt...')
    custom_prompt, _ = pm.create_custom_prompt(
        template='Analyze this {language} code: {code}',
        language='python',
        code='x = 1'
    )
    print('✅ Custom prompt created')
    print(f'   Result: {custom_prompt}')

    print()
    print('=' * 60)
    print('✅ PROMPT MANAGER TEST SUCCESSFUL')
    print('=' * 60)
    print()


def test_llm_cache():
    """Test the LLM cache."""
    print('=' * 60)
    print('TESTING LLM CACHE')
    print('=' * 60)
    print()

    # Get cache
    cache = get_llm_cache(backend='memory', ttl_seconds=60)
    print('✅ Created LLMCache instance (memory backend)')

    # Test cache key generation
    key = cache._generate_cache_key(
        prompt='test prompt',
        model='gemini-pro',
        temperature=0.7
    )
    print(f'✅ Generated cache key: {key[:16]}...')

    # Get stats
    stats = cache.get_stats()
    print('✅ Cache statistics:')
    for key, value in stats.items():
        print(f'   {key}: {value}')

    print()
    print('=' * 60)
    print('✅ LLM CACHE TEST SUCCESSFUL')
    print('=' * 60)
    print()


def test_provider_manager():
    """Test the provider manager."""
    print('=' * 60)
    print('TESTING LLM PROVIDER MANAGER')
    print('=' * 60)
    print()

    # Create provider manager
    manager = LLMProviderManager()
    print('✅ Created LLMProviderManager instance')

    # Register providers (without API keys for testing)
    print()
    print('Note: Providers registered without API keys (for testing structure only)')
    print('      To actually use LLM features, set GEMINI_API_KEY and ANTHROPIC_API_KEY')

    # Try to register Gemini provider
    try:
        gemini = GeminiProvider(api_key=None)
        manager.register_provider(gemini)
        print('✅ Registered Gemini provider (structure only)')
    except Exception as e:
        print(f'⚠️  Gemini provider setup incomplete: {e}')

    # Try to register Anthropic provider
    try:
        anthropic = AnthropicProvider(api_key=None)
        manager.register_provider(anthropic)
        print('✅ Registered Anthropic provider (structure only)')
    except Exception as e:
        print(f'⚠️  Anthropic provider setup incomplete: {e}')

    # Get provider status
    print()
    print('Provider status:')
    status = manager.get_provider_status()
    for provider, info in status.items():
        print(f'   {provider}:')
        for key, value in info.items():
            print(f'      {key}: {value}')

    # Get available providers
    available = manager.get_available_providers()
    print()
    print(f'Available providers: {[p.value for p in available]}')

    print()
    print('=' * 60)
    print('✅ LLM PROVIDER MANAGER TEST SUCCESSFUL')
    print('=' * 60)
    print()


def test_model_tiers():
    """Test model tier system."""
    print('=' * 60)
    print('TESTING MODEL TIER SYSTEM')
    print('=' * 60)
    print()

    print('Available model tiers:')
    for tier in ModelTier:
        print(f'   - {tier.value}: {tier.name}')

    print()
    print('Model tier use cases:')
    print('   - FAST: Simple tasks, quick responses')
    print('   - BALANCED: General purpose, good balance')
    print('   - ADVANCED: Complex reasoning, highest quality')

    print()
    print('=' * 60)
    print('✅ MODEL TIER TEST SUCCESSFUL')
    print('=' * 60)
    print()


def main():
    """Run all tests."""
    try:
        test_prompt_manager()
        test_llm_cache()
        test_provider_manager()
        test_model_tiers()

        print()
        print('=' * 60)
        print('✅ ALL LLM LAYER TESTS SUCCESSFUL')
        print('=' * 60)
        print()
        print('Note: To test actual LLM generation, set environment variables:')
        print('  export GEMINI_API_KEY="your-key"')
        print('  export ANTHROPIC_API_KEY="your-key"')
        print()

        return True

    except Exception as e:
        print(f'\n❌ Test failed: {e}')
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
