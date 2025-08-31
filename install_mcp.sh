#!/bin/bash

# Enhanced setup script for Code Standards Auditor MCP Server
# This script installs all necessary dependencies with error handling

echo "================================================================"
echo "Code Standards Auditor - MCP Server Setup (Enhanced)"
echo "================================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to check if a Python package is installed
check_package() {
    python3 -c "import $1" 2>/dev/null
    return $?
}

# Function to install a package
install_package() {
    echo -e "${BLUE}Installing $1...${NC}"
    python3 -m pip install "$2" || {
        echo -e "${RED}Failed to install $1${NC}"
        return 1
    }
    echo -e "${GREEN}✓ $1 installed successfully${NC}"
    return 0
}

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Error: Python 3 is not installed${NC}"
    exit 1
fi

echo -e "${GREEN}✓ Python 3 found: $(python3 --version)${NC}"

# Check Python version (need 3.8+)
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo -e "${RED}Error: Python $REQUIRED_VERSION or higher is required (found $PYTHON_VERSION)${NC}"
    exit 1
fi

# Change to project directory
cd /Volumes/FS001/pythonscripts/code-standards-auditor || {
    echo -e "${RED}Error: Could not find project directory${NC}"
    exit 1
}

# Upgrade pip first
echo ""
echo -e "${BLUE}Upgrading pip...${NC}"
python3 -m pip install --upgrade pip

# Install critical packages first
echo ""
echo "================================================================"
echo "Installing Critical Packages"
echo "================================================================"

# 1. Install MCP package
if ! check_package "mcp"; then
    install_package "MCP (Model Context Protocol)" "mcp"
else
    echo -e "${GREEN}✓ MCP already installed${NC}"
fi

# 2. Install Google Generative AI
if ! check_package "google.generativeai"; then
    install_package "Google Generative AI" "google-generativeai"
else
    echo -e "${GREEN}✓ Google Generative AI already installed${NC}"
fi

# 3. Install Neo4j
if ! check_package "neo4j"; then
    install_package "Neo4j" "neo4j"
else
    echo -e "${GREEN}✓ Neo4j already installed${NC}"
fi

# 4. Install Redis
if ! check_package "redis"; then
    install_package "Redis" "redis hiredis"
else
    echo -e "${GREEN}✓ Redis already installed${NC}"
fi

# 5. Install Pydantic Settings
if ! check_package "pydantic_settings"; then
    install_package "Pydantic Settings" "pydantic-settings"
else
    echo -e "${GREEN}✓ Pydantic Settings already installed${NC}"
fi

# Install remaining requirements with error handling
echo ""
echo "================================================================"
echo "Installing Remaining Requirements"
echo "================================================================"

# Use the minimal MCP requirements file if full requirements fail
echo -e "${BLUE}Installing from requirements file...${NC}"
python3 -m pip install -r mcp/requirements_mcp.txt 2>/dev/null || {
    echo -e "${YELLOW}Note: Some optional packages may have failed to install${NC}"
}

# Check environment variables
echo ""
echo "================================================================"
echo "Checking Environment Variables"
echo "================================================================"

ENV_ISSUES=0

if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠ Warning: GEMINI_API_KEY is not set${NC}"
    echo "  To set it: export GEMINI_API_KEY='your_api_key'"
    ENV_ISSUES=$((ENV_ISSUES + 1))
else
    echo -e "${GREEN}✓ GEMINI_API_KEY is set${NC}"
fi

if [ -z "$NEO4J_PASSWORD" ]; then
    echo -e "${YELLOW}⚠ Warning: NEO4J_PASSWORD is not set${NC}"
    echo "  To set it: export NEO4J_PASSWORD='your_password'"
    ENV_ISSUES=$((ENV_ISSUES + 1))
else
    echo -e "${GREEN}✓ NEO4J_PASSWORD is set${NC}"
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo -e "${BLUE}ℹ Info: ANTHROPIC_API_KEY is not set (optional)${NC}"
else
    echo -e "${GREEN}✓ ANTHROPIC_API_KEY is set${NC}"
fi

# Test the MCP server
echo ""
echo "================================================================"
echo "Testing MCP Server"
echo "================================================================"

echo -e "${BLUE}Running server test...${NC}"
python3 mcp/test_server.py

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ MCP server test passed!${NC}"
else
    echo -e "${YELLOW}⚠ MCP server test had issues${NC}"
fi

# Final summary
echo ""
echo "================================================================"
echo "Setup Summary"
echo "================================================================"

if [ $ENV_ISSUES -gt 0 ]; then
    echo -e "${YELLOW}Please set the missing environment variables before running the server.${NC}"
    echo ""
fi

echo "To configure Claude Desktop:"
echo "1. Copy the MCP configuration:"
echo "   cp mcp/mcp_config.json ~/Library/Application\\ Support/Claude/claude_desktop_config.json"
echo ""
echo "2. Restart Claude Desktop"
echo ""
echo "To test the server manually:"
echo "   python3 mcp/server.py"
echo ""
echo "The server will run with limited functionality if some services are unavailable."
echo "Use the 'check_status' tool in Claude to see which services are active."
echo "================================================================"
