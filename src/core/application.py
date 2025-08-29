"""
Main application class for the Asset Browser.
"""

import sys
from PySide6.QtWidgets import QApplication
from ..ui.main_window import MainWindow


class AssetBrowserApp:
    """Main application class for the Asset Browser."""
    
    def __init__(self):
        self.app = None
        self.main_window = None

    def run(self, start_dir=None):
        """Run the Asset Browser application."""
        self.app = QApplication(sys.argv)
        self.main_window = MainWindow(start_dir)
        self.main_window.show()
        return self.app.exec()
