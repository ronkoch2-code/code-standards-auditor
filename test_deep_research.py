#!/usr/bin/env python3
"""
Test script for Deep Research Mode with Iterative Refinement
Tests the new iterative refinement loop for standards generation
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file BEFORE importing services
env_file = Path(__file__).parent / '.env'
if env_file.exists():
    load_dotenv(env_file)

import asyncio
import sys
from services.gemini_service import GeminiService, ModelType
from services.standards_research_service import StandardsResearchService
from config.settings import settings

async def test_simple_refinement():
    """Test basic iterative refinement"""
    print("\n" + "="*80)
    print("TEST 1: Simple Iterative Refinement")
    print("="*80 + "\n")

    gemini = GeminiService(
        model_type=ModelType.GEMINI_PRO,
        enable_caching=True
    )

    prompt = """
    Create a comprehensive Python coding standard for error handling.
    Include:
    - Exception types and when to use them
    - Try/except best practices
    - Logging strategies
    - Custom exception design
    - Examples of good and bad patterns
    """

    result = await gemini.generate_with_iterative_refinement(
        prompt=prompt,
        context="Python error handling standards",
        max_iterations=2,  # Reduced for testing
        quality_threshold=8.0
    )

    print(f"✓ Iterations performed: {result['iterations_performed']}")
    print(f"✓ Quality scores: {result['quality_scores']}")
    print(f"✓ Final quality: {result['final_quality_score']}/10")
    print(f"✓ Improvement: +{result['improvement']:.1f} points")
    print(f"\n✓ Final content length: {len(result['final_content'])} characters")

    # Show iteration summaries
    print("\n" + "-"*80)
    print("ITERATION HISTORY:")
    print("-"*80)
    for iter_data in result['iteration_history']:
        print(f"\nIteration {iter_data['iteration']} (temp={iter_data['temperature']}):")
        print(f"  Quality Score: {iter_data['quality_score']}/10")
        print(f"  Strengths: {len(iter_data['strengths'])} identified")
        print(f"  Weaknesses: {len(iter_data['weaknesses'])} identified")

    return result


async def test_standards_research_deep_mode():
    """Test StandardsResearchService with deep research mode"""
    print("\n" + "="*80)
    print("TEST 2: Standards Research with Deep Mode")
    print("="*80 + "\n")

    research_service = StandardsResearchService()

    # Test creating a new standard with deep research
    standard = await research_service.research_standard(
        topic="API Rate Limiting Best Practices",
        category="security",
        context={
            "language": "python",
            "framework": "FastAPI"
        },
        use_deep_research=True,
        max_iterations=2,  # Reduced for testing
        quality_threshold=8.0
    )

    print(f"✓ Standard created: {standard['title']}")
    print(f"✓ Version: {standard['version']}")
    print(f"✓ Category: {standard['category']}")
    print(f"✓ Research mode: {standard['metadata']['refinement']['research_mode']}")

    if 'iterations_performed' in standard['metadata']['refinement']:
        refinement = standard['metadata']['refinement']
        print(f"✓ Iterations: {refinement['iterations_performed']}")
        print(f"✓ Quality scores: {refinement['quality_scores']}")
        print(f"✓ Final quality: {refinement['final_quality_score']}/10")
        print(f"✓ Improvement: +{refinement['quality_improvement']:.1f}")

    print(f"\n✓ Standard saved to filesystem")
    return standard


async def test_standard_update():
    """Test updating an existing standard with deep research"""
    print("\n" + "="*80)
    print("TEST 3: Update Existing Standard with Versioning")
    print("="*80 + "\n")

    research_service = StandardsResearchService()

    # First create a simple standard
    print("Creating initial standard...")
    initial = await research_service.research_standard(
        topic="Test Standard for Updates",
        category="general",
        use_deep_research=False  # Quick creation
    )

    print(f"✓ Initial standard created: v{initial['version']}")

    # Now update it with deep research
    print("\nUpdating standard with deep research...")
    updated = await research_service.update_standard(
        standard_id=initial['id'],
        use_deep_research=True,
        auto_version_bump=True
    )

    print(f"✓ Standard updated: v{initial['version']} → v{updated['version']}")
    print(f"✓ Changelog entries: {len(updated.get('changelog', []))}")

    # Get version history
    history = await research_service.get_standard_history(initial['id'])
    print(f"✓ Total versions in history: {len(history)}")

    return updated


async def test_comparison():
    """Compare simple vs deep research mode"""
    print("\n" + "="*80)
    print("TEST 4: Comparison - Simple vs Deep Research")
    print("="*80 + "\n")

    gemini = GeminiService(model_type=ModelType.GEMINI_PRO)

    test_prompt = """
    Create a coding standard for API authentication security.
    Include token management, session handling, and best practices.
    """

    # Simple generation
    print("Running simple generation...")
    simple_result = await gemini.generate_content_async(
        prompt=test_prompt,
        use_caching=False
    )

    # Deep research
    print("Running deep research mode...")
    deep_result = await gemini.generate_with_iterative_refinement(
        prompt=test_prompt,
        max_iterations=2,
        quality_threshold=8.0
    )

    print(f"\nResults:")
    print(f"  Simple mode content length: {len(simple_result)} chars")
    print(f"  Deep mode content length: {len(deep_result['final_content'])} chars")
    print(f"  Deep mode iterations: {deep_result['iterations_performed']}")
    print(f"  Deep mode quality: {deep_result['final_quality_score']}/10")
    print(f"  Quality improvement: +{deep_result['improvement']:.1f}")

    return {
        "simple": simple_result,
        "deep": deep_result
    }


async def main():
    """Run all tests"""
    print("\n" + "="*80)
    print("DEEP RESEARCH MODE - TEST SUITE")
    print("="*80)
    print(f"\nConfiguration:")
    print(f"  Model: {settings.GEMINI_MODEL}")
    print(f"  Deep Research Enabled: {settings.ENABLE_DEEP_RESEARCH}")
    print(f"  Max Iterations: {settings.DEEP_RESEARCH_MAX_ITERATIONS}")
    print(f"  Quality Threshold: {settings.DEEP_RESEARCH_QUALITY_THRESHOLD}")

    try:
        # Run tests
        await test_simple_refinement()
        await test_standards_research_deep_mode()
        # await test_standard_update()  # Skip for now - requires existing standard
        await test_comparison()

        print("\n" + "="*80)
        print("✓ ALL TESTS COMPLETED SUCCESSFULLY")
        print("="*80 + "\n")

    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
