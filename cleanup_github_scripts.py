#!/usr/bin/env python3
"""
Cleanup old GitHub scripts - keeping only latest versions
"""
import os
from pathlib import Path
from datetime import datetime

# Scripts to keep (latest versions)
KEEP_SCRIPTS = {
    'commit_mcp_debugging_suite.sh',  # Latest - Sept 4
    'git_commit_push.sh',  # General purpose
}

# Archive directory
ARCHIVE_DIR = Path('/Volumes/FS001/pythonscripts/code-standards-auditor/github-scripts/archive')
ARCHIVE_DIR.mkdir(exist_ok=True)

# Get all scripts in github-scripts
scripts_dir = Path('/Volumes/FS001/pythonscripts/code-standards-auditor/github-scripts')
scripts = list(scripts_dir.glob('*.sh')) + list(scripts_dir.glob('*.py'))

# Archive old scripts
archived_count = 0
for script in scripts:
    if script.name not in KEEP_SCRIPTS and script.parent == scripts_dir:
        # Create archive with timestamp
        archive_name = f"{script.stem}_{datetime.now().strftime('%Y%m%d')}{script.suffix}"
        archive_path = ARCHIVE_DIR / archive_name
        
        # Move to archive
        script.rename(archive_path)
        print(f"📦 Archived: {script.name} → archive/{archive_name}")
        archived_count += 1

print(f"\n✅ Cleanup complete!")
print(f"   Archived {archived_count} old scripts")
print(f"   Kept {len(KEEP_SCRIPTS)} current scripts")
print(f"\nCurrent scripts in github-scripts/:")
for script in KEEP_SCRIPTS:
    print(f"   - {script}")
