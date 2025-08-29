"""
Thumbnail generation task and threading.
"""

import os
import cv2
import numpy as np
from typing import Tuple, Optional
from PySide6.QtCore import QRunnable, Signal, QObject
from PySide6.QtGui import QPixmap
from .cache import ThumbResult, CacheManager
from .image_processor import ImageProcessor
from ..utils.file_utils import is_video, is_image, is_in_archive, get_archive_name
from ..utils.logging_config import LOGGER
from ..config.constants import THUMB_BG


class ThumbSignal(QObject):
    """Signal emitter for thumbnail generation."""
    done = Signal(object)  # ThumbResult


class ThumbTask(QRunnable):
    """Thumbnail generation task for threading."""
    
    def __init__(self, path: str, thumb_size: int, cache_root: str):
        super().__init__()
        self.signals = ThumbSignal()
        self.path = path
        self.thumb_size = thumb_size
        self.cache_root = cache_root
        self.image_processor = ImageProcessor()

    def run(self):
        """Execute the thumbnail generation task."""
        LOGGER.debug(f"ThumbTask start: path={self.path}, size={self.thumb_size}")
        pixmap, meta_text = self._make_thumbnail(self.path, self.thumb_size, self.cache_root)
        LOGGER.debug(f"ThumbTask done: path={self.path}, pix={'yes' if pixmap else 'no'}, meta_len={len(meta_text) if meta_text else 0}")
        self.signals.done.emit(ThumbResult(self.path, pixmap, meta_text))

    def _make_thumbnail(self, path: str, thumb_size: int, cache_root: str) -> Tuple[Optional[QPixmap], str]:
        """Generate thumbnail for the given file."""
        os.makedirs(cache_root, exist_ok=True)
        cache_path = CacheManager.get_cache_path(cache_root, path)
        
        # Check cache first
        if os.path.exists(cache_path):
            LOGGER.debug(f"Cache hit for {path} -> {cache_path}")
            img = cv2.imread(cache_path, cv2.IMREAD_COLOR)
            if img is not None:
                qimg = self.image_processor.to_qimage(img, is_bgr=True)
                pixmap = QPixmap.fromImage(qimg)
                # Get appropriate metadata based on file type
                if is_video(path):
                    meta = self.image_processor.get_video_metadata(path)
                else:
                    meta = self.image_processor.read_metadata_oiio(path)
                return pixmap, meta
            else:
                LOGGER.debug(f"Cache read failed (cv2 returned None) for {cache_path}")

        img_bgr = None
        meta = ""
        # Normalize path to handle mixed slashes
        normalized_path = os.path.normpath(path)
        
        if is_video(normalized_path):
            LOGGER.debug(f"Loading video frame for {normalized_path}")
            img_bgr = self.image_processor.extract_frame_video(normalized_path)
            # Use video metadata instead of OIIO metadata for video files
            meta = self.image_processor.get_video_metadata(normalized_path)
        elif is_image(normalized_path):
            LOGGER.debug(f"Loading image via OIIO for {normalized_path}")
            img_bgr = self.image_processor.read_image_oiio(normalized_path)
            meta = self.image_processor.read_metadata_oiio(normalized_path)
            if img_bgr is None:
                try:
                    img_bgr = cv2.imread(normalized_path, cv2.IMREAD_COLOR)
                except cv2.error:
                    LOGGER.warning(f"OpenCV failed to read image: {normalized_path}")
        else:
            # For unknown extensions, try OpenCV first (safer), then OIIO if enabled
            try:
                LOGGER.debug(f"Unknown extension, trying OpenCV first for {normalized_path}")
                img_bgr = cv2.imread(normalized_path, cv2.IMREAD_COLOR)
                meta = self.image_processor.read_metadata_oiio(normalized_path)
            except cv2.error:
                LOGGER.debug(f"OpenCV failed, trying OIIO for {normalized_path}")
                img_bgr = self.image_processor.read_image_oiio(normalized_path)
                meta = self.image_processor.read_metadata_oiio(normalized_path)

        if img_bgr is None:
            LOGGER.debug(f"Failed to load media for thumbnail, using placeholder: {path}")
            # Create 16:9 aspect ratio placeholder
            thumb_height = int(thumb_size * 9 / 16)
            thumb = np.full((thumb_height, thumb_size, 3), THUMB_BG, np.uint8)
            
            # Check if it's an archive file to provide appropriate icon
            if is_in_archive(path):
                # Use archive icon
                cv2.putText(thumb, "ZIP", (thumb_size//2-20, thumb_height//2+10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200,200,200), 2, cv2.LINE_AA)
                archive_name = get_archive_name(path)
                meta = meta or f"File in compressed archive: {archive_name}\nExtract archive to view content"
            else:
                # Use generic unknown icon
                cv2.putText(thumb, "?", (thumb_size//2-10, thumb_height//2+10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.5, (200,200,200), 2, cv2.LINE_AA)
                meta = meta or "(unsupported or failed to load)"
            
            qimg = self.image_processor.to_qimage(thumb, is_bgr=True)
            return QPixmap.fromImage(qimg), meta

        h, w = img_bgr.shape[:2]
        # Create 16:9 aspect ratio thumbnail
        thumb_height = int(thumb_size * 9 / 16)
        
        # Scale to fit within the 16:9 box while maintaining aspect ratio
        scale = min(thumb_size / w, thumb_height / h)
        new_w, new_h = max(1, int(w*scale)), max(1, int(h*scale))
        resized = cv2.resize(img_bgr, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
        
        # Create 16:9 canvas and center the image
        canvas = np.full((thumb_height, thumb_size, 3), THUMB_BG, np.uint8)
        y0 = (thumb_height - new_h)//2
        x0 = (thumb_size - new_w)//2
        canvas[y0:y0+new_h, x0:x0+new_w] = resized

        try:
            cv2.imwrite(cache_path, canvas)
            LOGGER.debug(f"Wrote cache thumbnail: {cache_path}")
        except Exception as e:
            LOGGER.warning(f"Failed to write cache {cache_path}: {e}")

        qimg = self.image_processor.to_qimage(canvas, is_bgr=True)
        return QPixmap.fromImage(qimg), meta
