"""
Preview pane widget for displaying asset previews and metadata.
"""

from typing import Optional
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QTextEdit, QSizePolicy
)


class PreviewPane(QWidget):
    """Widget for displaying asset preview and metadata."""
    
    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        """Setup the preview pane UI."""
        layout = QVBoxLayout(self)
        
        self.preview = QLabel("Preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.preview.setMinimumHeight(200)
        
        self.meta = QTextEdit()
        self.meta.setReadOnly(True)
        
        layout.addWidget(self.preview, 3)
        layout.addWidget(QLabel("Metadata"))
        layout.addWidget(self.meta, 2)

    def show_preview(self, pix: Optional[QPixmap]):
        """Display a preview pixmap."""
        if pix is None:
            self.preview.setText("No preview")
            self.preview.setPixmap(QPixmap())
            return
        self.preview.setPixmap(pix.scaled(
            self.preview.size(), 
            Qt.KeepAspectRatio, 
            Qt.SmoothTransformation
        ))

    def set_metadata(self, meta_text: str):
        """Set the metadata text."""
        self.meta.setPlainText(meta_text)

    def resizeEvent(self, e):
        """Handle resize events to maintain preview scaling."""
        super().resizeEvent(e)
        pix = self.preview.pixmap()
        if pix:
            self.preview.setPixmap(pix.scaled(
                self.preview.size(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
