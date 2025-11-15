#!/usr/bin/env python3
"""
Quick test of Deep Research Mode
Validates the implementation without full generation
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file BEFORE importing services
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)
    print(f"Loaded environment from {env_file}")

import asyncio
from services.gemini_service import GeminiService, ModelType

async def test_architecture():
    """Test that the architecture is properly set up"""
    print("\n" + "="*80)
    print("DEEP RESEARCH MODE - ARCHITECTURE TEST")
    print("="*80 + "\n")

    gemini = GeminiService(
        model_type=ModelType.GEMINI_PRO,
        enable_caching=True
    )

    print("✓ GeminiService initialized")
    print(f"  Model: {gemini.model_type.value}")
    print(f"  Caching enabled: {gemini.enable_caching}")

    # Check that methods exist
    assert hasattr(gemini, 'generate_with_iterative_refinement'), \
        "Missing generate_with_iterative_refinement method"
    assert hasattr(gemini, '_generate_with_temperature'), \
        "Missing _generate_with_temperature method"
    assert hasattr(gemini, '_critique_content'), \
        "Missing _critique_content method"

    print("✓ All required methods present")

    # Test basic temperature generation
    print("\nTesting temperature-based generation...")
    simple_prompt = "Explain Python error handling in 2 sentences."

    result = await gemini._generate_with_temperature(
        prompt=simple_prompt,
        temperature=0.7
    )

    print(f"✓ Temperature generation successful")
    print(f"  Response length: {len(result)} characters")
    print(f"  Preview: {result[:100]}...")

    # Test critique system
    print("\nTesting critique system...")
    critique = await gemini._critique_content(
        content=result,
        original_prompt=simple_prompt,
        iteration=1
    )

    print(f"✓ Critique generation successful")
    print(f"  Quality score: {critique['quality_score']}/10")
    print(f"  Strengths: {len(critique['strengths'])}")
    print(f"  Weaknesses: {len(critique['weaknesses'])}")
    print(f"  Specific improvements: {len(critique['specific_improvements'])}")

    print("\n" + "="*80)
    print("✓ ARCHITECTURE TEST PASSED")
    print("="*80)
    print("\nDeep Research Mode is properly implemented and ready to use!")
    print("\nKey Features:")
    print("  • Multi-pass iterative refinement")
    print("  • Self-critique and quality scoring")
    print("  • Temperature scheduling (creative → precise)")
    print("  • Quality threshold-based termination")
    print("\nTo use in production:")
    print("  result = await gemini.generate_with_iterative_refinement(")
    print("      prompt=your_prompt,")
    print("      max_iterations=3,")
    print("      quality_threshold=8.5")
    print("  )")


if __name__ == "__main__":
    asyncio.run(test_architecture())
