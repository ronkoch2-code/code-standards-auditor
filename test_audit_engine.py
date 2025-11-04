#!/usr/bin/env python3
"""
Test Audit Engine

Quick test to verify the audit engine works with sample code.
"""

import asyncio
from pathlib import Path
import tempfile
import sys

from core.audit import (
    AuditEngine,
    AuditSeverity,
    AuditCategory,
    Rule,
    PatternRuleChecker
)


async def test_audit_engine():
    """Test the audit engine with sample Python code."""

    print('=' * 60)
    print('TESTING AUDIT ENGINE')
    print('=' * 60)
    print()

    # Create audit engine
    engine = AuditEngine()
    print('✅ Created AuditEngine instance')

    # Register a simple test rule
    test_rule = Rule(
        id="test_hardcoded_password",
        name="No Hardcoded Passwords",
        description="Code should not contain hardcoded passwords",
        severity=AuditSeverity.CRITICAL,
        category=AuditCategory.SECURITY,
        languages=["python"],
        patterns=[r'password\s*=\s*["\'][^"\']+["\']']
    )
    engine.rule_engine.register_rule(test_rule)
    print('✅ Registered test rule: No Hardcoded Passwords')

    # Create sample code file
    sample_code = '''def connect_to_database():
    username = "admin"
    password = "secret123"  # Bad practice!
    return connect(username, password)

def calculate_sum(a, b):
    return a + b
'''

    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(sample_code)
        temp_file = Path(f.name)

    print(f'✅ Created test file: {temp_file.name}')

    try:
        # Create audit
        audit_id = await engine.create_audit(
            files=[temp_file],
            config={'severity_threshold': 'info'}
        )
        print(f'✅ Created audit: {audit_id}')

        # Run audit
        print()
        print('Running audit...')
        context = await engine.run_audit(audit_id)

        # Display results
        print()
        print('=' * 60)
        print('AUDIT RESULTS')
        print('=' * 60)
        print()
        print(f'Status: {context.status}')
        print(f'Files analyzed: {len(context.files)}')
        print(f'Total findings: {len(context.findings)}')
        print()

        if context.findings:
            print('Findings:')
            for i, finding in enumerate(context.findings, 1):
                print(f'\n{i}. [{finding.severity.value.upper()}] {finding.message}')
                print(f'   Category: {finding.category.value}')
                if finding.file_path:
                    print(f'   File: {finding.file_path.name}')
                if finding.line_number:
                    print(f'   Line: {finding.line_number}')
                if finding.suggestion:
                    print(f'   Suggestion: {finding.suggestion}')

        # Display metrics
        print()
        print('Metrics:')
        for key, value in context.metrics.items():
            print(f'  {key}: {value}')

        # Generate report
        print()
        print('Generating markdown report...')
        report = engine.generate_report(audit_id, format='markdown')
        if report:
            print('✅ Report generated successfully')
            # Print first 500 chars of report
            content = report.get('content', '')
            if content:
                print()
                print('Report preview:')
                print('-' * 60)
                print(content[:500] + ('...' if len(content) > 500 else ''))

        print()
        print('=' * 60)
        print('✅ AUDIT ENGINE TEST SUCCESSFUL')
        print('=' * 60)

        return True

    except Exception as e:
        print(f'\n❌ Audit failed: {e}')
        import traceback
        traceback.print_exc()
        return False

    finally:
        # Cleanup
        if temp_file.exists():
            temp_file.unlink()
            print(f'\n🧹 Cleaned up test file')


if __name__ == '__main__':
    success = asyncio.run(test_audit_engine())
    sys.exit(0 if success else 1)
