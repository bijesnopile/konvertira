#!/usr/bin/env sh
set -eu

BACKEND_HEALTH_URL="${BACKEND_HEALTH_URL:-http://localhost:8000/health}"
MCP_HEALTH_URL="${MCP_HEALTH_URL:-http://localhost:8001/health}"

curl --fail --silent --show-error "$BACKEND_HEALTH_URL"
curl --fail --silent --show-error "$MCP_HEALTH_URL"
