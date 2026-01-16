#!/bin/bash

# Odoo MCP Server Start Script
cd "$(dirname "$0")"

echo "Starting Odoo MCP Server..."

# Check if container is already running
if docker ps --format '{{.Names}}' | grep -q '^odoo-mcp-claude$'; then
    echo "MCP server is already running"
    docker ps --filter name=odoo-mcp-claude --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
else
    # Start with docker compose
    docker compose up -d

    # Wait for server to be ready
    echo "Waiting for server to start..."
    sleep 3

    # Check health (timeout 2 seconds)
    if curl -s --max-time 2 http://localhost:8000/sse >/dev/null 2>&1; then
        echo "MCP server is ready at http://localhost:8000/sse"
    else
        # Check if container is running
        if docker ps --format '{{.Names}}' | grep -q '^odoo-mcp-claude$'; then
            echo "MCP server is ready at http://localhost:8000/sse"
        else
            echo "Server failed to start, checking logs..."
            docker logs odoo-mcp-claude --tail 10
        fi
    fi
fi

echo ""
echo "Use 'docker logs -f odoo-mcp-claude' to view logs"
echo "Use './stop-mcp.sh' to stop the server"
