"""
List view widget for displaying assets in a table format.
"""

import os
import re
from datetime import datetime
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, QSize, QAbstractTableModel, QModelIndex
from PySide6.QtGui import QPixmap, QIcon
from PySide6.QtWidgets import QTableView, QHeaderView, QAbstractItemView, QMenu, QStyledItemDelegate, QComboBox
from ..utils.file_utils import is_video


class StatusDelegate(QStyledItemDelegate):
    """Delegate for editing status column with combo box."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.status_options = ["None", "WIP", "Review", "Approved"]
    
    def createEditor(self, parent, option, index):
        """Create combo box editor for status column."""
        combo = QComboBox(parent)
        combo.addItems(self.status_options)
        return combo
    
    def setEditorData(self, editor, index):
        """Set current value in the editor."""
        current_value = index.model().data(index, Qt.DisplayRole)
        editor.setCurrentText(current_value)
    
    def setModelData(self, editor, model, index):
        """Set the data from editor back to model."""
        model.setData(index, editor.currentText(), Qt.EditRole)


class AssetTableModel(QAbstractTableModel):
    """Table model for displaying asset information in list view."""
    
    def __init__(self):
        super().__init__()
        self.assets = []  # List of asset dictionaries
        self.headers = ["Thumbnail", "Shot Names", "Frame Range", "Status", "Date Created"]
        self.sort_column = 0
        self.sort_order = Qt.AscendingOrder
        self.thumbnail_size = 256  # Default thumbnail size
        
    def set_thumbnail_size(self, size: int):
        """Set the thumbnail size for the model."""
        self.thumbnail_size = size
        
    def rowCount(self, parent=QModelIndex()):
        return len(self.assets)
    
    def columnCount(self, parent=QModelIndex()):
        return len(self.headers)
    
    def headerData(self, section, orientation, role):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self.headers[section]
        return None
    
    def data(self, index, role):
        if not index.isValid() or index.row() >= len(self.assets):
            return None
        
        asset = self.assets[index.row()]
        column = index.column()
        
        if role == Qt.DisplayRole:
            if column == 0:  # Thumbnail
                return ""  # No text for thumbnail column
            elif column == 1:  # Shot Name
                return asset.get('shot_name', '')
            elif column == 2:  # Frame Range
                return asset.get('frame_range', '')
            elif column == 3:  # Status
                return asset.get('status', '')
            elif column == 4:  # Date Created
                return asset.get('date_created', '')
        
        elif role == Qt.DecorationRole:
            if column == 0:  # Thumbnail
                return asset.get('thumbnail_icon')
        
        elif role == Qt.SizeHintRole:
            if column == 0:  # Thumbnail column
                # Return the expected size for thumbnail icons
                return QSize(self.thumbnail_size, self.thumbnail_size)
        
        elif role == Qt.UserRole:  # Store asset path
            return asset.get('path')
        
        elif role == Qt.UserRole + 1:  # Store metadata
            return asset.get('metadata', '')
        
        elif role == Qt.ToolTipRole:
            if column == 0:  # Thumbnail tooltip
                return f"File: {os.path.basename(asset.get('path', ''))}"
            elif column == 1:  # Shot Name tooltip
                return f"Shot: {asset.get('shot_name', 'Unknown')}"
            elif column == 2:  # Frame Range tooltip
                return f"Frame Range: {asset.get('frame_range', 'Unknown')}"
            elif column == 3:  # Status tooltip
                return f"Status: {asset.get('status', 'Unknown')} (Double-click to edit)"
            elif column == 4:  # Date Created tooltip
                return f"Created: {asset.get('date_created', 'Unknown')}"
        
        elif role == Qt.BackgroundRole:
            if column == 3:  # Status column background color
                status = asset.get('status', '')
                return self._get_status_background_color(status)
        
        return None
    
    def flags(self, index):
        """Return item flags for the given index."""
        if not index.isValid():
            return Qt.ItemIsEnabled
        
        flags = super().flags(index)
        
        # Make status column (column 3) editable
        if index.column() == 3:
            flags |= Qt.ItemIsEditable
        
        return flags
    
    def setData(self, index, value, role=Qt.EditRole):
        """Set data for the given index."""
        if not index.isValid() or role != Qt.EditRole:
            return False
        
        row = index.row()
        column = index.column()
        
        if 0 <= row < len(self.assets):
            if column == 3:  # Status column
                # Validate status value
                valid_statuses = ["None", "WIP", "Review", "Approved"]
                if value in valid_statuses:
                    self.assets[row]['status'] = value
                    self.dataChanged.emit(index, index)
                    return True
        
        return False
    
    def sort(self, column, order):
        """Sort the model by the given column and order."""
        self.sort_column = column
        self.sort_order = order
        
        def sort_key(asset):
            if column == 0:  # Thumbnail - sort by filename
                return os.path.basename(asset.get('path', ''))
            elif column == 1:  # Shot Name
                return asset.get('shot_name', '')
            elif column == 2:  # Frame Range
                # Sort by first frame number if available
                frame_range = asset.get('frame_range', '')
                match = re.search(r'(\d+)', frame_range)
                return int(match.group(1)) if match else 0
            elif column == 3:  # Status
                return asset.get('status', '')
            elif column == 4:  # Date Created
                # Sort by actual file modification time
                path = asset.get('path', '')
                if os.path.exists(path):
                    return os.path.getmtime(path)
                return 0
            return ''
        
        reverse = (order == Qt.DescendingOrder)
        self.assets.sort(key=sort_key, reverse=reverse)
        self.dataChanged.emit(self.index(0, 0), self.index(self.rowCount() - 1, self.columnCount() - 1))
    
    def add_asset(self, asset_data: Dict[str, Any]):
        """Add an asset to the model."""
        self.beginInsertRows(QModelIndex(), len(self.assets), len(self.assets))
        self.assets.append(asset_data)
        self.endInsertRows()
    
    def clear_assets(self):
        """Clear all assets from the model."""
        self.beginResetModel()
        self.assets.clear()
        self.endResetModel()
    
    def update_asset_thumbnail(self, path: str, thumbnail_icon: QIcon, metadata: str):
        """Update the thumbnail and metadata for a specific asset."""
        for i, asset in enumerate(self.assets):
            if asset.get('path') == path:
                asset['thumbnail_icon'] = thumbnail_icon
                asset['metadata'] = metadata

                # Update frame range for videos based on metadata
                if metadata and self._is_video_file(path):
                    frame_count = self._extract_frame_count_from_metadata(metadata)
                    if frame_count and frame_count > 0:
                        asset['frame_range'] = f"1-{frame_count}"

                index = self.index(i, 0)
                self.dataChanged.emit(index, index)
                # Also emit for frame range column if it was updated
                frame_index = self.index(i, 2)
                self.dataChanged.emit(frame_index, frame_index)
                break
    
    def _is_video_file(self, path: str) -> bool:
        """Check if the file is a video file."""
        return is_video(path)
    
    def _extract_frame_count_from_metadata(self, metadata: str) -> Optional[int]:
        """Extract frame count from video metadata."""
        if not metadata:
            return None
        
        # Look for "Frames: {count}" pattern in metadata
        import re
        match = re.search(r'Frames:\s*(\d+)', metadata, re.IGNORECASE)
        if match:
            try:
                frame_count = int(match.group(1))
                return frame_count if frame_count > 0 else None
            except ValueError:
                pass
        return None
    
    def _get_status_background_color(self, status: str):
        """Get background color for status column based on status value."""
        from PySide6.QtGui import QColor
        
        color_map = {
            "None": QColor("#f0f0f0"),      # Light gray for no status
            "WIP": QColor("#fff3cd"),       # Light yellow for work in progress
            "Review": QColor("#d1ecf1"),    # Light blue for review
            "Approved": QColor("#d4edda"),  # Light green for approved
        }
        
        return color_map.get(status, QColor("#f0f0f0"))  # Default to light gray


class AssetListView(QTableView):
    """Custom table view for displaying assets in list format."""
    
    def __init__(self):
        super().__init__()
        self.model = AssetTableModel()
        self.setModel(self.model)
        
        # Set status delegate for column 3
        self.status_delegate = StatusDelegate(self)
        self.setItemDelegateForColumn(3, self.status_delegate)
        
        # Configure table appearance
        self.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.setSelectionMode(QAbstractItemView.SingleSelection)
        self.setAlternatingRowColors(False)  # Disable to allow custom background colors
        self.setSortingEnabled(True)
        self.setShowGrid(False)
        
        # Configure headers
        header = self.horizontalHeader()
        # Make Thumbnail (0) and Date Created (4) columns resizable (Interactive)
        header.setSectionResizeMode(0, QHeaderView.Interactive)  # Thumbnail column resizable from right
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Shot Name stretches to fill space
        header.setSectionResizeMode(2, QHeaderView.Interactive)  # Frame Range can be resized
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Status auto-size
        header.setSectionResizeMode(4, QHeaderView.Fixed)  # Date Created not resizable

        # Set minimum column widths
        header.setMinimumSectionSize(60)

        # Set default column widths
        self.thumbnail_size = 53
        self.model.set_thumbnail_size(self.thumbnail_size)
        self.setIconSize(QSize(self.thumbnail_size, self.thumbnail_size))
        self.setColumnWidth(0, self.thumbnail_size + 40)  # Thumbnail
        self.setColumnWidth(2, 90)   # Frame Range
        self.setColumnWidth(3, 70)   # Status
        self.setColumnWidth(4, 120)  # Date Created
        row_height = max(40, self.thumbnail_size + 4)
        self.verticalHeader().setDefaultSectionSize(row_height)
        self.verticalHeader().hide()

        # Set stylesheet for a more compact and modern appearance
        self.setStyleSheet("""
            QTableView {
                gridline-color: #3a3a3a;
                background-color: #232323;
                color: #f0f0f0;
                selection-background-color: #0078d4;
            }
            QTableView::item {
                padding: 1px 2px;
                border: none;
            }
            QTableView::item:selected {
                background-color: #0078d4 !important;
                color: white;
            }
            QTableView::item:hover {
                background-color: #353535;
            }
            QHeaderView::section {
                background-color: #353535;
                color: #f0f0f0;
                padding: 4px 6px;
                border: 1px solid #444444;
                font-weight: bold;
            }
            QHeaderView::section:hover {
                background-color: #444444;
            }
        """)
        
        # Enable context menu
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._show_context_menu)
        
    def set_thumbnail_size(self, size: int):
        """Set the thumbnail size and update row height accordingly. Always compact for list view."""
        self.thumbnail_size = 53
        self.model.set_thumbnail_size(self.thumbnail_size)
        row_height = max(40, self.thumbnail_size + 4)
        self.verticalHeader().setDefaultSectionSize(row_height)
        self.setColumnWidth(0, self.thumbnail_size + 40)
        # Set icon size to match column width for proper thumbnail display
        icon_width = self.columnWidth(0) - 8
        icon_height = row_height - 8
        self.setIconSize(QSize(icon_width, icon_height))
    
    def add_asset(self, path: str):
        """Add an asset to the list view."""
        # Extract asset information from file path
        asset_data = self._extract_asset_info(path)
        self.model.add_asset(asset_data)
    
    def clear_assets(self):
        """Clear all assets from the list view."""
        self.model.clear_assets()
    
    def update_asset_thumbnail(self, path: str, pixmap: Optional[QPixmap], metadata: str):
        """Update the thumbnail for a specific asset."""
        if pixmap:
            # Get the actual column width for thumbnail column (column 0)
            column_width = self.columnWidth(0) - 8  # Subtract padding for better fit
            
            # Scale pixmap to fit column width while maintaining aspect ratio
            # Keep height constrained to current row height minus padding
            max_height = self.verticalHeader().defaultSectionSize() - 8
            
            # Scale to fit width first, then constrain height if needed
            scaled_pixmap = pixmap.scaled(
                column_width, max_height,
                Qt.KeepAspectRatio, Qt.SmoothTransformation
            )
            icon = QIcon(scaled_pixmap)
        else:
            # Create placeholder icon using column width
            column_width = self.columnWidth(0) - 8
            max_height = self.verticalHeader().defaultSectionSize() - 8
            placeholder = QPixmap(column_width, max_height)
            placeholder.fill(Qt.darkGray)
            icon = QIcon(placeholder)
        
        self.model.update_asset_thumbnail(path, icon, metadata)
    
    def _extract_asset_info(self, path: str) -> Dict[str, Any]:
        """Extract asset information from file path."""
        filename = os.path.basename(path)
        
        # Extract shot name (everything before frame numbers or extension)
        shot_name = self._extract_shot_name(filename)
        
        # Extract frame range
        frame_range = self._extract_frame_range(filename)
        
        # Determine status (this could be enhanced with more sophisticated logic)
        status = self._determine_status(path, filename)
        
        # Get creation date
        date_created = self._get_date_created(path)
        
        # Create placeholder thumbnail using column width
        column_width = self.columnWidth(0) - 8 if hasattr(self, 'columnWidth') else self.thumbnail_size + 32
        max_height = self.verticalHeader().defaultSectionSize() - 8 if hasattr(self, 'verticalHeader') else self.thumbnail_size + 4
        placeholder = QPixmap(column_width, max_height)
        placeholder.fill(Qt.black)
        
        return {
            'path': path,
            'shot_name': shot_name,
            'frame_range': frame_range,
            'status': status,
            'date_created': date_created,
            'thumbnail_icon': QIcon(placeholder),
            'metadata': ''
        }
    
    def _extract_shot_name(self, filename: str) -> str:
        """Extract shot name from filename."""
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Common patterns for shot names:
        patterns = [
            # Pattern for Shot00001, Shot_001, etc.
            r'^(Shot[_\-]?\d+)',
            # Pattern for shot001, shot_001, etc.
            r'^(shot[_\-]?\d+)',
            # Pattern for any word followed by numbers (like render001, comp001)
            r'^([a-zA-Z]+\d+)',
            # Pattern for complex shot names like Shot_01_comp_v001
            r'^([^_\.]+_\d+)',
            # Pattern for sequence names like seq01_shot01
            r'^(seq\d+[_\-]shot\d+)',
            # General pattern: everything before version numbers or large frame sequences
            r'^([^\.]+?)(?:_v\d+|_\d{4,}|\.\d{4,}|_version\d+)?$',
        ]
        
        for pattern in patterns:
            match = re.match(pattern, name_without_ext, re.IGNORECASE)
            if match:
                shot_name = match.group(1)
                # Clean up shot name - normalize separators
                shot_name = re.sub(r'[_\-]+', '_', shot_name)
                # Remove trailing underscores
                shot_name = shot_name.rstrip('_')
                return shot_name
        
        # Fallback: use filename without extension, but truncate if too long
        result = name_without_ext
        if len(result) > 20:  # Truncate long names
            result = result[:17] + "..."
        return result
    
    def _extract_frame_range(self, filename: str) -> str:
        """Extract frame range from filename."""
        # Remove extension
        name_without_ext = os.path.splitext(filename)[0]
        
        # Look for frame number patterns
        patterns = [
            r'\.(\d{4,})$',  # .1001, .1002, etc.
            r'_(\d{4,})$',   # _1001, _1002, etc.
            r'(\d{4,})$',    # 1001, 1002, etc.
        ]
        
        frame_num = None
        for pattern in patterns:
            match = re.search(pattern, name_without_ext)
            if match:
                frame_num = match.group(1)
                break
        
        if frame_num:
            # Try to detect frame range by scanning directory
            directory = os.path.dirname(filename) if os.path.dirname(filename) else '.'
            if os.path.exists(directory):
                try:
                    frame_range = self._scan_frame_range(directory, name_without_ext, frame_num)
                    if frame_range:
                        return frame_range
                except:
                    pass
            return f"{frame_num}"
        
        # Check if it's a video file (single frame range)
        if is_video(filename):
            # For videos, we'll initially show "Video" but it will be updated
            # with actual frame count when metadata becomes available
            return "Video"
        
        return "Single"
    
    def _scan_frame_range(self, directory: str, base_name: str, current_frame: str) -> str:
        """Scan directory to find frame range for sequence."""
        try:
            # Extract the base name without frame number
            frame_pattern = current_frame
            base_pattern = base_name.replace(frame_pattern, '')
            
            # Find all files with similar pattern
            frames = []
            for file in os.listdir(directory):
                if file.startswith(base_pattern):
                    # Extract frame number from similar files
                    match = re.search(r'(\d{4,})', file)
                    if match:
                        try:
                            frames.append(int(match.group(1)))
                        except ValueError:
                            continue
            
            if len(frames) > 1:
                frames.sort()
                return f"{frames[0]}-{frames[-1]}"
            elif len(frames) == 1:
                return str(frames[0])
        except:
            pass
        
        return current_frame
    
    def _determine_status(self, path: str, filename: str) -> str:
        """Determine asset status - defaults to None for user control."""
        # Default to None - user will set status manually
        return "None"
    
        return "Unknown"
    
    def _show_context_menu(self, position):
        """Show context menu for status editing."""
        # Get the index at the clicked position
        index = self.indexAt(position)
        if not index.isValid():
            return
        
        # Create context menu
        menu = QMenu(self)
        
        # Status submenu
        status_menu = menu.addMenu("Set Status")
        
        # Status options
        status_options = ["None", "WIP", "Review", "Approved"]
        for status in status_options:
            action = status_menu.addAction(status)
            action.triggered.connect(lambda checked, s=status: self._set_asset_status(index.row(), s))
        
        # Show the menu
        menu.exec(self.mapToGlobal(position))
    
    def _set_asset_status(self, row: int, status: str):
        """Set the status for the asset at the given row."""
        if 0 <= row < len(self.model.assets):
            self.model.assets[row]['status'] = status
            # Emit data changed signal for the status column
            index = self.model.index(row, 3)  # Status column is index 3
            self.model.dataChanged.emit(index, index)
    
    def _get_date_created(self, path: str) -> str:
        """Get formatted creation date."""
        try:
            mtime = os.path.getmtime(path)
            date = datetime.fromtimestamp(mtime)
            return date.strftime("%d/%m/%Y")
        except:
            return "Unknown"
