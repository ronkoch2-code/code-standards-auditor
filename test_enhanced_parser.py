#!/usr/bin/env python3
"""Test the enhanced parser"""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent))

from scripts.import_standards_enhanced import EnhancedStandardsParser

# Create parser
parser = EnhancedStandardsParser()

# Test with multiple files
test_files = [
    "/Volumes/FS001/pythonscripts/standards/python/coding_standards_v1.0.0.md",
    "/Volumes/FS001/pythonscripts/standards/general/data_modeling_standards_v1.0.0.md",
    "/Volumes/FS001/pythonscripts/standards/python/ai-agents/ai_agent_standards_v1.0.0.md"
]

for file_path_str in test_files:
    test_file = Path(file_path_str)

    if not test_file.exists():
        print(f"⚠️  File not found: {test_file}")
        continue

    print(f"\n{'='*70}")
    print(f"Testing: {test_file.name}")
    print('='*70)

    # Parse the file
    standards = parser.parse_file(test_file, "test")

    print(f"\n📊 Result: {len(standards)} standards extracted")

    if standards:
        print("\nFirst 5 standards:")
        for i, std in enumerate(standards[:5]):
            print(f"\n{i+1}. {std['name'][:80]}")
            print(f"   Category: {std['category']}")
            print(f"   Severity: {std['severity']}")
            print(f"   Section: {std['section']}")

    # Show category breakdown
    if standards:
        categories = {}
        for std in standards:
            cat = std['category']
            categories[cat] = categories.get(cat, 0) + 1

        print(f"\n📂 Categories:")
        for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {cat}: {count}")
