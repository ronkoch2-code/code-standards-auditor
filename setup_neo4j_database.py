#!/usr/bin/env python3
"""
Create the code-standards database if it doesn't exist
Then test if MCP server can connect
"""

import os
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

def setup_neo4j_for_mcp():
    print("=" * 60)
    print("Setting up Neo4j for MCP Server")
    print("=" * 60)
    print()
    
    # Load environment
    env_file = Path('/Volumes/FS001/pythonscripts/code-standards-auditor/.env')
    load_dotenv(env_file)
    
    uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD", "")
    target_db = os.getenv("NEO4J_DATABASE", "code-standards")
    
    print(f"Connecting to Neo4j...")
    print(f"  URI: {uri}")
    print(f"  User: {user}")
    print(f"  Target DB: {target_db}")
    print()
    
    try:
        driver = GraphDatabase.driver(uri, auth=(user, password))
        driver.verify_connectivity()
        print("✅ Connected to Neo4j")
        
        # Check existing databases
        with driver.session(database="system") as session:
            result = session.run("SHOW DATABASES")
            databases = {}
            for record in result:
                db_name = record["name"]
                db_status = record.get("currentStatus", "unknown")
                databases[db_name] = db_status
                
            print("\nExisting databases:")
            for db, status in databases.items():
                print(f"  • {db} (status: {status})")
            
            # Create code-standards if needed
            if target_db not in databases:
                print(f"\n⚠️  Database '{target_db}' doesn't exist")
                print(f"Creating '{target_db}' database...")
                
                try:
                    session.run(f"CREATE DATABASE `{target_db}`")
                    print(f"✅ Created '{target_db}' database!")
                    
                    # Start it
                    session.run(f"START DATABASE `{target_db}`")
                    print(f"✅ Started '{target_db}' database!")
                    
                except Exception as e:
                    print(f"❌ Could not create database: {e}")
                    print("\nFalling back to default 'neo4j' database")
                    
                    # Update .env to use neo4j database
                    with open(env_file, 'r') as f:
                        content = f.read()
                    
                    new_content = content.replace(
                        f'NEO4J_DATABASE={target_db}',
                        'NEO4J_DATABASE=neo4j'
                    )
                    
                    with open(env_file, 'w') as f:
                        f.write(new_content)
                    
                    print("✅ Updated .env to use 'neo4j' database")
                    target_db = "neo4j"
            
            else:
                print(f"\n✅ Database '{target_db}' exists")
                
                # Check if it's online
                if databases[target_db] != "online":
                    print(f"⚠️  Database is {databases[target_db]}, starting it...")
                    try:
                        session.run(f"START DATABASE `{target_db}`")
                        print(f"✅ Started '{target_db}' database!")
                    except Exception as e:
                        print(f"Could not start: {e}")
        
        # Test connection to target database
        print(f"\nTesting connection to '{target_db}' database...")
        try:
            with driver.session(database=target_db) as session:
                result = session.run("RETURN 'Connection successful!' as msg")
                msg = result.single()["msg"]
                print(f"✅ {msg}")
                
                # Clear any existing constraints that might cause issues
                print("\nChecking constraints...")
                result = session.run("SHOW CONSTRAINTS")
                constraints = list(result)
                
                if constraints:
                    print(f"Found {len(constraints)} constraints")
                    # Don't drop them, just list them
                    for c in constraints[:3]:  # Show first 3
                        print(f"  • {c.get('name', 'unnamed')}")
                
        except Exception as e:
            print(f"❌ Could not connect to '{target_db}': {e}")
        
        driver.close()
        
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Restart Claude Desktop to reload MCP server")
        print("2. Test with: 'Check the code standards auditor status'")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to connect: {e}")
        print("\nCheck:")
        print("1. Is Neo4j running? brew services list | grep neo4j")
        print("2. Is password correct? Test at http://localhost:7474")
        return False

if __name__ == "__main__":
    setup_neo4j_for_mcp()
