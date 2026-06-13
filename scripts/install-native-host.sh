#!/usr/bin/env bash
# Install the native messaging host manifest for Firefox.
# Usage: ./scripts/install-native-host.sh [extension-id]

set -euo pipefail

EXT_ID="${1:-cove-dm@cove-download-manager.net}"
HOST_NAME="cove_download_manager"
MANIFEST_DIR="$HOME/.mozilla/native-messaging-hosts"

# Find the Python that has cove installed.
PYTHON="$(command -v python3 || command -v python)"
if [ -z "$PYTHON" ]; then
    echo "Error: python3 not found" >&2
    exit 1
fi

# Verify cove is importable.
if ! "$PYTHON" -c "import cove.native_messaging" 2>/dev/null; then
    echo "Error: cove.native_messaging not importable by $PYTHON" >&2
    echo "Install cove first: pip install -e ." >&2
    exit 1
fi

mkdir -p "$MANIFEST_DIR"

# Write a wrapper script that invokes the native messaging host.
WRAPPER="$MANIFEST_DIR/$HOST_NAME"
cat > "$WRAPPER" << WRAPPER_EOF
#!/usr/bin/env bash
exec $PYTHON -c "from cove.native_messaging import main; main()"
WRAPPER_EOF
chmod +x "$WRAPPER"

# Write the native messaging host manifest.
cat > "$MANIFEST_DIR/$HOST_NAME.json" << EOF
{
  "name": "$HOST_NAME",
  "description": "Cove Download Manager native messaging host",
  "path": "$WRAPPER",
  "type": "stdio",
  "allowed_extensions": ["$EXT_ID"]
}
EOF

echo "Installed native messaging host:"
echo "  Manifest: $MANIFEST_DIR/$HOST_NAME.json"
echo "  Wrapper:  $WRAPPER"
echo "  Extension ID: $EXT_ID"
