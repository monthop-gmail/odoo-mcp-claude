# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-16

### Added

- **Core MCP Server** (`src/odoo_mcp/server.py`)
  - Async MCP server implementation using MCP protocol v1.0.0+
  - Dual transport support: STDIO (local) and SSE/HTTP (Docker)
  - 10 registered tools for Odoo operations

- **Odoo Client** (`src/odoo_mcp/odoo_client.py`)
  - XML-RPC wrapper for Odoo API
  - Lazy authentication (authenticates on first use)
  - CRUD operations: search, read, search_read, create, write, unlink
  - Schema introspection via fields_get()

- **MCP Tools**
  - `odoo_search_read` - Search and read records with domain filtering
  - `odoo_search_count` - Count records matching criteria
  - `odoo_read` - Read specific records by IDs
  - `odoo_create` - Create new records
  - `odoo_write` - Update existing records
  - `odoo_delete` - Delete records
  - `odoo_execute` - Execute any model method
  - `odoo_fields_get` - Get field definitions
  - `odoo_version` - Get Odoo server version
  - `odoo_list_servers` - List configured servers

- **Multi-Server Support**
  - Configuration via `odoo_servers.json`
  - Switch between servers using `server` parameter
  - Default server fallback

- **Docker Support**
  - Dockerfile for containerized deployment
  - docker-compose.yml for easy orchestration
  - Helper scripts: `start-mcp.sh`, `stop-mcp.sh`

- **Documentation**
  - README.md with installation and usage guide
  - CLAUDE.md for AI assistant context
  - Example configuration files

### Security

- Credentials excluded from version control via .gitignore
- Support for Odoo API keys (recommended over passwords)
- Example files provided for safe configuration

---

## Template for Future Releases

## [X.Y.Z] - YYYY-MM-DD

### Added
- New features

### Changed
- Changes in existing functionality

### Deprecated
- Soon-to-be removed features

### Removed
- Removed features

### Fixed
- Bug fixes

### Security
- Vulnerability fixes
