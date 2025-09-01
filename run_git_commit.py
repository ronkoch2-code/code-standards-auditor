#!/usr/bin/env python3
"""
Make Git commit script executable
"""
import os
import subprocess
import sys

def main():
    script_path = "/Volumes/FS001/pythonscripts/code-standards-auditor/git_commit_research_feature.sh"
    
    # Make executable
    os.chmod(script_path, 0o755)
    print(f"✅ Made {script_path} executable")
    
    # Run the script
    print("\n🚀 Running git commit script...")
    result = subprocess.run(["/bin/bash", script_path], capture_output=True, text=True)
    
    print(result.stdout)
    if result.stderr:
        print("Errors:", result.stderr)
    
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
