"""
Directly Update Old Standards Using Deep Research

This script regenerates the 3 oldest standards using deep research mode.

Author: Code Standards Auditor
Date: November 16, 2025
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from services.gemini_service import GeminiService
from config.settings import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def regenerate_standard(gemini: GeminiService, filepath: Path, language: str):
    """
    Regenerate a standard file using deep research.

    Args:
        gemini: GeminiService instance
        filepath: Path to standard file
        language: Programming language
    """
    logger.info(f"\n{'='*80}")
    logger.info(f"Regenerating: {filepath.name}")
    logger.info(f"Language: {language}")
    logger.info(f"{'='*80}")

    # Read current content to understand the topic
    current_content = filepath.read_text()
    title = current_content.split('\n')[0].replace('# ', '') if current_content else f"{language.title()} Coding Standards"

    logger.info(f"Current title: {title}")
    logger.info(f"Current size: {len(current_content)} characters")

    # Create prompt for regeneration
    prompt = f"""You are an expert software architect and standards authority for {language}.

Please create comprehensive, up-to-date coding standards for {language} as of November 2025.

Title: {title}

The standards should include:

1. **Overview and Rationale**
   - Why these standards matter
   - Benefits of following them
   - Modern {language} best practices (2025)

2. **Code Structure and Organization**
   - Project structure
   - File and directory naming
   - Module organization

3. **Naming Conventions**
   - Variables, functions, classes
   - Constants and configuration
   - Files and packages

4. **Code Style**
   - Formatting guidelines
   - Indentation and spacing
   - Line length and wrapping
   - Comments and documentation

5. **Best Practices**
   - Error handling
   - Logging
   - Testing
   - Security considerations
   - Performance optimization

6. **Common Anti-Patterns to Avoid**
   - Bad practices with explanations
   - Why they're problematic
   - Better alternatives

7. **Code Examples**
   - Good examples demonstrating best practices
   - Bad examples showing anti-patterns
   - Side-by-side comparisons

8. **Tools and Automation**
   - Linters and formatters
   - Static analysis tools
   - IDE setup recommendations

9. **Version-Specific Considerations**
   - Latest language version features
   - Deprecated patterns to avoid
   - Migration guidelines

10. **References and Resources**
    - Official documentation
    - Community standards
    - Recommended reading

Format the response as a comprehensive markdown document with clear headings, code blocks, and examples.

Include metadata at the top:
- **Version:** 2.0.0
- **Last Updated:** {datetime.now().strftime('%Y-%m-%d')}
- **Category:** {language}
- **Status:** Active

Make this a production-ready, enterprise-grade standard that developers can rely on.
"""

    try:
        logger.info("Starting deep research generation...")
        start_time = datetime.now()

        # Generate with deep research mode
        result = await gemini.generate_with_iterative_refinement(
            prompt=prompt,
            context=f"Regenerating {language} coding standards",
            max_iterations=settings.DEEP_RESEARCH_MAX_ITERATIONS,
            quality_threshold=settings.DEEP_RESEARCH_QUALITY_THRESHOLD
        )

        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        logger.info(f"\n✅ Generation completed in {duration:.2f} seconds")
        logger.info(f"Iterations: {result['iterations_performed']}")
        logger.info(f"Final quality score: {result['final_quality_score']:.2f}/10")
        logger.info(f"Generated {len(result['final_content'])} characters")

        # Backup old file
        backup_path = filepath.with_suffix('.md.backup')
        filepath.rename(backup_path)
        logger.info(f"Backed up old version to: {backup_path.name}")

        # Write new content
        filepath.write_text(result['final_content'])
        logger.info(f"✅ Wrote new version to: {filepath.name}")

        # Update modification time
        filepath.touch()

        return {
            'success': True,
            'filepath': str(filepath),
            'quality_score': result['final_quality_score'],
            'iterations': result['iterations_performed'],
            'duration': duration,
            'old_size': len(current_content),
            'new_size': len(result['final_content'])
        }

    except Exception as e:
        logger.error(f"❌ Failed to regenerate {filepath.name}: {e}")
        logger.exception(e)
        return {
            'success': False,
            'filepath': str(filepath),
            'error': str(e)
        }


async def main():
    """Main function"""

    logger.info("\n" + "="*80)
    logger.info("REGENERATING 3 OLDEST STANDARDS WITH DEEP RESEARCH")
    logger.info("="*80)
    logger.info(f"Deep Research Settings:")
    logger.info(f"  - Max Iterations: {settings.DEEP_RESEARCH_MAX_ITERATIONS}")
    logger.info(f"  - Quality Threshold: {settings.DEEP_RESEARCH_QUALITY_THRESHOLD}")
    logger.info(f"  - Temperature Schedule: {settings.DEEP_RESEARCH_TEMPERATURE_SCHEDULE}")
    logger.info("="*80 + "\n")

    # Standards to regenerate
    standards = [
        (Path(settings.STANDARDS_BASE_PATH) / "python/coding_standards_v1.0.0.md", "Python"),
        (Path(settings.STANDARDS_BASE_PATH) / "java/coding_standards_v1.0.0.md", "Java"),
        (Path(settings.STANDARDS_BASE_PATH) / "general/coding_standards_v1.0.0.md", "General")
    ]

    # Initialize Gemini service
    gemini = GeminiService()

    # Regenerate each standard
    results = []
    for filepath, language in standards:
        if not filepath.exists():
            logger.error(f"❌ File not found: {filepath}")
            continue

        result = await regenerate_standard(gemini, filepath, language)
        results.append(result)

        # Small delay between updates
        if filepath != standards[-1][0]:
            logger.info("\nWaiting 10 seconds before next update...")
            await asyncio.sleep(10)

    # Summary
    logger.info("\n" + "="*80)
    logger.info("REGENERATION SUMMARY")
    logger.info("="*80)

    successful = [r for r in results if r.get('success')]
    failed = [r for r in results if not r.get('success')]

    logger.info(f"\nTotal: {len(results)}")
    logger.info(f"Successful: {len(successful)}")
    logger.info(f"Failed: {len(failed)}")

    if successful:
        logger.info("\n✅ Successful regenerations:")
        for r in successful:
            logger.info(f"  - {Path(r['filepath']).name}")
            logger.info(f"    Quality: {r['quality_score']:.2f}/10")
            logger.info(f"    Iterations: {r['iterations']}")
            logger.info(f"    Duration: {r['duration']:.2f}s")
            logger.info(f"    Size: {r['old_size']} → {r['new_size']} chars")

    if failed:
        logger.info("\n❌ Failed:")
        for r in failed:
            logger.info(f"  - {Path(r['filepath']).name}: {r.get('error')}")

    logger.info("\n" + "="*80)

    return len(successful) == len(results)


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
