"""
File type detection utilities.
"""

import os
from ..config.constants import SUPPORTED_VIDEO_EXTS, SUPPORTED_IMAGE_EXTS


def is_video(path: str) -> bool:
    """Check if the file is a supported video format."""
    return os.path.splitext(path)[1].lower() in SUPPORTED_VIDEO_EXTS


def is_image(path: str) -> bool:
    """Check if the file is a supported image format."""
    return os.path.splitext(path)[1].lower() in SUPPORTED_IMAGE_EXTS


def is_supported_asset(path: str) -> bool:
    """Check if the file is a supported asset (image or video)."""
    return is_image(path) or is_video(path)


def is_in_archive(path: str) -> bool:
    """Check if the file path indicates it's inside a compressed archive."""
    archive_extensions = {'.7z', '.zip', '.rar', '.tar', '.gz', '.bz2'}
    path_parts = os.path.normpath(path).split(os.sep)
    return any(any(part.lower().endswith(ext) for ext in archive_extensions) for part in path_parts)


def get_archive_name(path: str) -> str:
    """Get the name of the archive file containing this path."""
    archive_extensions = {'.7z', '.zip', '.rar', '.tar', '.gz', '.bz2'}
    path_parts = os.path.normpath(path).split(os.sep)
    for part in path_parts:
        if any(part.lower().endswith(ext) for ext in archive_extensions):
            return part
    return ""
