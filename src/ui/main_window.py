"""
Main window for the Asset Browser application.
"""

import os
import re
import shutil
from typing import List, Optional
from PySide6.QtCore import Qt, QDir, QUrl, QThreadPool, QSize
from PySide6.QtGui import QAction, QIcon, QPixmap, QDesktopServices
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QToolBar, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QLabel, QListWidgetItem, QSlider, QSplitter, QTreeView,
    QFileSystemModel, QMessageBox, QComboBox, QMenuBar, QMenu, QStackedWidget,
    QPushButton
)

from .thumb_list import ThumbList
from .list_view import AssetListView
from .preview_pane import PreviewPane
from .settings_dialog import SettingsDialog
from ..config.config_manager import ConfigManager
from ..thumbnail.cache import CacheManager
from ..thumbnail.thumb_task import ThumbTask
from ..utils.file_utils import is_supported_asset
from ..utils.logging_config import LOGGER
from ..config import constants


class MainWindow(QMainWindow):
    """Main window for the Asset Browser application."""
    
    def __init__(self, start_dir: Optional[str] = None):
        super().__init__()
        self.setWindowTitle("Asset Browser — Python + OpenCV + OIIO")
        self.resize(1400, 900)

        # Initialize configuration manager and load settings
        self.config_manager = ConfigManager()
        self.settings = self.config_manager.load_settings()

        # Initialize project management
        self.projects_list = self.settings.get('projects', [])
        
        self.thread_pool = QThreadPool.globalInstance()
        self.thumb_px = self.settings['thumb_size']

        self.current_project = None
        self.current_dir = start_dir or QDir.homePath()
        
        # View mode: 'grid' or 'list'
        self.view_mode = self.settings.get('view_mode', 'grid')

        # Apply thread count setting
        self.thread_pool.setMaxThreadCount(self.settings['thread_count'])

        self._setup_ui()
        self._apply_startup_settings()
        self._refresh_thumbs()

    def _setup_ui(self):
        """Setup the main window UI."""
        # Setup file system model
        self.fs_model = QFileSystemModel()
        self.fs_model.setRootPath("")
        self.fs_model.setFilter(QDir.AllDirs | QDir.NoDotAndDotDot)
        
        # Setup tree view
        self.tree = QTreeView()
        self.tree.setModel(self.fs_model)
        self.tree.setRootIndex(self.fs_model.index(self.current_dir))
        self.tree.clicked.connect(self._on_tree_clicked)

        # Setup thumbnail list (grid view)
        self.list = ThumbList()
        self.list.itemSelectionChanged.connect(self._on_selection_changed)
        self.list.itemDoubleClicked.connect(self._open_selected)

        # Setup asset list view (list view)
        self.asset_list_view = AssetListView()
        self.asset_list_view.selectionModel().selectionChanged.connect(self._on_list_selection_changed)
        self.asset_list_view.doubleClicked.connect(self._on_list_double_clicked)

        # Create stacked widget to switch between views
        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.list)  # Index 0: Grid view
        self.view_stack.addWidget(self.asset_list_view)  # Index 1: List view

        # Setup preview pane
        self.preview = PreviewPane()

        # Setup toolbar
        self._setup_toolbar()

        # Create menu bar
        self._create_menu_bar()

        # Populate project dropdown
        self._populate_projects_dropdown()

        # Setup main layout
        splitter = QSplitter()
        splitter.addWidget(self.tree)
        splitter.addWidget(self.view_stack)  # Use stacked widget instead of list
        splitter.addWidget(self.preview)
        splitter.setSizes([250, 800, 350])

        central = QWidget()
        v = QVBoxLayout(central)
        v.addWidget(splitter)
        self.setCentralWidget(central)

        # Add status bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")

    def _setup_toolbar(self):
        """Setup the main toolbar."""
        tb = QToolBar("Main")
        self.addToolBar(tb)

        tb.addWidget(QLabel("Project:"))
        self.project_combo = QComboBox()
        self.project_combo.setEditable(False)
        self.project_combo.setMinimumWidth(200)
        self.project_combo.setToolTip("Select a project from the dropdown")
        self.project_combo.currentTextChanged.connect(self._on_project_changed)
        tb.addWidget(self.project_combo)

        tb.addSeparator()
        tb.addWidget(QLabel("Search:"))
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter by filename (regex ok)")
        self.search.textChanged.connect(self._refresh_thumbs)
        tb.addWidget(self.search)

        tb.addSeparator()
        tb.addWidget(QLabel("View:"))
        
        # Grid view button
        self.grid_view_btn = QPushButton("Grid")
        self.grid_view_btn.setCheckable(True)
        self.grid_view_btn.setToolTip("Switch to grid view")
        self.grid_view_btn.clicked.connect(lambda: self._set_view_mode('grid'))
        tb.addWidget(self.grid_view_btn)
        
        # List view button
        self.list_view_btn = QPushButton("List")
        self.list_view_btn.setCheckable(True)
        self.list_view_btn.setToolTip("Switch to list view")
        self.list_view_btn.clicked.connect(lambda: self._set_view_mode('list'))
        tb.addWidget(self.list_view_btn)

        tb.addSeparator()
        tb.addWidget(QLabel("Thumb Size:"))
        self.size_slider = QSlider(Qt.Horizontal)
        self.size_slider.setRange(128, 512)
        self.size_slider.setValue(self.thumb_px)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        tb.addWidget(self.size_slider)
        
        # Set initial view mode
        self._set_view_mode(self.view_mode)

    def _create_menu_bar(self):
        """Create and setup the application menu bar."""
        menubar = self.menuBar()
        
        # File Menu
        file_menu = menubar.addMenu("&File")
        
        # New Project action
        new_project_action = QAction("&New Project...", self)
        new_project_action.setShortcut("Ctrl+N")
        new_project_action.setStatusTip("Add a new project to the project list")
        new_project_action.triggered.connect(self._new_project)
        file_menu.addAction(new_project_action)
        
        file_menu.addSeparator()
        
        # Open Folder action
        open_folder_action = QAction("&Open Folder...", self)
        open_folder_action.setShortcut("Ctrl+O")
        open_folder_action.setStatusTip("Open a folder to browse assets")
        open_folder_action.triggered.connect(self._choose_folder)
        file_menu.addAction(open_folder_action)
        
        file_menu.addSeparator()
        
        # Recent folders submenu (placeholder for future implementation)
        recent_menu = file_menu.addMenu("&Recent Folders")
        recent_menu.addAction("(No recent folders)")
        recent_menu.setEnabled(False)
        
        file_menu.addSeparator()
        
        # Exit action
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Edit Menu
        edit_menu = menubar.addMenu("&Edit")
        
        # Search action
        search_action = QAction("&Find...", self)
        search_action.setShortcut("Ctrl+F")
        search_action.setStatusTip("Focus on search field")
        search_action.triggered.connect(lambda: self.search.setFocus())
        edit_menu.addAction(search_action)
        
        edit_menu.addSeparator()
        
        # Settings action
        settings_action = QAction("&Preferences...", self)
        settings_action.setShortcut("Ctrl+,")
        settings_action.setStatusTip("Open application settings")
        settings_action.triggered.connect(self._open_settings)
        edit_menu.addAction(settings_action)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        
        # Refresh action
        refresh_action = QAction("&Refresh", self)
        refresh_action.setShortcut("F5")
        refresh_action.setStatusTip("Refresh thumbnail view")
        refresh_action.triggered.connect(self._refresh_thumbs)
        view_menu.addAction(refresh_action)
        
        view_menu.addSeparator()
        
        # View mode actions
        grid_view_action = QAction("&Grid View", self)
        grid_view_action.setCheckable(True)
        grid_view_action.setChecked(self.view_mode == 'grid')
        grid_view_action.setShortcut("Ctrl+1")
        grid_view_action.setStatusTip("Switch to grid view")
        grid_view_action.triggered.connect(lambda: self._set_view_mode('grid'))
        view_menu.addAction(grid_view_action)
        
        list_view_action = QAction("&List View", self)
        list_view_action.setCheckable(True)
        list_view_action.setChecked(self.view_mode == 'list')
        list_view_action.setShortcut("Ctrl+2")
        list_view_action.setStatusTip("Switch to list view")
        list_view_action.triggered.connect(lambda: self._set_view_mode('list'))
        view_menu.addAction(list_view_action)
        
        # Store references for updating
        self.grid_view_action = grid_view_action
        self.list_view_action = list_view_action
        
        view_menu.addSeparator()
        
        # Toggle metadata panel
        toggle_metadata_action = QAction("Show &Metadata Panel", self)
        toggle_metadata_action.setCheckable(True)
        toggle_metadata_action.setChecked(self.settings['show_metadata'])
        toggle_metadata_action.setStatusTip("Toggle metadata panel visibility")
        toggle_metadata_action.triggered.connect(self._toggle_metadata_panel)
        view_menu.addAction(toggle_metadata_action)
        
        # Toggle tree view
        toggle_tree_action = QAction("Show &Tree View", self)
        toggle_tree_action.setCheckable(True)
        toggle_tree_action.setChecked(self.settings['show_tree_view'])
        toggle_tree_action.setStatusTip("Toggle folder tree view visibility")
        toggle_tree_action.triggered.connect(self._toggle_tree_view)
        view_menu.addAction(toggle_tree_action)
        
        # Store references for later updates
        self.toggle_metadata_action = toggle_metadata_action
        self.toggle_tree_action = toggle_tree_action
        
        # Tools Menu
        tools_menu = menubar.addMenu("&Tools")
        
        # Clear cache action
        clear_cache_action = QAction("&Clear Cache", self)
        clear_cache_action.setStatusTip("Delete thumbnail cache for current folder")
        clear_cache_action.triggered.connect(self._clear_cache_current)
        tools_menu.addAction(clear_cache_action)
        
        # Clear all cache action
        clear_all_cache_action = QAction("Clear &All Cache", self)
        clear_all_cache_action.setStatusTip("Delete all thumbnail cache files")
        clear_all_cache_action.triggered.connect(self._clear_all_cache)
        tools_menu.addAction(clear_all_cache_action)
        
        tools_menu.addSeparator()
        
        # Open cache folder
        open_cache_action = QAction("Open Cache &Folder", self)
        open_cache_action.setStatusTip("Open the thumbnail cache directory")
        open_cache_action.triggered.connect(self._open_cache_folder)
        tools_menu.addAction(open_cache_action)
        
        # Help Menu
        help_menu = menubar.addMenu("&Help")
        
        # Keyboard shortcuts
        shortcuts_action = QAction("&Keyboard Shortcuts", self)
        shortcuts_action.setShortcut("F1")
        shortcuts_action.setStatusTip("Show keyboard shortcuts")
        shortcuts_action.triggered.connect(self._show_shortcuts)
        help_menu.addAction(shortcuts_action)
        
        help_menu.addSeparator()
        
        # About action
        about_action = QAction("&About Asset Browser", self)
        about_action.setStatusTip("About this application")
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _apply_startup_settings(self):
        """Apply settings loaded from configuration at startup."""
        # Apply grid spacing from settings
        self.list.setSpacing(self.settings['grid_spacing'])
        
        # Apply thumbnail size to both views
        if self.view_mode == 'grid':
            self.list.set_thumb_size(self.thumb_px)
        else:
            self.asset_list_view.set_thumbnail_size(self.thumb_px)
        
        # Apply metadata panel visibility
        self.preview.setVisible(self.settings['show_metadata'])
        
        # Apply tree view visibility
        self.tree.setVisible(self.settings['show_tree_view'])
        
        # Apply view mode
        self._set_view_mode(self.view_mode)
        
        LOGGER.info(f"Applied startup settings: thumb_size={self.settings['thumb_size']}, "
                   f"grid_spacing={self.settings['grid_spacing']}, "
                   f"show_metadata={self.settings['show_metadata']}, "
                   f"view_mode={self.view_mode}")

    def _populate_projects_dropdown(self):
        """Populate the project dropdown with available projects."""
        self.project_combo.clear()
        self.project_combo.addItem("(No project selected)")
        
        # Remove non-existent projects
        valid_projects = [p for p in self.projects_list if os.path.exists(p)]
        if len(valid_projects) != len(self.projects_list):
            self.projects_list = valid_projects
            self.settings['projects'] = self.projects_list
            self.config_manager.save_settings(self.settings)
        
        # Add valid projects to dropdown
        for project_path in valid_projects:
            project_name = os.path.basename(project_path)
            self.project_combo.addItem(project_name, project_path)

    def _on_tree_clicked(self, index):
        """Handle tree view item clicks."""
        path = self.fs_model.filePath(index)
        if self.current_project and not path.startswith(self.current_project):
            return
        self.current_dir = path
        self._refresh_thumbs()

    def _on_project_changed(self, project_name):
        """Handle project selection change."""
        if project_name == "(No project selected)" or not project_name:
            self.current_project = None
            self.current_dir = QDir.homePath()
        else:
            # Find the project path by name
            for i in range(1, self.project_combo.count()):  # Skip first item
                if self.project_combo.itemText(i) == project_name:
                    project_path = self.project_combo.itemData(i)
                    if project_path and os.path.exists(project_path):
                        self.current_project = project_path
                        self.current_dir = project_path
                        break
        
        # Update tree view and refresh
        self.tree.setRootIndex(self.fs_model.index(self.current_dir))
        self._refresh_thumbs()

    def _set_view_mode(self, mode: str):
        """Switch between grid and list view modes."""
        self.view_mode = mode
        
        # Update button states
        self.grid_view_btn.setChecked(mode == 'grid')
        self.list_view_btn.setChecked(mode == 'list')
        
        # Update menu actions
        if hasattr(self, 'grid_view_action'):
            self.grid_view_action.setChecked(mode == 'grid')
        if hasattr(self, 'list_view_action'):
            self.list_view_action.setChecked(mode == 'list')
        
        # Switch view
        if mode == 'grid':
            self.view_stack.setCurrentIndex(0)
        else:
            self.view_stack.setCurrentIndex(1)
        
        # Save view mode to settings
        self.settings['view_mode'] = mode
        self.config_manager.save_settings(self.settings)
        
        # Refresh current view
        self._refresh_thumbs()

    def _on_list_selection_changed(self, selected, deselected):
        """Handle list view selection changes."""
        indexes = self.asset_list_view.selectionModel().selectedRows()
        if not indexes:
            self.preview.show_preview(None)
            self.preview.set_metadata("")
            return
        
        index = indexes[0]
        path = self.asset_list_view.model.data(index, Qt.UserRole)
        metadata = self.asset_list_view.model.data(index, Qt.UserRole + 1)
        
        # Get thumbnail from the model
        thumbnail_icon = self.asset_list_view.model.data(self.asset_list_view.model.index(index.row(), 0), Qt.DecorationRole)
        if thumbnail_icon:
            pixmap = thumbnail_icon.pixmap(self.thumb_px, self.thumb_px)
            self.preview.show_preview(pixmap)
        else:
            self.preview.show_preview(None)
        
        self.preview.set_metadata(metadata or "")

    def _on_list_double_clicked(self, index):
        """Handle list view double-click."""
        path = self.asset_list_view.model.data(index, Qt.UserRole)
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _on_size_changed(self, v: int):
        """Handle thumbnail size slider changes."""
        self.thumb_px = int(v)
        if self.view_mode == 'grid':
            self.list.set_thumb_size(self.thumb_px)
        else:
            self.asset_list_view.set_thumbnail_size(self.thumb_px)

    def _on_selection_changed(self):
        """Handle thumbnail list selection changes."""
        items = self.list.selectedItems()
        if not items:
            self.preview.show_preview(None)
            self.preview.set_metadata("")
            return
        item = items[0]
        pix = item.icon().pixmap(self.thumb_px, self.thumb_px)
        self.preview.show_preview(pix)
        self.preview.set_metadata(item.data(Qt.UserRole) or "")

    def _open_selected(self, item: QListWidgetItem):
        """Open selected item with system default application."""
        path = item.data(Qt.UserRole + 1)
        if path and os.path.exists(path):
            QDesktopServices.openUrl(QUrl.fromLocalFile(path))

    def _choose_folder(self):
        """Open folder chooser dialog."""
        dir_ = QFileDialog.getExistingDirectory(self, "Choose Folder", self.current_dir)
        if dir_:
            if self.current_project and not dir_.startswith(self.current_project):
                QMessageBox.warning(self, "Invalid Folder", 
                                  "Selected folder is outside the current project.")
                return
            self.current_dir = dir_
            self.tree.setRootIndex(self.fs_model.index(self.current_dir))
            self._refresh_thumbs()

    def _new_project(self):
        """Add a new project to the project list."""
        dir_ = QFileDialog.getExistingDirectory(self, "Select New Project Folder", QDir.homePath())
        if dir_:
            # Check if project already exists
            if dir_ not in self.projects_list:
                self.projects_list.append(dir_)
                self.settings['projects'] = self.projects_list
                self.config_manager.save_settings(self.settings)
                self._populate_projects_dropdown()
                # Select the newly added project
                project_name = os.path.basename(dir_)
                index = self.project_combo.findText(project_name)
                if index >= 0:
                    self.project_combo.setCurrentIndex(index)
            else:
                QMessageBox.information(self, "Project Exists", 
                                      "This project is already in the list.")

    def _list_assets(self) -> List[str]:
        """List all supported assets in the current directory."""
        root = self.current_dir
        if not os.path.isdir(root):
            return []
        names = []
        for name in os.listdir(root):
            p = os.path.join(root, name)
            if os.path.isdir(p):
                continue
            if is_supported_asset(p):
                names.append(p)
        
        # Apply search filter
        q = self.search.text().strip()
        if q:
            try:
                rx = re.compile(q, re.IGNORECASE)
                names = [n for n in names if rx.search(os.path.basename(n))]
            except Exception:
                ql = q.lower()
                names = [n for n in names if ql in os.path.basename(n).lower()]
        
        # Sort by modification time (newest first)
        names.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return names

    def _cache_root_for_dir(self, folder: str) -> str:
        """Get cache root directory for the given folder."""
        return CacheManager.generate_cache_root(self.current_project, folder)

    def _refresh_thumbs(self):
        """Refresh the thumbnail list."""
        if self.view_mode == 'grid':
            self._refresh_grid_view()
        else:
            self._refresh_list_view()
    
    def _refresh_grid_view(self):
        """Refresh the grid view."""
        self.list.clear()
        assets = self._list_assets()
        LOGGER.info(f"Refresh grid view: dir={self.current_dir}, count={len(assets)}")
        cache_root = self._cache_root_for_dir(self.current_dir)
        
        for path in assets:
            LOGGER.debug(f"Schedule thumbnail: {path}")
            item = QListWidgetItem(os.path.basename(path))
            # Set item size to match 16:9 aspect ratio with some padding
            thumb_height = int(self.thumb_px * 9 / 16)
            item.setSizeHint(QSize(self.thumb_px + 16, thumb_height + 36))
            item.setData(Qt.UserRole + 1, path)
            placeholder = QPixmap(self.thumb_px, thumb_height)
            placeholder.fill(Qt.black)
            item.setIcon(QIcon(placeholder))
            self.list.addItem(item)

            task = ThumbTask(path, self.thumb_px, cache_root)
            task.signals.done.connect(self._on_thumb_ready)
            self.thread_pool.start(task)
    
    def _refresh_list_view(self):
        """Refresh the list view."""
        self.asset_list_view.clear_assets()
        assets = self._list_assets()
        LOGGER.info(f"Refresh list view: dir={self.current_dir}, count={len(assets)}")
        cache_root = self._cache_root_for_dir(self.current_dir)
        
        for path in assets:
            LOGGER.debug(f"Add asset to list view: {path}")
            self.asset_list_view.add_asset(path)

            task = ThumbTask(path, self.thumb_px, cache_root)
            task.signals.done.connect(self._on_list_thumb_ready)
            self.thread_pool.start(task)

    def _on_list_thumb_ready(self, result):
        """Handle thumbnail generation completion for list view."""
        self.asset_list_view.update_asset_thumbnail(result.path, result.pixmap, result.meta_text)
        
        # Update preview if this item is currently selected
        indexes = self.asset_list_view.selectionModel().selectedRows()
        if indexes:
            index = indexes[0]
            selected_path = self.asset_list_view.model.data(index, Qt.UserRole)
            if selected_path == result.path:
                self.preview.show_preview(result.pixmap)
                self.preview.set_metadata(result.meta_text)

    def _on_thumb_ready(self, result):
        """Handle thumbnail generation completion."""
        for i in range(self.list.count()):
            it = self.list.item(i)
            if it.data(Qt.UserRole + 1) == result.path:
                if result.pixmap:
                    it.setIcon(QIcon(result.pixmap))
                else:
                    placeholder = QPixmap(self.thumb_px, int(self.thumb_px * 9 / 16))
                    placeholder.fill(Qt.darkGray)
                    it.setIcon(QIcon(placeholder))
                it.setData(Qt.UserRole, result.meta_text)
                if it.isSelected():
                    self.preview.show_preview(result.pixmap)
                    self.preview.set_metadata(result.meta_text)
                LOGGER.debug(f"Updated UI item for {result.path}")
                break

    def _open_settings(self):
        """Open the settings dialog."""
        dialog = SettingsDialog(self)
        
        # Load current settings into dialog
        dialog.thumb_size_spin.setValue(self.settings['thumb_size'])
        dialog.grid_spacing.setValue(self.settings['grid_spacing'])
        dialog.cache_enabled.setChecked(self.settings['cache_enabled'])
        dialog.show_metadata.setChecked(self.settings['show_metadata'])
        dialog.show_tree_view.setChecked(self.settings['show_tree_view'])
        dialog.thread_count.setValue(self.settings['thread_count'])
        dialog.preload_thumbnails.setChecked(self.settings['preload_thumbnails'])
        dialog.max_cache_size.setValue(self.settings['max_cache_size'])
        dialog.auto_clear_cache.setChecked(self.settings['auto_clear_cache'])
        dialog.log_level.setCurrentText(self.settings['log_level'])
        dialog.enable_debug.setChecked(self.settings['enable_debug'])
        dialog.use_oiio.setChecked(self.settings['use_oiio'])
        dialog.hdr_tonemap.setChecked(self.settings['hdr_tonemap'])
        
        # Load format settings
        for fmt, checkbox in dialog.format_checkboxes.items():
            checkbox.setChecked(self.settings['supported_formats'].get(fmt, True))
        
        if dialog.exec() == SettingsDialog.Accepted:
            # Apply and save settings
            new_settings = dialog.get_settings()
            self._apply_settings(new_settings)
            self.settings = new_settings
            self.config_manager.save_settings(self.settings)
    
    def _apply_settings(self, settings):
        """Apply settings from the settings dialog."""
        # Apply thumbnail size
        if settings['thumb_size'] != self.thumb_px:
            self.thumb_px = settings['thumb_size']
            self.size_slider.setValue(self.thumb_px)
            if self.view_mode == 'grid':
                self.list.set_thumb_size(self.thumb_px)
            else:
                self.asset_list_view.set_thumbnail_size(self.thumb_px)
            self._refresh_thumbs()  # Regenerate thumbnails with new size
        
        # Apply grid spacing (only affects grid view)
        self.list.setSpacing(settings['grid_spacing'])
        
        # Apply thread count
        QThreadPool.globalInstance().setMaxThreadCount(settings['thread_count'])
        
        # Show/hide metadata panel
        self.preview.setVisible(settings['show_metadata'])
        
        # Show/hide tree view
        self.tree.setVisible(settings['show_tree_view'])
        
        # Update supported formats
        constants.SUPPORTED_IMAGE_EXTS = {
            fmt for fmt in constants.SUPPORTED_IMAGE_EXTS 
            if settings['supported_formats'].get(fmt, True)
        }
        constants.SUPPORTED_VIDEO_EXTS = {
            fmt for fmt in constants.SUPPORTED_VIDEO_EXTS 
            if settings['supported_formats'].get(fmt, True)
        }
        
        # Show success message in status bar
        self.status_bar.showMessage("Settings applied successfully", 3000)
        
        LOGGER.info(f"Applied settings: {settings}")

    def _toggle_metadata_panel(self, checked):
        """Toggle the metadata panel visibility."""
        self.preview.setVisible(checked)
        self.settings['show_metadata'] = checked
        self.config_manager.save_settings(self.settings)

    def _toggle_tree_view(self, checked):
        """Toggle the tree view visibility."""
        self.tree.setVisible(checked)
        self.settings['show_tree_view'] = checked
        self.config_manager.save_settings(self.settings)

    def _clear_cache_current(self):
        """Clear cache for current directory."""
        root = self._cache_root_for_dir(self.current_dir)
        if os.path.isdir(root):
            try:
                shutil.rmtree(root)
                LOGGER.info(f"Cleared cache: {root}")
                self._refresh_thumbs()
            except Exception as e:
                LOGGER.error(f"Failed to clear cache at {root}: {e}")
                QMessageBox.critical(self, "Clear Cache Failed", 
                                   f"Could not remove cache folder:\n{root}\n\n{e}")
        else:
            LOGGER.info(f"No cache folder to clear: {root}")
            QMessageBox.information(self, "Clear Cache", 
                                  "No cache folder found in current directory.")

    def _clear_all_cache(self):
        """Clear all thumbnail cache files."""
        try:
            cleared_count = 0
            
            # Clear project-based caches
            for project_path in self.projects_list:
                if os.path.exists(project_path):
                    project_name = os.path.basename(project_path)
                    cache_folder_name = f"{project_name}_AssetBrowserCache"
                    cache_root = os.path.join(project_path, cache_folder_name)
                    if os.path.exists(cache_root):
                        shutil.rmtree(cache_root)
                        cleared_count += 1
            
            # Also clear any old-style .assetbrowser_cache folders for backward compatibility
            for project_path in self.projects_list:
                if os.path.exists(project_path):
                    for root, dirs, files in os.walk(project_path):
                        if '.assetbrowser_cache' in dirs:
                            cache_path = os.path.join(root, '.assetbrowser_cache')
                            shutil.rmtree(cache_path)
                            cleared_count += 1
            
            if cleared_count > 0:
                QMessageBox.information(self, "Cache Cleared", 
                                      f"Cleared {cleared_count} cache directories.")
            else:
                QMessageBox.information(self, "Cache Cleared", 
                                      "No cache directories found to clear.")
            self._refresh_thumbs()
            
        except Exception as e:
            LOGGER.error(f"Error clearing all cache: {e}")
            QMessageBox.warning(self, "Error", f"Failed to clear all cache: {e}")

    def _open_cache_folder(self):
        """Open the thumbnail cache directory in file explorer."""
        cache_dir = self._cache_root_for_dir(self.current_dir)
        if os.path.exists(cache_dir):
            QDesktopServices.openUrl(QUrl.fromLocalFile(cache_dir))
        else:
            if self.current_project:
                project_name = os.path.basename(self.current_project)
                msg = (f"Cache folder for project '{project_name}' does not exist yet.\n\n"
                      f"It will be created at:\n{cache_dir}\n\n"
                      f"When you browse folders and generate thumbnails.")
            else:
                msg = f"Cache folder does not exist yet:\n{cache_dir}"
            QMessageBox.information(self, "Cache Folder", msg)

    def _show_shortcuts(self):
        """Show keyboard shortcuts dialog."""
        shortcuts_text = """
<h3>Keyboard Shortcuts</h3>
<table>
<tr><td><b>Ctrl+N</b></td><td>New Project</td></tr>
<tr><td><b>Ctrl+O</b></td><td>Open Folder</td></tr>
<tr><td><b>Ctrl+F</b></td><td>Focus Search Field</td></tr>
<tr><td><b>Ctrl+,</b></td><td>Open Settings</td></tr>
<tr><td><b>F5</b></td><td>Refresh View</td></tr>
<tr><td><b>F1</b></td><td>Show Shortcuts</td></tr>
<tr><td><b>Ctrl+Q</b></td><td>Exit Application</td></tr>
<tr><td><b>Double-click</b></td><td>Open File</td></tr>
</table>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Keyboard Shortcuts")
        msg.setTextFormat(Qt.RichText)
        msg.setText(shortcuts_text)
        msg.exec()

    def _show_about(self):
        """Show about dialog."""
        about_text = """
<h2>Asset Browser</h2>
<p><b>Version:</b> 1.0</p>
<p><b>Description:</b> A standalone asset browser built with Python, OpenCV, OpenImageIO, and PySide6</p>

<h3>Features:</h3>
<ul>
<li>Browse folders and view thumbnails in a grid</li>
<li>Support for many image formats (including EXR, TIFF, HDR)</li>
<li>Video thumbnail support (first frame)</li>
<li>Search filtering with regex support</li>
<li>Adjustable thumbnail size</li>
<li>Preview pane with metadata</li>
<li>Disk thumbnail cache</li>
<li>Light/dark theme awareness</li>
</ul>

<h3>Supported Formats:</h3>
<p><b>Images:</b> JPG, PNG, BMP, TIFF, GIF, EXR, HDR, DPX, PSD, SVG, JP2</p>
<p><b>Videos:</b> MP4, MOV, AVI, MKV, WEBM</p>

<p><b>Built with:</b> Python 3.10+, PySide6, OpenCV, OpenImageIO</p>
        """
        
        msg = QMessageBox(self)
        msg.setWindowTitle("About Asset Browser")
        msg.setTextFormat(Qt.RichText)
        msg.setText(about_text)
        msg.exec()
