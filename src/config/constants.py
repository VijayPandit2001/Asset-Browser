"""
Constants and configuration settings for the Asset Browser.
"""

# Supported file extensions
SUPPORTED_VIDEO_EXTS = {".mp4", ".mov", ".avi", ".mkv", ".webm"}
SUPPORTED_IMAGE_EXTS = {
    ".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif",
    ".exr", ".hdr", ".dpx", ".psd", ".svg", ".jp2"
}

# Thumbnail settings
THUMB_BG = (28, 28, 30)  # Background color for thumbnails
THUMB_CACHE_VERSION = "2"  # Cache version for invalidation

# Default settings
DEFAULT_SETTINGS = {
    'thumb_size': 256,
    'cache_enabled': True,
    'grid_spacing': 8,
    'show_metadata': True,
    'show_tree_view': True,
    'view_mode': 'grid',  # 'grid' or 'list'
    'thread_count': 4,  # Will be updated to actual CPU count
    'preload_thumbnails': True,
    'max_cache_size': 100,
    'auto_clear_cache': False,
    'log_level': 'INFO',
    'enable_debug': False,
    'use_oiio': True,  # Will be updated based on availability
    'hdr_tonemap': True,
    'projects': [],  # List of project folder paths
    'supported_formats': {
        '.jpg': True, '.jpeg': True, '.png': True, '.bmp': True,
        '.tiff': True, '.tif': True, '.gif': True, '.exr': True,
        '.hdr': True, '.dpx': True, '.psd': True, '.svg': True,
        '.jp2': True, '.mp4': True, '.mov': True, '.avi': True,
        '.mkv': True, '.webm': True
    }
}
