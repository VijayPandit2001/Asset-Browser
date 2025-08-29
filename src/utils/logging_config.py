"""
Logging configuration and setup.
"""

import os
import logging
from logging.handlers import RotatingFileHandler


def setup_logging() -> logging.Logger:
    """Setup logging configuration for the Asset Browser."""
    lvl_name = os.environ.get("ASSET_BROWSER_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, lvl_name, logging.INFO)
    logger = logging.getLogger("asset_browser")
    logger.setLevel(level)
    
    if not logger.handlers:
        # File handler
        try:
            log_dir = os.path.join(os.path.expanduser("~"), ".assetbrowser_logs")
            os.makedirs(log_dir, exist_ok=True)
            fh = RotatingFileHandler(
                os.path.join(log_dir, "asset_browser.log"), 
                maxBytes=1_000_000, 
                backupCount=3, 
                encoding="utf-8"
            )
            fh.setLevel(level)
            fh.setFormatter(logging.Formatter(
                "%(asctime)s [%(levelname)s] %(threadName)s %(name)s: %(message)s"
            ))
            logger.addHandler(fh)
        except Exception:
            pass
            
        # Console handler
        sh = logging.StreamHandler()
        sh.setLevel(level)
        sh.setFormatter(logging.Formatter(
            "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        ))
        logger.addHandler(sh)
    
    return logger


# Global logger instance
LOGGER = setup_logging()
