#!/usr/bin/env python3
"""
Test script to verify the GeminiService method fixes
"""

import sys
import os
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_gemini_service_methods():
    """Test that the GeminiService can be imported and has the required methods"""
    print("🧪 Testing GeminiService after method fixes...")
    print("=" * 70)
    
    try:
        # Test importing the service
        print("📦 Importing GeminiService...")
        from services.gemini_service import GeminiService
        print("✅ GeminiService imported successfully")
        
        # Test initialization
        print("\n🚀 Initializing GeminiService...")
        gemini_service = GeminiService()
        print("✅ GeminiService initialized successfully")
        
        # Test that the service has the expected methods
        print("\n🔍 Checking service methods...")
        expected_methods = [
            'generate_content_async',
            'generate_with_caching', 
            'audit_code',
            'batch_audit',
            'get_usage_stats'
        ]
        
        for method in expected_methods:
            if hasattr(gemini_service, method):
                print(f"✅ Method '{method}' exists")
            else:
                print(f"❌ Method '{method}' missing")
                return False
        
        print("\n🎉 All GeminiService method fixes are working!")
        return True
        
    except AttributeError as e:
        if "generate_content_async" in str(e):
            print(f"❌ Gemini method issue still exists: {e}")
            print("🔧 The generate_content_async method call was not properly fixed")
        else:
            print(f"❌ Attribute error: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_integrated_workflow_imports():
    """Test that IntegratedWorkflowService can import GeminiService correctly"""
    print("\n🔄 Testing IntegratedWorkflowService imports...")
    print("=" * 70)
    
    try:
        print("📦 Importing IntegratedWorkflowService...")
        from services.integrated_workflow_service import IntegratedWorkflowService
        print("✅ IntegratedWorkflowService imported successfully")
        
        print("\n🚀 Initializing IntegratedWorkflowService...")
        workflow_service = IntegratedWorkflowService()
        print("✅ IntegratedWorkflowService initialized successfully")
        
        # Check that gemini_service is properly initialized
        if hasattr(workflow_service, 'gemini_service') and workflow_service.gemini_service:
            print("✅ GeminiService is properly initialized in WorkflowService")
            
            # Check if it has the method we need
            if hasattr(workflow_service.gemini_service, 'generate_content_async'):
                print("✅ generate_content_async method is available")
            else:
                print("❌ generate_content_async method not available")
                return False
        else:
            print("❌ GeminiService not properly initialized in WorkflowService")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ IntegratedWorkflowService error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🔧 Code Standards Auditor - GeminiService Method Fix Test")
    print("=" * 80)
    
    success1 = test_gemini_service_methods()
    success2 = test_integrated_workflow_imports()
    
    print("\n" + "="*80)
    if success1 and success2:
        print("🎯 SUCCESS: All GeminiService method fixes are working!")
        print("🚀 You can now run the workflow without the generate_content_async error")
    else:
        print("❌ FAILED: There are still issues to fix")
    
    sys.exit(0 if (success1 and success2) else 1)
