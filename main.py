#!/usr/bin/env python3
"""
Asset Browser (Standalone) — Python + OpenCV + OpenImageIO (OIIO) + PySide6

Main entry point for the Asset Browser application.

Virtual Environment Support:
  A virtual environment (.venv) will be automatically used if present in the script directory.
  Run setup.py to create the virtual environment and install dependencies.
  
Tested with Python 3.10+
"""

import sys
import os
from src.utils.environment import setup_virtual_environment
from src.core.application import AssetBrowserApp

def main():
    """Main entry point for the Asset Browser application."""
    # Setup virtual environment before importing other dependencies
    setup_virtual_environment()
    
    # Create and run the application
    app = AssetBrowserApp()
    start_dir = sys.argv[1] if len(sys.argv) > 1 else None
    return app.run(start_dir)

if __name__ == "__main__":
    sys.exit(main())
