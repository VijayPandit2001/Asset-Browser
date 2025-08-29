"""
Thumbnail list widget for displaying asset thumbnails.
"""

from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QListWidget


class ThumbList(QListWidget):
    """Custom list widget for displaying thumbnails in a grid."""
    
    def __init__(self):
        super().__init__()
        self.setViewMode(QListWidget.IconMode)
        self.setResizeMode(QListWidget.Adjust)
        self.setMovement(QListWidget.Static)
        self.setSpacing(8)
        # Use 16:9 aspect ratio (landscape) for thumbnails
        self.setIconSize(QSize(256, 144))  # 16:9 ratio starting size
        self.setWordWrap(True)
        self.setUniformItemSizes(False)

    def set_thumb_size(self, px: int):
        """Set thumbnail size maintaining 16:9 aspect ratio."""
        #changed thumb size --- 
        # Maintain 16:9 aspect ratio (width:height)
        height = int(px * 9 / 16)
        self.setIconSize(QSize(px, height))
