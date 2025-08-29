#!/usr/bin/env python3
"""
Setup script for Asset Browser virtual environment.
"""

import os
import sys
import subprocess
import venv
import platform


def main():
    """Setup virtual environment and install dependencies."""
    script_dir = os.path.dirname(os.path.abspath(__file__))
    venv_dir = os.path.join(script_dir, ".venv")
    requirements_file = os.path.join(script_dir, "requirements.txt")
    
    print("Setting up Asset Browser virtual environment...")
    
    # Create virtual environment if it doesn't exist
    if not os.path.exists(venv_dir):
        print(f"Creating virtual environment at: {venv_dir}")
        venv.create(venv_dir, with_pip=True)
    else:
        print(f"Virtual environment already exists at: {venv_dir}")
    
    # Determine the python executable path
    if platform.system() == "Windows":
        python_exe = os.path.join(venv_dir, "Scripts", "python.exe")
        pip_exe = os.path.join(venv_dir, "Scripts", "pip.exe")
    else:
        python_exe = os.path.join(venv_dir, "bin", "python")
        pip_exe = os.path.join(venv_dir, "bin", "pip")
    
    # Upgrade pip
    print("Upgrading pip...")
    subprocess.run([python_exe, "-m", "pip", "install", "--upgrade", "pip"], check=True)
    
    # Install requirements
    if os.path.exists(requirements_file):
        print(f"Installing requirements from: {requirements_file}")
        subprocess.run([pip_exe, "install", "-r", requirements_file], check=True)
    else:
        print("No requirements.txt file found, installing basic dependencies...")
        basic_deps = ["PySide6", "opencv-python-headless", "numpy"]
        subprocess.run([pip_exe, "install"] + basic_deps, check=True)
    
    print("\nSetup complete!")
    print(f"Virtual environment created at: {venv_dir}")
    print("\nTo run the Asset Browser:")
    print("  python main.py")
    print("\nOr use the batch/shell scripts if available.")


if __name__ == "__main__":
    main()
