# Odoo MCP Server

MCP (Model Context Protocol) Server สำหรับเชื่อมต่อ Odoo ERP กับ AI Agents เช่น Claude Code

## Features

- **CRUD Operations** - Create, Read, Update, Delete records
- **Search & Filter** - ใช้ Odoo domain filter syntax
- **Execute Methods** - เรียก method บน Odoo models
- **Schema Introspection** - ดู field definitions
- **Multi-Server Support** - เชื่อมต่อหลาย Odoo instances

## Tools

| Tool | Description |
|------|-------------|
| `odoo_search_read` | ค้นหาและอ่าน records |
| `odoo_search_count` | นับจำนวน records |
| `odoo_read` | อ่าน records ตาม IDs |
| `odoo_create` | สร้าง record ใหม่ |
| `odoo_write` | แก้ไข records |
| `odoo_delete` | ลบ records |
| `odoo_execute` | เรียก method บน model |
| `odoo_fields_get` | ดู field definitions |
| `odoo_version` | ดูเวอร์ชัน Odoo |
| `odoo_list_servers` | รายการ servers ที่ config ไว้ |

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/monthop-gmail/odoo-mcp-claude.git
cd odoo-mcp-claude
```

### 2. Configure Environment

```bash
cp env.example .env
nano .env
```

```env
ODOO_URL=https://your-odoo-instance.com
ODOO_DB=your_database
ODOO_USERNAME=admin
ODOO_PASSWORD=your_api_key
```

### 3. Multi-Server Configuration (Optional)

```bash
cp odoo_servers.json.example odoo_servers.json
nano odoo_servers.json
```

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

### 4. Start with Docker Compose

```bash
docker compose up -d --build
```

### 5. Verify

```bash
# Check status
docker compose ps

# Test health
curl http://localhost:8000/health

# View logs
docker logs -f odoo-mcp
```

## Add to Claude Code

```bash
# Add MCP server
claude mcp add --transport sse --scope user odoo http://localhost:8000/sse

# Verify connection
claude mcp list

# Remove (if needed)
claude mcp remove odoo
```

## Endpoints

| Endpoint | Description |
|----------|-------------|
| `http://localhost:8000/sse` | SSE connection for MCP |
| `http://localhost:8000/health` | Health check |

## Domain Syntax

Odoo ใช้ domain filter syntax:

```python
# AND conditions
[["field1", "=", "value1"], ["field2", ">", 100]]

# OR conditions
["|", ["field1", "=", "A"], ["field1", "=", "B"]]

# NOT condition
["!", ["active", "=", false]]
```

**Operators:** `=`, `!=`, `>`, `>=`, `<`, `<=`, `like`, `ilike`, `in`, `not in`

## Security

- ใช้ API Keys แทน password
- `.env` และ `odoo_servers.json` อยู่ใน `.gitignore`
- สร้าง Odoo user แยกที่มี permissions จำกัด

## License

MIT
