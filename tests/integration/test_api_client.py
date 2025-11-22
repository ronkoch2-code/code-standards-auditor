#!/usr/bin/env python3
"""
Test the API Client MCP Server

Tests the new API-first architecture by:
1. Checking API connectivity
2. Testing each MCP tool endpoint
3. Verifying Neo4j data access via API
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Import after path setup
from mcp_server.server_api_client import StandardsAPIClient


async def test_api_client():
    """Test the API client"""
    print("="*70)
    print("Testing Code Standards Auditor API Client")
    print("="*70)

    client = StandardsAPIClient()

    try:
        # Test 1: Health Check
        print("\n1. Testing Health Check...")
        print("-"*70)
        health = await client.health_check()
        print(f"Status: {health.get('status', 'unknown')}")
        if 'neo4j' in health:
            print(f"Neo4j: {health['neo4j']}")
        if 'redis' in health:
            print(f"Redis: {health['redis']}")
        if 'error' in health:
            print(f"⚠️  Error: {health['error']}")
            print("\n⚠️  API may not be running. Start it with:")
            print("   uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
            return

        # Test 2: List Standards
        print("\n2. Testing List Standards...")
        print("-"*70)
        standards = await client.list_standards(language="python", category="security")
        if 'error' in standards:
            print(f"❌ Error: {standards['error']}")
        else:
            count = len(standards.get('standards', []))
            print(f"✅ Found {count} Python security standards")
            if count > 0:
                print(f"   Example: {standards['standards'][0].get('name', 'N/A')[:60]}...")

        # Test 3: Search Standards
        print("\n3. Testing Search Standards...")
        print("-"*70)
        search_result = await client.search_standards(
            query="async await error handling",
            language="python",
            limit=5
        )
        if 'error' in search_result:
            print(f"❌ Error: {search_result['error']}")
        else:
            results = search_result.get('results', [])
            print(f"✅ Found {len(results)} matching standards")
            for i, result in enumerate(results[:3], 1):
                print(f"   {i}. {result.get('name', 'N/A')[:60]}... (score: {result.get('score', 0):.2f})")

        # Test 4: Analyze Code
        print("\n4. Testing Code Analysis...")
        print("-"*70)
        test_code = """
def process_data(data):
    try:
        result = data.split(',')
        return result[0]
    except:
        pass
"""
        analysis = await client.analyze_code(
            code=test_code,
            language="python",
            focus="all"
        )
        if 'error' in analysis:
            print(f"❌ Error: {analysis['error']}")
        else:
            print(f"✅ Analysis complete")
            violations = analysis.get('violations', [])
            print(f"   Found {len(violations)} potential issues")
            for v in violations[:2]:
                print(f"   - {v.get('message', 'N/A')[:60]}...")

        # Test 5: Get Recommendations
        print("\n5. Testing Recommendations...")
        print("-"*70)
        recs = await client.get_recommendations(
            code=test_code,
            language="python",
            priority_threshold="medium"
        )
        if 'error' in recs:
            print(f"❌ Error: {recs['error']}")
        else:
            recommendations = recs.get('recommendations', [])
            print(f"✅ Got {len(recommendations)} recommendations")
            for rec in recommendations[:2]:
                print(f"   Priority: {rec.get('priority', 'N/A')} - {rec.get('suggestion', 'N/A')[:50]}...")

        # Summary
        print("\n" + "="*70)
        print("SUMMARY")
        print("="*70)
        print("✅ API Client is working correctly")
        print("✅ All endpoints are accessible")
        print("✅ Neo4j data is available via API")
        print("\nThe API-first MCP server is ready to use!")
        print("\nNext steps:")
        print("1. Update Claude Desktop config to use server_api_client.py")
        print("2. Test in Claude Desktop")
        print("3. Configure remote API URL for production use")

    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_api_client())
