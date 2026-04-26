#!/usr/bin/env bash
# Cove Download Manager — AppImage entrypoint.

set -e

# Make bundled binaries (aria2c, etc.) and libraries discoverable.
export PATH="${APPDIR}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${APPDIR}/usr/lib:${LD_LIBRARY_PATH:-}"

# Friendly message if aria2 is missing — Cove will also surface its own
# dialog, but a terminal hint is useful when launched from a shell.
if ! command -v aria2c >/dev/null 2>&1; then
    echo "Cove: aria2c not found in PATH." >&2
    echo "  Install it: sudo pacman -S aria2" >&2
fi

exec {{ python-executable }} -m cove "$@"
