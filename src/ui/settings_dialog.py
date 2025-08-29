"""
Settings dialog for configuring the Asset Browser.
"""

import os
from typing import Dict, Any
from PySide6.QtCore import Qt, QThreadPool
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget,
    QGroupBox, QFormLayout, QCheckBox, QSpinBox, QComboBox,
    QPushButton, QLabel, QDialogButtonBox, QMessageBox
)

try:
    import OpenImageIO as oiio
except ImportError:
    oiio = None


class SettingsDialog(QDialog):
    """Settings dialog for the Asset Browser."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_browser = parent
        self.setWindowTitle("Asset Browser Settings")
        self.setModal(True)
        self.resize(500, 400)
        self._setup_ui()

    def _setup_ui(self):
        """Setup the settings dialog UI."""
        layout = QVBoxLayout(self)
        
        # Tab widget for organized settings
        tabs = QTabWidget()
        layout.addWidget(tabs)
        
        # Create tabs
        tabs.addTab(self._create_general_tab(), "General")
        tabs.addTab(self._create_performance_tab(), "Performance")
        tabs.addTab(self._create_formats_tab(), "File Formats")
        tabs.addTab(self._create_advanced_tab(), "Advanced")
        
        # Dialog buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.RestoreDefaults
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        buttons.button(QDialogButtonBox.RestoreDefaults).clicked.connect(self._restore_defaults)
        layout.addWidget(buttons)
        
        self._update_cache_info()

    def _create_general_tab(self) -> QWidget:
        """Create the general settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Thumbnail Settings Group
        thumb_group = QGroupBox("Thumbnail Settings")
        thumb_layout = QFormLayout(thumb_group)
        
        self.thumb_size_spin = QSpinBox()
        self.thumb_size_spin.setRange(64, 1024)
        self.thumb_size_spin.setValue(256)
        self.thumb_size_spin.setSuffix(" px")
        thumb_layout.addRow("Default Thumbnail Size:", self.thumb_size_spin)
        
        self.cache_enabled = QCheckBox("Enable thumbnail cache")
        self.cache_enabled.setChecked(True)
        thumb_layout.addRow("Cache:", self.cache_enabled)
        
        layout.addWidget(thumb_group)
        
        # Display Settings Group
        display_group = QGroupBox("Display Settings")
        display_layout = QFormLayout(display_group)
        
        self.grid_spacing = QSpinBox()
        self.grid_spacing.setRange(0, 50)
        self.grid_spacing.setValue(8)
        self.grid_spacing.setSuffix(" px")
        display_layout.addRow("Grid Spacing:", self.grid_spacing)
        
        self.show_metadata = QCheckBox("Show metadata panel")
        self.show_metadata.setChecked(True)
        display_layout.addRow("Metadata:", self.show_metadata)
        
        self.show_tree_view = QCheckBox("Show folder tree")
        self.show_tree_view.setChecked(True)
        display_layout.addRow("Folder Tree:", self.show_tree_view)
        
        layout.addWidget(display_group)
        
        return tab

    def _create_performance_tab(self) -> QWidget:
        """Create the performance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Threading Group
        thread_group = QGroupBox("Threading & Performance")
        thread_layout = QFormLayout(thread_group)
        
        self.thread_count = QSpinBox()
        self.thread_count.setRange(1, 16)
        self.thread_count.setValue(QThreadPool.globalInstance().maxThreadCount())
        thread_layout.addRow("Max Thread Count:", self.thread_count)
        
        self.preload_thumbnails = QCheckBox("Preload thumbnails")
        self.preload_thumbnails.setChecked(True)
        thread_layout.addRow("Preloading:", self.preload_thumbnails)
        
        layout.addWidget(thread_group)
        
        # Memory Management Group
        memory_group = QGroupBox("Memory Management")
        memory_layout = QFormLayout(memory_group)
        
        self.max_cache_size = QSpinBox()
        self.max_cache_size.setRange(10, 1000)
        self.max_cache_size.setValue(100)
        self.max_cache_size.setSuffix(" MB")
        memory_layout.addRow("Max Cache Size:", self.max_cache_size)
        
        self.auto_clear_cache = QCheckBox("Auto-clear cache on exit")
        self.auto_clear_cache.setChecked(False)
        memory_layout.addRow("Auto-clear:", self.auto_clear_cache)
        
        layout.addWidget(memory_group)
        
        return tab

    def _create_formats_tab(self) -> QWidget:
        """Create the file formats settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Image Formats Group
        image_group = QGroupBox("Supported Image Formats")
        image_layout = QVBoxLayout(image_group)
        
        self.format_checkboxes = {}
        image_formats = [".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".gif", 
                        ".exr", ".hdr", ".dpx", ".psd", ".svg", ".jp2"]
        
        # Create checkboxes in a grid layout
        format_grid = QWidget()
        format_grid_layout = QHBoxLayout(format_grid)
        
        left_col = QVBoxLayout()
        right_col = QVBoxLayout()
        
        for i, fmt in enumerate(image_formats):
            checkbox = QCheckBox(fmt.upper())
            checkbox.setChecked(True)
            self.format_checkboxes[fmt] = checkbox
            
            if i < len(image_formats) // 2:
                left_col.addWidget(checkbox)
            else:
                right_col.addWidget(checkbox)
        
        format_grid_layout.addLayout(left_col)
        format_grid_layout.addLayout(right_col)
        image_layout.addWidget(format_grid)
        
        layout.addWidget(image_group)
        
        # Video Formats Group
        video_group = QGroupBox("Supported Video Formats")
        video_layout = QVBoxLayout(video_group)
        
        video_formats = [".mp4", ".mov", ".avi", ".mkv", ".webm"]
        video_grid = QWidget()
        video_grid_layout = QHBoxLayout(video_grid)
        
        for fmt in video_formats:
            checkbox = QCheckBox(fmt.upper())
            checkbox.setChecked(True)
            self.format_checkboxes[fmt] = checkbox
            video_grid_layout.addWidget(checkbox)
        
        video_layout.addWidget(video_grid)
        layout.addWidget(video_group)
        
        return tab

    def _create_advanced_tab(self) -> QWidget:
        """Create the advanced settings tab."""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        
        # Logging Group
        logging_group = QGroupBox("Logging & Debug")
        logging_layout = QFormLayout(logging_group)
        
        self.log_level = QComboBox()
        self.log_level.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        self.log_level.setCurrentText("INFO")
        logging_layout.addRow("Log Level:", self.log_level)
        
        self.enable_debug = QCheckBox("Enable debug output")
        self.enable_debug.setChecked(False)
        logging_layout.addRow("Debug Mode:", self.enable_debug)
        
        layout.addWidget(logging_group)
        
        # OpenImageIO Group
        oiio_group = QGroupBox("OpenImageIO Settings")
        oiio_layout = QFormLayout(oiio_group)
        
        self.use_oiio = QCheckBox("Use OpenImageIO for image reading")
        self.use_oiio.setChecked(oiio is not None)
        self.use_oiio.setEnabled(oiio is not None)
        oiio_layout.addRow("OIIO Support:", self.use_oiio)
        
        self.hdr_tonemap = QCheckBox("Enable HDR tonemapping")
        self.hdr_tonemap.setChecked(True)
        oiio_layout.addRow("HDR Tonemap:", self.hdr_tonemap)
        
        layout.addWidget(oiio_group)
        
        # Cache Management Group
        cache_group = QGroupBox("Cache Management")
        cache_layout = QVBoxLayout(cache_group)
        
        cache_buttons_layout = QHBoxLayout()
        
        clear_current_btn = QPushButton("Clear Current Folder Cache")
        clear_current_btn.clicked.connect(self._clear_current_cache)
        cache_buttons_layout.addWidget(clear_current_btn)
        
        clear_all_btn = QPushButton("Clear All Caches")
        clear_all_btn.clicked.connect(self._clear_all_caches)
        cache_buttons_layout.addWidget(clear_all_btn)
        
        cache_layout.addLayout(cache_buttons_layout)
        
        # Cache info
        self.cache_info = QLabel("Cache information will be displayed here")
        self.cache_info.setWordWrap(True)
        cache_layout.addWidget(self.cache_info)
        
        layout.addWidget(cache_group)
        
        return tab

    def _clear_current_cache(self):
        """Clear cache for current folder."""
        if self.parent_browser:
            self.parent_browser._clear_cache_current()
            self._update_cache_info()
    
    def _clear_all_caches(self):
        """Clear all caches after confirmation."""
        reply = QMessageBox.question(
            self, "Clear All Caches", 
            "This will clear all thumbnail caches for all projects. Continue?",
            QMessageBox.Yes | QMessageBox.No
        )
        if reply == QMessageBox.Yes:
            if self.parent_browser:
                self.parent_browser._clear_all_cache()
                self._update_cache_info()
            else:
                QMessageBox.warning(self, "Error", "Cannot access main browser window.")
    
    def _restore_defaults(self):
        """Reset all settings to defaults."""
        self.thumb_size_spin.setValue(256)
        self.cache_enabled.setChecked(True)
        self.grid_spacing.setValue(8)
        self.show_metadata.setChecked(True)
        self.show_tree_view.setChecked(True)
        self.thread_count.setValue(QThreadPool.globalInstance().maxThreadCount())
        self.preload_thumbnails.setChecked(True)
        self.max_cache_size.setValue(100)
        self.auto_clear_cache.setChecked(False)
        self.log_level.setCurrentText("INFO")
        self.enable_debug.setChecked(False)
        self.use_oiio.setChecked(oiio is not None)
        self.hdr_tonemap.setChecked(True)
        
        # Reset format checkboxes
        for checkbox in self.format_checkboxes.values():
            checkbox.setChecked(True)
    
    def _update_cache_info(self):
        """Update cache information display."""
        if self.parent_browser:
            cache_root = self.parent_browser._cache_root_for_dir(self.parent_browser.current_dir)
            if os.path.exists(cache_root):
                try:
                    # Calculate cache size
                    total_size = 0
                    file_count = 0
                    for root, dirs, files in os.walk(cache_root):
                        for file in files:
                            file_path = os.path.join(root, file)
                            total_size += os.path.getsize(file_path)
                            file_count += 1
                    
                    size_mb = total_size / (1024 * 1024)
                    
                    # Show project cache info if available
                    if self.parent_browser.current_project:
                        project_name = os.path.basename(self.parent_browser.current_project)
                        self.cache_info.setText(
                            f"Project '{project_name}' cache:\n"
                            f"{file_count} files, {size_mb:.1f} MB\n"
                            f"Location: {cache_root}"
                        )
                    else:
                        self.cache_info.setText(
                            f"Current folder cache:\n"
                            f"{file_count} files, {size_mb:.1f} MB\n"
                            f"Location: {cache_root}"
                        )
                except Exception as e:
                    self.cache_info.setText(f"Error reading cache info: {e}")
            else:
                if self.parent_browser.current_project:
                    project_name = os.path.basename(self.parent_browser.current_project)
                    self.cache_info.setText(
                        f"No cache yet for project '{project_name}'\n"
                        f"Will be created at: {cache_root}"
                    )
                else:
                    self.cache_info.setText("No cache folder in current directory")
        else:
            self.cache_info.setText("Cache information not available")
    
    def get_settings(self) -> Dict[str, Any]:
        """Return a dictionary of all current settings."""
        settings = {
            'thumb_size': self.thumb_size_spin.value(),
            'cache_enabled': self.cache_enabled.isChecked(),
            'grid_spacing': self.grid_spacing.value(),
            'show_metadata': self.show_metadata.isChecked(),
            'show_tree_view': self.show_tree_view.isChecked(),
            'thread_count': self.thread_count.value(),
            'preload_thumbnails': self.preload_thumbnails.isChecked(),
            'max_cache_size': self.max_cache_size.value(),
            'auto_clear_cache': self.auto_clear_cache.isChecked(),
            'log_level': self.log_level.currentText(),
            'enable_debug': self.enable_debug.isChecked(),
            'use_oiio': self.use_oiio.isChecked(),
            'hdr_tonemap': self.hdr_tonemap.isChecked(),
            'supported_formats': {fmt: cb.isChecked() for fmt, cb in self.format_checkboxes.items()}
        }
        return settings
