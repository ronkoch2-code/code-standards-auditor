#!/usr/bin/env python3
"""
Make commit script executable and run it
"""
import os
import stat

script_path = '/Volumes/FS001/pythonscripts/code-standards-auditor/commit_mcp_fixes.sh'

# Make executable
current_permissions = os.stat(script_path).st_mode
os.chmod(script_path, current_permissions | stat.S_IEXEC)

print("✅ Commit script made executable")
print(f"📁 Script location: {script_path}")
print("\n🚀 To commit and push the MCP fixes, run:")
print("  cd /Volumes/FS001/pythonscripts/code-standards-auditor")
print("  ./commit_mcp_fixes.sh")
