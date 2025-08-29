# Asset Browser v002 - Refactored Edition

A professional, modular standalone asset browser built with Python, OpenCV, OpenImageIO (OIIO), and PySide6.

## Features

- **Multi-format Support**: Browse and preview images (JPG, PNG, EXR, HDR, TIFF, etc.) and videos (MP4, MOV, AVI, etc.)
- **Thumbnail Grid**: Fast, threaded thumbnail generation with 16:9 aspect ratio
- **Project Management**: Organize assets by projects with centralized caching
- **Smart Caching**: Disk-based thumbnail cache with version control
- **Search & Filter**: Real-time search with regex support
- **Metadata Display**: Image metadata via OpenImageIO
- **Preview Pane**: Large preview with detailed metadata
- **Customizable UI**: Adjustable thumbnail size, grid spacing, and layout options
- **HDR Support**: Advanced tonemapping for HDR images (EXR, HDR)
- **Performance**: Multi-threaded processing with configurable thread count

## Architecture

The refactored version follows a clean, modular architecture:

```
Asset Browser v002/
├── main.py                 # Application entry point
├── setup.py               # Virtual environment setup
├── requirements.txt       # Python dependencies
├── run_asset_browser.bat  # Windows batch launcher
├── run_asset_browser.ps1  # PowerShell launcher
├── install_and_run.bat    # Setup and run script
└── src/                   # Source code
    ├── core/              # Core application logic
    │   └── application.py # Main application class
    ├── ui/                # User interface components
    │   ├── main_window.py # Main application window
    │   ├── thumb_list.py  # Thumbnail grid widget
    │   ├── preview_pane.py# Preview and metadata pane
    │   └── settings_dialog.py # Settings configuration
    ├── thumbnail/         # Thumbnail generation
    │   ├── cache.py       # Cache management
    │   ├── image_processor.py # Image processing
    │   └── thumb_task.py  # Threading and tasks
    ├── config/            # Configuration management
    │   ├── constants.py   # Application constants
    │   └── config_manager.py # Settings persistence
    └── utils/             # Utility modules
        ├── environment.py # Virtual environment setup
        ├── file_utils.py  # File type detection
        └── logging_config.py # Logging configuration
```

## Installation & Setup

### Option 1: Automatic Setup (Recommended)
```bash
# Run the automatic installer
install_and_run.bat
```

### Option 2: Manual Setup
```bash
# 1. Setup virtual environment and install dependencies
python setup.py

# 2. Run the application
python main.py
```

### Option 3: System Python
```bash
# Install dependencies globally
pip install -r requirements.txt

# Run the application
python main.py
```

## Usage

### Quick Start
1. Launch the application using one of the run scripts
2. Create a new project via **File → New Project**
3. Browse folders and view thumbnails
4. Use the search box to filter assets
5. Click thumbnails to see previews and metadata

### Project Management
- **New Project**: Add project folders for organized asset management
- **Project-based Caching**: Each project gets its own cache directory
- **Tree Navigation**: Browse project folders in the left panel

### Customization
- **Settings**: Access via **Edit → Preferences** or `Ctrl+,`
- **Thumbnail Size**: Adjust with the slider or in settings
- **View Options**: Toggle metadata panel and tree view
- **Performance**: Configure thread count and cache settings

## Technical Details

### Supported Formats
- **Images**: JPG, JPEG, PNG, BMP, TIFF, TIF, GIF, EXR, HDR, DPX, PSD, SVG, JP2
- **Videos**: MP4, MOV, AVI, MKV, WEBM

### Dependencies
- **PySide6**: Modern Qt6-based GUI framework
- **OpenImageIO**: Professional image I/O with metadata support
- **OpenCV**: Computer vision library for image processing
- **NumPy**: Numerical computing for image data

### Performance Features
- **Multi-threading**: Parallel thumbnail generation
- **Smart Caching**: File modification time-based cache invalidation
- **Memory Management**: Configurable cache size limits
- **Lazy Loading**: Thumbnails generated on-demand

### Cache Management
- **Project-based**: `(ProjectName)_AssetBrowserCache` folders
- **Hierarchical**: Organized by folder structure
- **Versioned**: Cache invalidation on file changes
- **Configurable**: Cache size limits and auto-cleanup options

## Configuration

Settings are automatically saved in `~/.assetbrowser_config/settings.json`:

```json
{
  "thumb_size": 256,
  "cache_enabled": true,
  "grid_spacing": 8,
  "show_metadata": true,
  "show_tree_view": true,
  "thread_count": 4,
  "projects": ["/path/to/project1", "/path/to/project2"]
}
```

## Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+N` | New Project |
| `Ctrl+O` | Open Folder |
| `Ctrl+F` | Focus Search |
| `Ctrl+,` | Open Settings |
| `F5` | Refresh View |
| `F1` | Show Shortcuts |
| `Ctrl+Q` | Exit Application |

## Logging

Logs are automatically saved to `~/.assetbrowser_logs/asset_browser.log`:
- Configurable log levels (DEBUG, INFO, WARNING, ERROR)
- Rotating log files (1MB max, 3 backups)
- Performance and error tracking

## Virtual Environment

The application automatically detects and uses a `.venv` virtual environment:
- Isolated dependencies
- Automatic activation
- Clean system separation

## Troubleshooting

### Common Issues
1. **Import Errors**: Run `python setup.py` to install dependencies
2. **OpenImageIO Missing**: Install with `pip install OpenImageIO`
3. **Permission Errors**: Ensure write access to cache directories
4. **Performance Issues**: Reduce thread count in settings

### Debug Mode
Set environment variable for detailed logging:
```bash
set ASSET_BROWSER_LOG_LEVEL=DEBUG
python main.py
```

## Development

### Code Organization
- **Separation of Concerns**: Each module has a specific responsibility
- **Loose Coupling**: Minimal dependencies between modules
- **Extensibility**: Easy to add new features or modify existing ones
- **Testability**: Modular structure supports unit testing

### Key Design Patterns
- **MVC Architecture**: Separation of UI, logic, and data
- **Observer Pattern**: Signal/slot communication
- **Factory Pattern**: Thumbnail task creation
- **Singleton Pattern**: Configuration manager

## License

This project is provided as-is for educational and professional use.

## Version History

### v002 (Refactored)
- Complete architectural refactoring
- Modular design with clean separation
- Improved error handling and logging
- Enhanced project management
- Better performance and caching
- Professional code organization

### v001 (Original)
- Monolithic single-file design
- Basic functionality implementation
