#!/usr/bin/env python3
"""Make scripts executable"""

import os
import stat

scripts = [
    'prepare_commit.sh',
    'mcp/setup.sh'
]

for script in scripts:
    if os.path.exists(script):
        # Get current permissions
        current_perms = os.stat(script).st_mode
        # Add execute permissions for owner
        new_perms = current_perms | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
        os.chmod(script, new_perms)
        print(f"✅ Made executable: {script}")
    else:
        print(f"⚠️  File not found: {script}")

print("\nDone! Scripts are now executable.")
