# Odoo MCP Server

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![MCP](https://img.shields.io/badge/MCP-1.0.0-green.svg)](https://modelcontextprotocol.io/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Python bridge that exposes Odoo ERP operations to AI agents via the **Model Context Protocol (MCP)**. Enables Claude Code and other MCP-compatible AI tools to interact with Odoo databases through standardized tools.

## Features

- **CRUD Operations** - Create, Read, Update, Delete records on any Odoo model
- **Search & Filter** - Query data using Odoo's powerful domain filter syntax
- **Execute Methods** - Call any method on Odoo models (e.g., `action_confirm` on `sale.order`)
- **Schema Introspection** - Get field definitions and model structure
- **Multi-Server Support** - Connect to multiple Odoo instances from a single server
- **Dual Transport** - Supports both STDIO (local) and SSE/HTTP (Docker) modes

## Table of Contents

- [Quick Start](#quick-start)
- [Installation](#installation)
  - [Docker (Recommended)](#docker-recommended)
  - [Local Installation](#local-installation)
- [Configuration](#configuration)
  - [Single Server (Environment Variables)](#single-server-environment-variables)
  - [Multi-Server Configuration](#multi-server-configuration)
- [Usage with Claude Code](#usage-with-claude-code)
- [Available Tools](#available-tools)
- [Domain Syntax](#domain-syntax)
- [Security](#security)
- [Contributing](#contributing)
- [License](#license)

## Quick Start

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/odoo-mcp-server.git
cd odoo-mcp-server

# Copy and configure environment
cp env.example .env
# Edit .env with your Odoo credentials

# Start with Docker
./start-mcp.sh

# View logs
docker logs -f odoo-mcp
```

## Installation

### Docker (Recommended)

1. **Configure environment**
   ```bash
   cp env.example .env
   ```

   Edit `.env` with your Odoo credentials:
   ```env
   ODOO_URL=https://your-odoo-instance.com
   ODOO_DB=your_database
   ODOO_USERNAME=admin
   ODOO_PASSWORD=your_api_key
   ```

2. **Start the server**
   ```bash
   ./start-mcp.sh
   ```

   Or manually:
   ```bash
   docker compose up -d
   ```

3. **Verify it's running**
   ```bash
   curl http://localhost:8000/sse
   ```

4. **Stop the server**
   ```bash
   ./stop-mcp.sh
   ```

### Local Installation

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install package
pip install -e .

# Run server (STDIO mode)
python -m odoo_mcp.server

# Or run with SSE transport
python -m odoo_mcp.server --sse --host 0.0.0.0 --port 8000
```

## Configuration

### Single Server (Environment Variables)

Set these environment variables or create a `.env` file:

| Variable | Description | Example |
|----------|-------------|---------|
| `ODOO_URL` | Odoo instance URL | `https://odoo.example.com` |
| `ODOO_DB` | Database name | `production` |
| `ODOO_USERNAME` | Login username | `admin` |
| `ODOO_PASSWORD` | Password or API key | `your_api_key` |

### Multi-Server Configuration

For connecting to multiple Odoo instances, create `odoo_servers.json`:

```bash
cp odoo_servers.json.example odoo_servers.json
```

Edit `odoo_servers.json`:

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

## Usage with Claude Code

### Docker SSE Mode

Add to your `.mcp.json` or MCP configuration:

```json
{
  "mcpServers": {
    "odoo": {
      "type": "sse",
      "url": "http://localhost:8000/sse"
    }
  }
}
```

### Local STDIO Mode

Add to `~/.claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "odoo": {
      "command": "python",
      "args": ["-m", "odoo_mcp.server"],
      "cwd": "/path/to/odoo-mcp-server",
      "env": {
        "ODOO_URL": "https://your-odoo.com",
        "ODOO_DB": "your_database",
        "ODOO_USERNAME": "admin",
        "ODOO_PASSWORD": "your_api_key"
      }
    }
  }
}
```

## Available Tools

### odoo_search_read

Search and read records from any Odoo model.

```json
{
  "model": "res.partner",
  "domain": [["is_company", "=", true]],
  "fields": ["name", "email", "phone"],
  "limit": 10,
  "offset": 0,
  "order": "name asc"
}
```

### odoo_search_count

Count records matching a domain.

```json
{
  "model": "sale.order",
  "domain": [["state", "=", "sale"]]
}
```

### odoo_read

Read specific records by IDs.

```json
{
  "model": "res.partner",
  "ids": [1, 2, 3],
  "fields": ["name", "email"]
}
```

### odoo_create

Create a new record.

```json
{
  "model": "res.partner",
  "values": {
    "name": "New Customer",
    "email": "customer@example.com",
    "is_company": false
  }
}
```

### odoo_write

Update existing records.

```json
{
  "model": "res.partner",
  "ids": [1],
  "values": {
    "phone": "+1234567890"
  }
}
```

### odoo_delete

Delete records by IDs.

```json
{
  "model": "res.partner",
  "ids": [1, 2]
}
```

### odoo_execute

Execute any method on a model.

```json
{
  "model": "sale.order",
  "method": "action_confirm",
  "args": [[1, 2, 3]]
}
```

### odoo_fields_get

Get field definitions for a model.

```json
{
  "model": "res.partner",
  "attributes": ["string", "type", "required"]
}
```

### odoo_version

Get Odoo server version information.

```json
{}
```

### odoo_list_servers

List all configured servers (multi-server mode only).

```json
{}
```

## Domain Syntax

Odoo uses a domain filter syntax as a list of conditions:

```python
# AND conditions (implicit)
[["field1", "=", "value1"], ["field2", ">", 100]]

# OR conditions
["|", ["field1", "=", "A"], ["field1", "=", "B"]]

# NOT condition
["!", ["active", "=", false]]

# Complex: (A AND B) OR C
["|", "&", ["field1", "=", "A"], ["field2", "=", "B"], ["field3", "=", "C"]]
```

**Available operators:**
- Comparison: `=`, `!=`, `>`, `>=`, `<`, `<=`
- Text: `like`, `ilike`, `not like`, `not ilike`
- List: `in`, `not in`
- Hierarchy: `child_of`, `parent_of`

## Security

- **Use API Keys** - Generate API keys in Odoo instead of using passwords
- **Never commit credentials** - `.env` and `odoo_servers.json` are in `.gitignore`
- **Least privilege** - Create a dedicated Odoo user with minimal required permissions
- **Network security** - In production, use HTTPS and restrict network access

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note:** This project is not affiliated with Odoo S.A. Odoo is a trademark of Odoo S.A.
