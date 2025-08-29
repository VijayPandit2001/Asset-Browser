"""
Image processing utilities for thumbnails.
"""

import os
import cv2
import numpy as np
from typing import Optional
from PySide6.QtGui import QImage
from ..utils.logging_config import LOGGER
from ..config.constants import SUPPORTED_VIDEO_EXTS

# Setup OpenCV logging
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
try:
    cv2.setLogLevel(getattr(cv2, "LOG_LEVEL_ERROR", 3))
except Exception:
    try:
        from cv2 import utils as _cv2_utils
        _cv2_utils.logging.setLogLevel(_cv2_utils.logging.LOG_LEVEL_ERROR)
    except Exception:
        pass

# Import OpenImageIO if available
try:
    import OpenImageIO as oiio
except ImportError:
    oiio = None


class ImageProcessor:
    """Handles image processing operations for thumbnail generation."""
    
    @staticmethod
    def to_qimage(bgr_or_rgb: np.ndarray, is_bgr: bool = True) -> QImage:
        """Convert numpy array to QImage."""
        if bgr_or_rgb is None:
            return QImage()
        img = bgr_or_rgb
        if is_bgr:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        h, w, c = img.shape
        qimg = QImage(img.data, w, h, c * w, QImage.Format.Format_RGB888)
        return qimg.copy()

    @classmethod
    def read_image_oiio(cls, path: str) -> Optional[np.ndarray]:
        """Read image using OpenImageIO."""
        if oiio is None:
            LOGGER.debug("OIIO not available; skipping OIIO read")
            return None
        
        # Check if this is likely a video file that OIIO can't handle
        ext = os.path.splitext(path)[1].lower()
        if ext in SUPPORTED_VIDEO_EXTS:
            LOGGER.debug(f"Skipping OIIO for video file: {path}")
            return None
            
        # Try ImageInput API first, then fall back to ImageBuf
        try:
            inp = None
            if hasattr(oiio, "ImageInput"):
                inp = oiio.ImageInput.open(path)
            elif hasattr(oiio, "Input"):
                # Older alias (rare); keep for safety
                inp = oiio.Input.open(path)
            if inp:
                try:
                    spec = inp.spec()
                    arr = inp.read_image(oiio.FLOAT)
                    arr = np.array(arr).reshape(spec.height, spec.width, spec.nchannels)
                finally:
                    inp.close()
            else:
                # ImageBuf path
                if hasattr(oiio, "ImageBuf"):
                    ib = oiio.ImageBuf(path)
                    arr = np.array(ib.get_pixels(oiio.FLOAT))
                    arr = arr.reshape(ib.spec().height, ib.spec().width, ib.spec().nchannels)
                else:
                    return None

            # Ensure 3 channels RGB float in [0,1] with tonemapping if HDR-like
            if arr.shape[2] == 1:
                arr = np.repeat(arr, 3, axis=2)
            elif arr.shape[2] == 2:
                pad = np.zeros((arr.shape[0], arr.shape[1], 1), dtype=np.float32)
                arr = np.concatenate([arr, pad], axis=2)
            elif arr.shape[2] >= 3:
                arr = arr[:, :, :3]

            ext = os.path.splitext(path)[1].lower()
            needs_hdr_tonemap = ext in {".exr", ".hdr"} or (np.isfinite(arr).any() and float(np.nanmax(arr)) > 1.2)
            if needs_hdr_tonemap:
                LOGGER.debug(f"Tonemapping HDR image: {path}")
                arr = cls.tonemap_float_image(arr)
            else:
                arr = np.clip(arr, 0.0, 1.0)

            arr8 = (arr * 255.0 + 0.5).astype(np.uint8)
            arr8 = cv2.cvtColor(arr8, cv2.COLOR_RGB2BGR)
            return arr8
        except Exception as e:
            # More specific error handling for common cases
            if "format reader" in str(e).lower():
                LOGGER.debug(f"OIIO doesn't support format for {path}: {e}")
            elif ext in SUPPORTED_VIDEO_EXTS:
                LOGGER.debug(f"OIIO attempted to read video file {path}, this is expected to fail")
            elif "file format that OpenImageIO doesn't know about" in str(e):
                LOGGER.debug(f"OIIO format not supported for {path}")
            else:
                LOGGER.warning(f"OIIO exception reading {path}: {e}")
            return None

    @staticmethod
    def tonemap_float_image(arr: np.ndarray) -> np.ndarray:
        """Apply tonemapping to HDR image."""
        arr = np.nan_to_num(arr, nan=0.0, posinf=1e4, neginf=0.0)
        R = arr[:, :, 0]; G = arr[:, :, 1]; B = arr[:, :, 2]
        lum = 0.2126 * R + 0.7152 * G + 0.0722 * B
        flat = lum.reshape(-1)
        nz = flat[flat > 0]
        p95 = float(np.percentile(nz if nz.size else flat, 95)) if flat.size else 1.0
        scale = 0.85 / max(p95, 1e-6)
        arr = arr * scale
        arr = arr / (1.0 + arr)
        arr = np.clip(arr, 0.0, 1.0)
        arr = np.power(arr, 1.0 / 2.2, out=arr)
        return arr

    @classmethod
    def read_metadata_oiio(cls, path: str) -> str:
        """Read metadata using OpenImageIO."""
        if oiio is None:
            return ""
        
        # Skip video files as OIIO doesn't handle them
        ext = os.path.splitext(path)[1].lower()
        if ext in SUPPORTED_VIDEO_EXTS:
            LOGGER.debug(f"Skipping OIIO metadata for video file: {path}")
            return f"Video file: {ext.upper()}"
            
        try:
            spec = None
            if hasattr(oiio, "ImageInput"):
                inp = oiio.ImageInput.open(path)
                if not inp:
                    return ""
                try:
                    spec = inp.spec()
                finally:
                    inp.close()
            elif hasattr(oiio, "Input"):
                inp = oiio.Input.open(path)
                if not inp:
                    return ""
                try:
                    spec = inp.spec()
                finally:
                    inp.close()
            elif hasattr(oiio, "ImageBuf"):
                ib = oiio.ImageBuf(path)
                spec = ib.spec()
            if spec is None:
                return ""
            base = f"{spec.width}x{spec.height}x{spec.nchannels}, format={getattr(spec, 'format', '')}"
            lines = []
            try:
                extras = getattr(spec, "extra_attribs", [])
                for a in extras[:64]:
                    lines.append(f"{a.name}: {a.value}")
            except Exception:
                pass
            return base + ("\n" + "\n".join(lines) if lines else "")
        except Exception:
            return ""

    @classmethod
    def extract_frame_video(cls, path: str) -> Optional[np.ndarray]:
        """Extract first frame from video file."""
        # Normalize path to handle mixed slashes
        normalized_path = os.path.normpath(path)
        
        # Check if the file is inside an archive (7z, zip, rar, etc.)
        archive_extensions = {'.7z', '.zip', '.rar', '.tar', '.gz', '.bz2'}
        path_parts = normalized_path.split(os.sep)
        for part in path_parts:
            if any(part.lower().endswith(ext) for ext in archive_extensions):
                LOGGER.debug(f"Video file is inside archive, cannot extract frame: {normalized_path}")
                return None
        
        # Check if file actually exists
        if not os.path.exists(normalized_path):
            LOGGER.debug(f"Video file does not exist: {normalized_path}")
            return None
        
        cap = cv2.VideoCapture(normalized_path)
        if not cap.isOpened():
            LOGGER.warning(f"Could not open video file: {normalized_path}")
            return None
        fps = cap.get(cv2.CAP_PROP_FPS) or 0
        if fps > 0:
            cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
        ok, frame = cap.read()
        cap.release()
        if not ok or frame is None:
            LOGGER.warning(f"Could not read frame from video: {normalized_path}")
            return None
        LOGGER.debug(f"Successfully extracted frame from video: {normalized_path}")
        return frame

    @classmethod
    def get_video_metadata(cls, path: str) -> str:
        """Get video metadata using OpenCV."""
        try:
            normalized_path = os.path.normpath(path)
            
            # Check if the file is inside an archive
            archive_extensions = {'.7z', '.zip', '.rar', '.tar', '.gz', '.bz2'}
            path_parts = normalized_path.split(os.sep)
            for part in path_parts:
                if any(part.lower().endswith(ext) for ext in archive_extensions):
                    archive_name = part
                    ext = os.path.splitext(path)[1].upper()
                    return f"Video file in archive: {archive_name}\nFormat: {ext[1:] if ext else 'Unknown'}\nNote: Extract archive to view video"
            
            # Check if file exists
            if not os.path.exists(normalized_path):
                ext = os.path.splitext(path)[1].upper()
                return f"Video file not found\nFormat: {ext[1:] if ext else 'Unknown'}"
            
            cap = cv2.VideoCapture(normalized_path)
            if not cap.isOpened():
                ext = os.path.splitext(path)[1].upper()
                return f"Cannot open video file\nFormat: {ext[1:] if ext else 'Unknown'}"
            
            # Get video properties
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            cap.release()
            
            # Format metadata
            metadata = [
                f"Video: {width}x{height}",
                f"FPS: {fps:.2f}" if fps > 0 else "FPS: Unknown",
                f"Duration: {duration:.2f}s" if duration > 0 else "Duration: Unknown",
                f"Frames: {frame_count}" if frame_count > 0 else "Frames: Unknown",
                f"Codec: {os.path.splitext(path)[1].upper()[1:]}"
            ]
            
            return "\n".join(metadata)
            
        except Exception as e:
            LOGGER.debug(f"Failed to get video metadata for {path}: {e}")
            ext = os.path.splitext(path)[1].upper()
            return f"Video file: {ext[1:] if ext else 'Unknown'}"
