#!/usr/bin/env sh
set -eu

BACKUP_DIR="${BACKUP_DIR:-./backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
mkdir -p "$BACKUP_DIR"

docker run --rm -v konvertira_backend_results:/data:ro -v "$(cd "$BACKUP_DIR" && pwd):/backup" alpine \
  tar -czf "/backup/backend-results-$STAMP.tar.gz" -C /data .
docker run --rm -v konvertira_mcp_results:/data:ro -v "$(cd "$BACKUP_DIR" && pwd):/backup" alpine \
  tar -czf "/backup/mcp-results-$STAMP.tar.gz" -C /data .
