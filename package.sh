#!/usr/bin/env bash
set -euo pipefail

ADDON_DIR="service.video.playhistory"

if [ ! -d "$ADDON_DIR" ]; then
    echo "Error: $ADDON_DIR not found"
    exit 1
fi

ADDON_TAG=$(tr '\n' ' ' < "$ADDON_DIR/addon.xml")
ADDON_ID=$(echo "$ADDON_TAG" | grep -oP '<addon[^>]*id="\K[^"]+')
ADDON_VERSION=$(echo "$ADDON_TAG" | grep -oP '<addon[^>]*version="\K[^"]+')
OUTPUT="${ADDON_ID}-${ADDON_VERSION}.zip"

rm -f "$OUTPUT"
cd "$(dirname "$0")"
zip -r "$OUTPUT" "$ADDON_DIR" -x "*/__pycache__/*" "*.pyc" "*.pyo"
echo "Packaged: $OUTPUT"
