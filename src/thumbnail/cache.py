"""
Thumbnail generation data structures and utilities.
"""

import os
import hashlib
import numpy as np
from dataclasses import dataclass
from typing import Optional
from PySide6.QtGui import QPixmap
from ..config.constants import THUMB_CACHE_VERSION


@dataclass
class ThumbResult:
    """Result data structure for thumbnail generation."""
    path: str
    pixmap: Optional[QPixmap]
    meta_text: str


class CacheManager:
    """Manages thumbnail cache operations."""
    
    @staticmethod
    def hash_for_file(path: str) -> str:
        """Generate a hash for the file for cache key."""
        try:
            st = os.stat(path)
            payload = f"{THUMB_CACHE_VERSION}|{path}|{st.st_mtime_ns}|{st.st_size}".encode()
        except FileNotFoundError:
            payload = f"{THUMB_CACHE_VERSION}|{path}".encode()
        return hashlib.sha1(payload).hexdigest()

    @classmethod
    def get_cache_path(cls, cache_root: str, src_path: str) -> str:
        """Get the cache file path for a given source file."""
        h = cls.hash_for_file(src_path)
        sub = os.path.join(cache_root, h[:2])
        os.makedirs(sub, exist_ok=True)
        return os.path.join(sub, f"{h}.png")
    
    @staticmethod
    def generate_cache_root(current_project: Optional[str], folder: str) -> str:
        """Generate cache root directory for the given folder."""
        if current_project:
            # Use project-based cache: (ProjectName)_AssetBrowserCache
            project_name = os.path.basename(current_project)
            cache_folder_name = f"{project_name}_AssetBrowserCache"
            # Store cache in the project root directory
            cache_root = os.path.join(current_project, cache_folder_name)
            
            # Create subdirectory structure within cache based on relative path
            try:
                rel_path = os.path.relpath(folder, current_project)
                if rel_path and rel_path != ".":
                    # Replace path separators with underscores to create a valid folder name
                    safe_rel_path = rel_path.replace(os.sep, "_").replace("/", "_").replace("\\", "_")
                    cache_root = os.path.join(cache_root, safe_rel_path)
            except ValueError:
                # If folder is outside project, fall back to simple cache
                pass
                
            return cache_root
        else:
            # Fallback to old behavior if no project is selected
            return os.path.join(folder, ".assetbrowser_cache")
