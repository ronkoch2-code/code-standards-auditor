#!/bin/bash

# Create the code-standards database in Neo4j
# This script uses the Neo4j cypher-shell command line tool

echo "=========================================="
echo "Creating code-standards Database"
echo "=========================================="
echo ""

# Load password from .env
NEO4J_PASSWORD=$(grep NEO4J_PASSWORD /Volumes/FS001/pythonscripts/code-standards-auditor/.env | cut -d'=' -f2)

echo "Using password from .env file..."
echo ""

# Check if cypher-shell is available
if ! command -v cypher-shell &> /dev/null; then
    echo "❌ cypher-shell not found"
    echo ""
    echo "Alternative: Use Neo4j Browser"
    echo "1. Open http://localhost:7474"
    echo "2. Login with neo4j/$NEO4J_PASSWORD"
    echo "3. Run: :use system"
    echo "4. Run: CREATE DATABASE \`code-standards\`;"
    exit 1
fi

# Create the database
echo "Creating database..."
cypher-shell -u neo4j -p "$NEO4J_PASSWORD" -d system "CREATE DATABASE \`code-standards\`;" 2>/dev/null

if [ $? -eq 0 ]; then
    echo "✅ Successfully created code-standards database!"
else
    echo "Database might already exist or there was an error"
    echo ""
    echo "Checking existing databases..."
    cypher-shell -u neo4j -p "$NEO4J_PASSWORD" -d system "SHOW DATABASES;" 2>/dev/null
fi

echo ""
echo "=========================================="
echo "Database setup complete!"
echo "=========================================="
