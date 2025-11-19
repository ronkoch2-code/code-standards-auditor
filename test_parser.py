#!/usr/bin/env python3
"""
Test the StandardsParser to see why it's extracting 0 standards
"""

import re
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from scripts.import_standards import StandardsParser

# Create parser
parser = StandardsParser()

# Test with a real file
test_file = Path("/Volumes/FS001/pythonscripts/standards/python/fastapi_async_standards_v1.0.0.md")

if test_file.exists():
    print(f"Testing parser with: {test_file.name}\n")

    # Parse the file
    standards = parser.parse_file(test_file, "python")

    print(f"\nResult: Extracted {len(standards)} standards")

    if standards:
        print("\nFirst few standards:")
        for i, std in enumerate(standards[:3]):
            print(f"\n{i+1}. {std['name']}")
            print(f"   Category: {std['category']}")
            print(f"   Severity: {std['severity']}")
    else:
        print("\n⚠️  NO STANDARDS EXTRACTED")
        print("\nDEBUGGING:")

        # Read content
        content = test_file.read_text()

        # Check sections
        sections = parser._split_into_sections(content)
        print(f"\nFound {len(sections)} sections:")
        for sec in sections[:3]:
            print(f"  - {sec['name']}")

        # Check for "**Standards**:" pattern
        standards_pattern = r'\*\*Standards\*\*:(.+?)(?=\n#{2,}|\n\*\*|$)'
        matches = list(re.finditer(standards_pattern, content, re.DOTALL))
        print(f"\nFound {len(matches)} '**Standards**:' sections")

        if matches:
            for i, match in enumerate(matches[:2]):
                print(f"\nMatch {i+1}:")
                matched_text = match.group(1)[:200]
                print(f"  Text: {matched_text}...")

                # Try to extract bullets
                bullets = re.findall(r'^[\-\*]\s+(.+)$', matched_text, re.MULTILINE)
                print(f"  Bullets found: {len(bullets)}")
                if bullets:
                    print(f"  First bullet: {bullets[0][:80]}...")

        # Look for any "**Standards**:" in the file
        simple_pattern = r'\*\*Standards\*\*:'
        simple_matches = list(re.finditer(simple_pattern, content))
        print(f"\nSimple search for '**Standards**:': {len(simple_matches)} matches")

        if simple_matches:
            # Show context around first match
            pos = simple_matches[0].start()
            context = content[pos:pos+300]
            print(f"\nContext around first match:")
            print(context)

else:
    print(f"File not found: {test_file}")
