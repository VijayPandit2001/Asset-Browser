"""
Configuration management for the Asset Browser.
"""

import os
import json
from PySide6.QtCore import QThreadPool
from ..config.constants import DEFAULT_SETTINGS
from ..utils.logging_config import LOGGER

try:
    import OpenImageIO as oiio
except ImportError:
    oiio = None


class ConfigManager:
    """Simple configuration manager for storing and loading settings."""
    
    def __init__(self):
        self.config_dir = os.path.join(os.path.expanduser("~"), ".assetbrowser_config")
        self.config_file = os.path.join(self.config_dir, "settings.json")
        self.default_settings = DEFAULT_SETTINGS.copy()
        
        # Update defaults based on system
        self.default_settings['thread_count'] = QThreadPool.globalInstance().maxThreadCount()
        self.default_settings['use_oiio'] = oiio is not None
    
    def load_settings(self):
        """Load settings from config file, return defaults if file doesn't exist."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    loaded = json.load(f)
                # Merge with defaults to ensure all keys exist
                settings = self.default_settings.copy()
                settings.update(loaded)
                return settings
        except Exception as e:
            LOGGER.warning(f"Failed to load settings: {e}")
        
        return self.default_settings.copy()
    
    def save_settings(self, settings):
        """Save settings to config file."""
        try:
            os.makedirs(self.config_dir, exist_ok=True)
            with open(self.config_file, 'w') as f:
                json.dump(settings, f, indent=2)
            LOGGER.info(f"Settings saved to {self.config_file}")
        except Exception as e:
            LOGGER.error(f"Failed to save settings: {e}")
