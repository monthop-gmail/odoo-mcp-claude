# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Odoo MCP Server - A Python bridge that exposes Odoo ERP operations to AI agents via the Model Context Protocol (MCP). Enables Claude Code to interact with Odoo databases through standardized tools.

## Development Commands

```bash
# Start the server (Docker, recommended)
./start-mcp.sh

# Stop the server
./stop-mcp.sh

# View logs
docker logs -f odoo-mcp

# Rebuild from scratch
docker compose down && docker compose build --no-cache && docker compose up -d

# Local development (STDIO mode)
pip install -e .
python -m odoo_mcp.server

# Run with SSE transport
python -m odoo_mcp.server --sse --host 0.0.0.0 --port 8000
```

## Architecture

The codebase consists of two main components in `src/odoo_mcp/`:

**OdooClient** (`odoo_client.py`) - Low-level XML-RPC wrapper:
- Manages connections to Odoo's `/xmlrpc/2/common` and `/xmlrpc/2/object` endpoints
- Provides lazy authentication (authenticates on first use)
- Exposes CRUD operations: `search()`, `read()`, `search_read()`, `create()`, `write()`, `unlink()`
- Schema introspection via `fields_get()`

**MCP Server** (`server.py`) - High-level tool registry:
- Async server using MCP protocol v1.0.0+
- Two transport modes: STDIO (local) and SSE/HTTP (Docker)
- Registers 10 tools: `odoo_search_read`, `odoo_search_count`, `odoo_read`, `odoo_create`, `odoo_write`, `odoo_delete`, `odoo_execute`, `odoo_fields_get`, `odoo_version`, `odoo_list_servers`
- Tools defined in `list_tools()` decorator, implementations in `call_tool()` dispatcher

## Configuration

### Multi-Server Configuration (Recommended)

Create `odoo_servers.json` in the project root:

```json
{
  "servers": {
    "production": {
      "url": "https://prod.example.com",
      "db": "prod_db",
      "username": "admin",
      "password": "api_key_here"
    },
    "staging": {
      "url": "https://staging.example.com",
      "db": "staging_db",
      "username": "admin",
      "password": "api_key_here"
    }
  },
  "default_server": "production"
}
```

Use the `server` parameter in tool calls to specify which server:
```python
# Uses default server
odoo_search_read(model="res.partner", limit=10)

# Uses specific server
odoo_search_read(model="res.partner", limit=10, server="staging")
```

Use `odoo_list_servers` tool to see all configured servers.

### Single Server (Environment Variables)

Fallback for backward compatibility:
- `ODOO_URL` - Odoo instance URL
- `ODOO_DB` - Database name
- `ODOO_USERNAME` - User login
- `ODOO_PASSWORD` - Password or API key (API key recommended)

MCP client configuration in `.mcp.json` defines the SSE endpoint connection.

## Odoo Concepts

- **Models**: Database tables (e.g., `res.partner`, `sale.order`, `product.product`)
- **Domain**: Filter syntax `[["field", "operator", "value"]]` (e.g., `[["is_company", "=", true]]`)
- **Fields**: List of column names to return
- **execute()**: Calls any model method (e.g., `action_confirm` on `sale.order`)

## Adding New Features

To add a new MCP tool:
1. Add tool definition to `list_tools()` in `server.py` (name, description, inputSchema)
2. Add handler case to `call_tool()` dispatcher
3. If needed, add supporting method to `OdooClient` class
