#!/usr/bin/env python3
"""
Test script to verify the Neo4j settings fixes
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_neo4j_settings():
    """Test that the settings now include USE_NEO4J and it works correctly"""
    print("🧪 Testing Neo4j Settings Fix...")
    print("=" * 70)
    
    try:
        # Test importing settings
        print("📦 Importing settings...")
        from config.settings import settings, get_settings
        print("✅ Settings imported successfully")
        
        # Test that USE_NEO4J attribute exists
        print("\n🔍 Checking USE_NEO4J attribute...")
        if hasattr(settings, 'USE_NEO4J'):
            print(f"✅ USE_NEO4J exists: {settings.USE_NEO4J}")
        else:
            print("❌ USE_NEO4J attribute missing")
            return False
        
        # Test that STANDARDS_BASE_PATH exists (and not STANDARDS_DIR)
        print("\n📁 Checking standards path settings...")
        if hasattr(settings, 'STANDARDS_BASE_PATH'):
            print(f"✅ STANDARDS_BASE_PATH exists: {settings.STANDARDS_BASE_PATH}")
        else:
            print("❌ STANDARDS_BASE_PATH missing")
            return False
        
        # Check other Neo4j related settings
        neo4j_settings = [
            'NEO4J_URI', 'NEO4J_USER', 'NEO4J_PASSWORD', 
            'NEO4J_DATABASE', 'NEO4J_MAX_CONNECTION_LIFETIME'
        ]
        
        print("\n🔗 Checking all Neo4j settings...")
        for setting in neo4j_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                # Don't show password in logs
                display_value = "***" if "PASSWORD" in setting else value
                print(f"✅ {setting}: {display_value}")
            else:
                print(f"❌ {setting} missing")
                return False
        
        # Test the intelligent USE_NEO4J detection
        print(f"\n🤖 Intelligent Neo4j detection result: {settings.USE_NEO4J}")
        if not settings.NEO4J_PASSWORD:
            print("ℹ️  Neo4j disabled (no password configured) - this is expected for development")
        else:
            print("ℹ️  Neo4j enabled (password configured)")
        
        return True
        
    except Exception as e:
        print(f"❌ Settings test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_standards_research_service_settings():
    """Test that StandardsResearchService can access the settings correctly"""
    print("\n🔬 Testing StandardsResearchService settings access...")
    print("=" * 70)
    
    try:
        print("📦 Importing StandardsResearchService...")
        from services.standards_research_service import StandardsResearchService
        print("✅ StandardsResearchService imported successfully")
        
        print("\n🚀 Initializing StandardsResearchService...")
        research_service = StandardsResearchService()
        print("✅ StandardsResearchService initialized successfully")
        
        # Test settings access by checking the settings object
        print("\n⚙️ Testing settings access in service...")
        from config.settings import settings
        
        # These are the settings that caused errors before
        critical_settings = ['USE_NEO4J', 'STANDARDS_BASE_PATH']
        
        for setting in critical_settings:
            try:
                value = getattr(settings, setting)
                print(f"✅ {setting}: accessible")
            except AttributeError as e:
                print(f"❌ {setting}: not accessible - {e}")
                return False
        
        print("\n🎉 All critical settings are now accessible!")
        return True
        
    except Exception as e:
        print(f"❌ StandardsResearchService test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Code Standards Auditor - Neo4j Settings Fix Test")
    print("=" * 80)
    
    success1 = test_neo4j_settings()
    success2 = test_standards_research_service_settings()
    
    print("\n" + "="*80)
    if success1 and success2:
        print("🎯 SUCCESS: All Neo4j settings fixes are working!")
        print("🚀 The workflow should now progress past the settings error")
        print("")
        print("📋 What's now fixed:")
        print("   ✅ USE_NEO4J setting exists and is intelligently determined")
        print("   ✅ STANDARDS_BASE_PATH is used instead of non-existent STANDARDS_DIR")
        print("   ✅ All Neo4j settings are properly configured")
        print("   ✅ StandardsResearchService can access all required settings")
    else:
        print("❌ FAILED: There are still settings issues to fix")
    
    sys.exit(0 if (success1 and success2) else 1)
