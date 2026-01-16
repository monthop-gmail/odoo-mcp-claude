#!/bin/bash

# Odoo MCP Server Stop Script
cd "$(dirname "$0")"

echo "Stopping Odoo MCP Server..."
docker compose down

echo "MCP server stopped"
