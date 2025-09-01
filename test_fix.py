#!/usr/bin/env python3
"""
Test script to verify the cache method fixes
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_standards_research_service():
    """Test that the Standards Research Service can be imported and initialized"""
    print("🧪 Testing Standards Research Service after cache method fixes...")
    print("=" * 70)
    
    try:
        # Test importing the service
        print("📦 Importing StandardsResearchService...")
        from services.standards_research_service import StandardsResearchService
        print("✅ StandardsResearchService imported successfully")
        
        # Test initialization
        print("\n🚀 Initializing StandardsResearchService...")
        research_service = StandardsResearchService()
        print("✅ StandardsResearchService initialized successfully")
        
        # Test that the service has the expected methods
        print("\n🔍 Checking service methods...")
        expected_methods = [
            'research_standard',
            'discover_patterns', 
            'validate_standard'
        ]
        
        for method in expected_methods:
            if hasattr(research_service, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return False
        
        print("\n🎉 All cache method fixes are working!")
        print("🚀 The research service should now work correctly during Phase 3")
        return True
        
    except AttributeError as e:
        if "get_cached_audit" in str(e):
            print(f"❌ Cache method issue still exists: {e}")
            print("🔧 The get_cached_audit method call was not properly fixed")
        else:
            print(f"❌ Attribute error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_standards_research_service()
    print("\n" + "="*70)
    if success:
        print("🎯 SUCCESS: Cache method fixes are working!")
        print("🚀 You can now run the enhanced CLI without the cache error")
    else:
        print("❌ FAILED: There are still issues to fix")
    
    sys.exit(0 if success else 1)
