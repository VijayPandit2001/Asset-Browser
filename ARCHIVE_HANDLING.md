# Archive File Handling in Asset Browser v002

## Overview

The Asset Browser can detect when files are located inside compressed archives but cannot directly preview them. This document explains the behavior and provides guidance for working with archived assets.

## Supported Archive Detection

The application detects the following archive formats:
- **7-Zip**: `.7z`
- **ZIP**: `.zip` 
- **RAR**: `.rar`
- **Tar**: `.tar`
- **Gzip**: `.gz`
- **Bzip2**: `.bz2`

## Behavior with Archive Files

### Detection
When browsing through Windows Explorer or file managers that show virtual paths inside archives, the Asset Browser will:

1. **Detect Archive Context**: Recognize when file paths contain archive files
2. **Show Placeholder Thumbnails**: Display "ZIP" icon instead of attempting to load
3. **Provide Informative Metadata**: Explain that files are archived and need extraction

### Visual Indicators
- **Thumbnail**: Shows "ZIP" text instead of actual content
- **Metadata Panel**: Displays archive name and extraction instructions
- **Log Messages**: Debug-level messages (not warnings) for archive detection

## Example Scenarios

### Scenario 1: Browsing Inside 7z Archive
```
Path: D:\Showreel\archive.7z\videos\movie.mov
Result: 
- Thumbnail: "ZIP" placeholder
- Metadata: "File in compressed archive: archive.7z
           Extract archive to view content"
```

### Scenario 2: Extracted Files
```
Path: D:\Showreel\extracted\videos\movie.mov
Result:
- Thumbnail: Actual video frame
- Metadata: Video resolution, FPS, duration, etc.
```

## Working with Archived Assets

### Recommended Workflow
1. **Extract Archive**: Extract the compressed archive to a regular folder
2. **Browse Extracted Content**: Navigate to the extracted folder in Asset Browser
3. **Full Functionality**: Enjoy complete thumbnail and preview functionality

### Why Archives Can't Be Previewed
- **File System Limitations**: Archive contents are not accessible as regular files
- **OpenCV/OIIO Constraints**: Media libraries require direct file system access
- **Performance Considerations**: Extracting files temporarily would be slow and resource-intensive

## Log Messages Explanation

### Before Improvements (Problematic)
```
[WARNING] Could not read frame from video: D:\archive.7z\video.mov
[WARNING] Failed to load media for thumbnail, using placeholder
```

### After Improvements (Informative)
```
[DEBUG] Video file is inside archive, cannot extract frame: D:\archive.7z\video.mov
[DEBUG] Failed to load media for thumbnail, using placeholder
```

## Technical Implementation

### Archive Detection Logic
```python
def is_in_archive(path: str) -> bool:
    """Check if file path indicates it's inside a compressed archive."""
    archive_extensions = {'.7z', '.zip', '.rar', '.tar', '.gz', '.bz2'}
    path_parts = os.path.normpath(path).split(os.sep)
    return any(any(part.lower().endswith(ext) for ext in archive_extensions) 
               for part in path_parts)
```

### Smart Placeholder Generation
- **Archive Detection**: Automatically detects archive context
- **Appropriate Icon**: Shows "ZIP" instead of generic "?" 
- **Informative Metadata**: Provides specific extraction guidance
- **Clean Logging**: Uses debug level for expected behavior

## Benefits of This Approach

1. **User Clarity**: Clear indication that files need extraction
2. **Reduced Confusion**: No misleading error messages
3. **Performance**: Quick detection without unnecessary processing attempts
4. **Professional UX**: Proper handling of edge cases

## Alternative Solutions

### For Frequent Archive Browsing
1. **Extract to Temp Folder**: Manually extract archives when needed
2. **Archive Management Tools**: Use specialized tools like 7-Zip for browsing
3. **Batch Extraction**: Extract multiple archives to a working directory

### Future Enhancement Possibilities
- **Temporary Extraction**: Auto-extract small files to temp directory
- **Archive Integration**: Direct integration with archive libraries
- **Preview Cache**: Cache extracted previews for frequently accessed archives

This intelligent archive handling makes the Asset Browser more user-friendly and provides clear guidance when encountering archived content.
