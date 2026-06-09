#!/usr/bin/env bash
set -euo pipefail

ADDON_DIR="service.video.playhistory"

if [ ! -d "$ADDON_DIR" ]; then
    echo "Error: $ADDON_DIR not found"
    exit 1
fi

VERSION=$(date +%Y%m%d%H%M%S)

python3 <<-EOF
import re
with open("$ADDON_DIR/addon.xml") as f:
    c = f.read()
c = re.sub(
    r'(<addon\s+.*?version=)"[^"]*"',
    r'\1"$VERSION"',
    c,
    count=1,
    flags=re.DOTALL,
)
with open("$ADDON_DIR/addon.xml", "w") as f:
    f.write(c)
EOF

ADDON_ID=$(grep -oP '<addon[^>]*id="\K[^"]+' "$ADDON_DIR/addon.xml")
OUTPUT="${ADDON_ID}-${VERSION}.zip"

rm -f "$OUTPUT"
cd "$(dirname "$0")"
zip -r "$OUTPUT" "$ADDON_DIR" -x "*/__pycache__/*" "*.pyc" "*.pyo"
echo "Packaged: $OUTPUT"
echo "Version: $VERSION"
