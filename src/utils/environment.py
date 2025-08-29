"""
Virtual environment setup utilities.
"""

import os
import sys


def setup_virtual_environment():
    """Setup virtual environment if available in the script directory."""
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    venv_dir = os.path.join(script_dir, ".venv")
    
    # Check if we're already in a virtual environment
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        return  # Already in a virtual environment
    
    # Check if virtual environment exists and use it
    if os.path.exists(venv_dir):
        if sys.platform == "win32":
            venv_python = os.path.join(venv_dir, "Scripts", "python.exe")
        else:
            venv_python = os.path.join(venv_dir, "bin", "python")
        
        if os.path.exists(venv_python) and os.path.samefile(sys.executable, venv_python):
            return  # Already using virtual environment Python
        
        # Re-execute with virtual environment Python if not already using it
        if os.path.exists(venv_python):
            print(f"Using virtual environment: {venv_dir}")
            os.execv(venv_python, [venv_python] + sys.argv)
