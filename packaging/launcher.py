"""PyInstaller entry point for the cove-download-manager bundles.

PyInstaller treats the script as a top-level module, which would break
relative imports inside the package. Importing through the package keeps
them working.
"""
from cove.app import run

if __name__ == "__main__":
    raise SystemExit(run())
