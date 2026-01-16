"""Odoo MCP Server - Main server implementation with multi-server support."""

import argparse
import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import TextContent, Tool

from .odoo_client import OdooClient

# Load environment variables
load_dotenv()

# Initialize server
server = Server("odoo-mcp")

# Client pool for multiple Odoo servers
_clients: dict[str, OdooClient] = {}
_server_configs: dict[str, dict] = {}
_default_server: str | None = None


def load_server_configs() -> None:
    """Load server configurations from JSON file or environment variables."""
    global _server_configs, _default_server

    # Try to load from JSON config file
    config_paths = [
        Path(os.getenv("ODOO_CONFIG_FILE", "")),
        Path.cwd() / "odoo_servers.json",
        Path(__file__).parent.parent.parent.parent / "odoo_servers.json",
    ]

    for config_path in config_paths:
        if config_path.is_file():
            with open(config_path) as f:
                config = json.load(f)
                _server_configs = config.get("servers", {})
                _default_server = config.get("default_server")
                return

    # Fallback to environment variables (single server, backward compatible)
    url = os.getenv("ODOO_URL")
    db = os.getenv("ODOO_DB")
    username = os.getenv("ODOO_USERNAME")
    password = os.getenv("ODOO_PASSWORD")

    if all([url, db, username, password]):
        _server_configs["default"] = {
            "url": url,
            "db": db,
            "username": username,
            "password": password,
        }
        _default_server = "default"


def get_server_names() -> list[str]:
    """Get list of configured server names."""
    if not _server_configs:
        load_server_configs()
    return list(_server_configs.keys())


def get_client(server_name: str | None = None) -> OdooClient:
    """Get or create Odoo client instance for specified server.

    Args:
        server_name: Name of server from config. None uses default server.

    Returns:
        OdooClient instance for the specified server.
    """
    global _clients

    if not _server_configs:
        load_server_configs()

    if not _server_configs:
        raise ValueError(
            "No Odoo servers configured. Please create odoo_servers.json "
            "or set ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD environment variables."
        )

    # Use default server if not specified
    if server_name is None:
        server_name = _default_server or list(_server_configs.keys())[0]

    if server_name not in _server_configs:
        available = ", ".join(_server_configs.keys())
        raise ValueError(
            f"Unknown server '{server_name}'. Available servers: {available}"
        )

    # Return cached client or create new one
    if server_name not in _clients:
        config = _server_configs[server_name]
        _clients[server_name] = OdooClient(
            url=config["url"],
            db=config["db"],
            username=config["username"],
            password=config["password"],
        )

    return _clients[server_name]


def format_result(result: Any) -> str:
    """Format result for MCP response."""
    if isinstance(result, (dict, list)):
        return json.dumps(result, indent=2, ensure_ascii=False, default=str)
    return str(result)


def _server_property() -> dict:
    """Return server property schema for tools."""
    return {
        "type": "string",
        "description": "Server name from config (optional, uses default if not specified)",
    }


@server.list_tools()
async def list_tools() -> list[Tool]:
    """List available Odoo tools."""
    return [
        Tool(
            name="odoo_list_servers",
            description="List all configured Odoo servers.",
            inputSchema={
                "type": "object",
                "properties": {},
            },
        ),
        Tool(
            name="odoo_search_read",
            description="Search and read records from an Odoo model. "
            "Returns records matching the search domain with specified fields.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name (e.g., 'res.partner', 'sale.order')",
                    },
                    "domain": {
                        "type": "array",
                        "description": "Search domain as list of conditions. "
                        "Example: [['is_company', '=', True], ['country_id.code', '=', 'TH']]",
                        "default": [],
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of field names to return. Empty for all fields.",
                    },
                    "offset": {
                        "type": "integer",
                        "description": "Number of records to skip",
                        "default": 0,
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of records to return",
                    },
                    "order": {
                        "type": "string",
                        "description": "Sort order (e.g., 'name asc, id desc')",
                    },
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="odoo_search_count",
            description="Count records matching a search domain in an Odoo model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "domain": {
                        "type": "array",
                        "description": "Search domain as list of conditions",
                        "default": [],
                    },
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="odoo_read",
            description="Read specific records by their IDs from an Odoo model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of record IDs to read",
                    },
                    "fields": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of field names to return",
                    },
                },
                "required": ["model", "ids"],
            },
        ),
        Tool(
            name="odoo_create",
            description="Create a new record in an Odoo model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "values": {
                        "type": "object",
                        "description": "Field values for the new record. "
                        "Example: {'name': 'New Partner', 'email': 'partner@example.com'}",
                    },
                },
                "required": ["model", "values"],
            },
        ),
        Tool(
            name="odoo_write",
            description="Update existing records in an Odoo model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of record IDs to update",
                    },
                    "values": {
                        "type": "object",
                        "description": "Field values to update",
                    },
                },
                "required": ["model", "ids", "values"],
            },
        ),
        Tool(
            name="odoo_delete",
            description="Delete records from an Odoo model.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "ids": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "description": "List of record IDs to delete",
                    },
                },
                "required": ["model", "ids"],
            },
        ),
        Tool(
            name="odoo_execute",
            description="Execute any method on an Odoo model. "
            "Use this for custom methods or operations not covered by other tools.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "method": {
                        "type": "string",
                        "description": "Method name to call",
                    },
                    "args": {
                        "type": "array",
                        "description": "Positional arguments for the method",
                        "default": [],
                    },
                    "kwargs": {
                        "type": "object",
                        "description": "Keyword arguments for the method",
                        "default": {},
                    },
                },
                "required": ["model", "method"],
            },
        ),
        Tool(
            name="odoo_fields_get",
            description="Get field definitions for an Odoo model. "
            "Useful for understanding model structure.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                    "model": {
                        "type": "string",
                        "description": "Odoo model name",
                    },
                    "attributes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Field attributes to return (e.g., ['string', 'type', 'required'])",
                    },
                },
                "required": ["model"],
            },
        ),
        Tool(
            name="odoo_version",
            description="Get Odoo server version information.",
            inputSchema={
                "type": "object",
                "properties": {
                    "server": _server_property(),
                },
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    try:
        # Get server name from arguments (optional)
        server_name = arguments.get("server")
        result: Any = None

        if name == "odoo_list_servers":
            if not _server_configs:
                load_server_configs()
            servers_info = {}
            for srv_name, config in _server_configs.items():
                servers_info[srv_name] = {
                    "url": config["url"],
                    "db": config["db"],
                    "is_default": srv_name == _default_server,
                }
            result = {
                "servers": servers_info,
                "default_server": _default_server,
            }

        elif name == "odoo_search_read":
            client = get_client(server_name)
            result = client.search_read(
                model=arguments["model"],
                domain=arguments.get("domain", []),
                fields=arguments.get("fields"),
                offset=arguments.get("offset", 0),
                limit=arguments.get("limit"),
                order=arguments.get("order"),
            )

        elif name == "odoo_search_count":
            client = get_client(server_name)
            result = client.search_count(
                model=arguments["model"],
                domain=arguments.get("domain", []),
            )

        elif name == "odoo_read":
            client = get_client(server_name)
            result = client.read(
                model=arguments["model"],
                ids=arguments["ids"],
                fields=arguments.get("fields"),
            )

        elif name == "odoo_create":
            client = get_client(server_name)
            record_id = client.create(
                model=arguments["model"],
                values=arguments["values"],
            )
            result = {"id": record_id, "message": f"Created record with ID {record_id}"}

        elif name == "odoo_write":
            client = get_client(server_name)
            success = client.write(
                model=arguments["model"],
                ids=arguments["ids"],
                values=arguments["values"],
            )
            result = {
                "success": success,
                "message": f"Updated {len(arguments['ids'])} record(s)",
            }

        elif name == "odoo_delete":
            client = get_client(server_name)
            success = client.unlink(
                model=arguments["model"],
                ids=arguments["ids"],
            )
            result = {
                "success": success,
                "message": f"Deleted {len(arguments['ids'])} record(s)",
            }

        elif name == "odoo_execute":
            client = get_client(server_name)
            args = arguments.get("args", [])
            kwargs = arguments.get("kwargs", {})
            result = client.execute(
                arguments["model"],
                arguments["method"],
                *args,
                **kwargs,
            )

        elif name == "odoo_fields_get":
            client = get_client(server_name)
            result = client.fields_get(
                model=arguments["model"],
                attributes=arguments.get("attributes"),
            )

        elif name == "odoo_version":
            client = get_client(server_name)
            result = client.get_version()

        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]

        return [TextContent(type="text", text=format_result(result))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def run_stdio_server():
    """Run the MCP server with stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options(),
        )


async def run_sse_server(host: str, port: int):
    """Run the MCP server with SSE transport."""
    from mcp.server.sse import SseServerTransport
    from starlette.applications import Starlette
    from starlette.routing import Mount
    from starlette.responses import Response
    import uvicorn

    sse = SseServerTransport("/messages")

    async def handle_sse(scope, receive, send):
        async with sse.connect_sse(scope, receive, send) as streams:
            await server.run(
                streams[0],
                streams[1],
                server.create_initialization_options(),
            )

    async def handle_messages(scope, receive, send):
        await sse.handle_post_message(scope, receive, send)

    from starlette.routing import Route

    async def sse_endpoint(request):
        from starlette.responses import StreamingResponse

        async def event_generator():
            # This is handled by the ASGI interface directly
            pass

        # We need to handle this at the ASGI level
        return Response("SSE endpoint - use ASGI interface", status_code=200)

    # Use raw ASGI app for SSE
    from starlette.routing import Router

    async def asgi_app(scope, receive, send):
        if scope["type"] == "http":
            path = scope["path"]
            if path == "/sse":
                await handle_sse(scope, receive, send)
            elif path == "/messages":
                await handle_messages(scope, receive, send)
            else:
                response = Response("Not Found", status_code=404)
                await response(scope, receive, send)
        else:
            response = Response("Not Found", status_code=404)
            await response(scope, receive, send)

    app = asgi_app

    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server_instance = uvicorn.Server(config)
    await server_instance.serve()


def main():
    """Main entry point."""
    import asyncio

    parser = argparse.ArgumentParser(description="Odoo MCP Server")
    parser.add_argument(
        "--sse",
        action="store_true",
        help="Run with SSE transport (HTTP) instead of stdio",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind SSE server (default: 0.0.0.0)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for SSE server (default: 8000)",
    )

    args = parser.parse_args()

    if args.sse:
        asyncio.run(run_sse_server(args.host, args.port))
    else:
        asyncio.run(run_stdio_server())


if __name__ == "__main__":
    main()
