FROM python:3.12-slim

WORKDIR /app

# Install curl for healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies
COPY pyproject.toml README.md ./
COPY src/ ./src/

RUN pip install --no-cache-dir .

# Create non-root user
RUN useradd -m -u 1000 mcp
USER mcp

# Expose port for SSE mode
EXPOSE 8000

# Default: run with SSE transport for Docker
CMD ["python", "-m", "odoo_mcp.server", "--sse"]
