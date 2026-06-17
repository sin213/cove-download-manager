"""Auto-install native messaging host manifests for Firefox-based browsers.

Called once on app startup. Writes (or refreshes) the JSON manifest and
wrapper script into each browser's native-messaging-hosts directory so the
Cove extension can connect without manual setup.

Supports: Firefox, Zen, LibreWolf, Waterfox, Floorp.
"""
from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path

HOST_NAME = "cove_download_manager"
EXTENSION_ID = "cove-dm@cove-download-manager.net"

_BROWSER_DIRS = [
    Path.home() / ".mozilla" / "native-messaging-hosts",
    Path.home() / ".zen" / "native-messaging-hosts",
    Path.home() / ".librewolf" / "native-messaging-hosts",
    Path.home() / ".waterfox" / "native-messaging-hosts",
    Path.home() / ".floorp" / "native-messaging-hosts",
]


def _wrapper_command() -> str:
    """Build the shell command that launches the native messaging host.

    - AppImage: use $APPIMAGE directly with --native-messaging flag
    - pip / venv: use the current Python interpreter
    """
    appimage = os.environ.get("APPIMAGE")
    if appimage:
        return f'exec "{appimage}" --native-messaging'

    python = sys.executable or "python3"
    return f'exec "{python}" -c "from cove.native_messaging import main; main()"'


def _manifest(wrapper_path: str) -> dict:
    return {
        "name": HOST_NAME,
        "description": "Cove Download Manager native messaging host",
        "path": wrapper_path,
        "type": "stdio",
        "allowed_extensions": [EXTENSION_ID],
    }


def install_native_hosts() -> list[str]:
    """Install manifests into every browser dir whose parent exists.

    Returns list of directories where manifests were written.
    """
    command = _wrapper_command()
    installed: list[str] = []

    for hosts_dir in _BROWSER_DIRS:
        if not hosts_dir.parent.exists():
            continue

        hosts_dir.mkdir(parents=True, exist_ok=True)

        wrapper_path = hosts_dir / HOST_NAME
        wrapper_path.write_text(f"#!/usr/bin/env bash\n{command}\n")
        wrapper_path.chmod(wrapper_path.stat().st_mode | stat.S_IEXEC)

        manifest_path = hosts_dir / f"{HOST_NAME}.json"
        manifest_path.write_text(json.dumps(_manifest(str(wrapper_path)), indent=2) + "\n")

        installed.append(str(hosts_dir))

    return installed
