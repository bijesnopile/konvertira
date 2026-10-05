#!/usr/bin/env sh
set -eu

# Konvertira has no persistent application database. Result volumes contain
# short-lived user files and must not be copied into longer-lived backups.
echo "No persistent Konvertira application data to back up."
echo "Temporary processed-file volumes are intentionally excluded."
