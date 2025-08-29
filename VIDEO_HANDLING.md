# Video File Handling in Asset Browser v002

## Overview

The Asset Browser properly handles both image and video files, with different processing pipelines optimized for each media type.

## Video File Processing

### Supported Video Formats
- MP4, MOV, AVI, MKV, WEBM

### Processing Pipeline
1. **Detection**: File extension determines video vs image processing
2. **Frame Extraction**: OpenCV extracts first frame (at 1 second mark when possible)
3. **Metadata**: OpenCV provides video-specific metadata (resolution, FPS, duration, codec)
4. **Thumbnail**: Frame is resized to 16:9 aspect ratio thumbnail
5. **Caching**: Thumbnail cached for performance

### Video Metadata
For video files, the metadata panel displays:
- Video resolution (width x height)
- Frame rate (FPS)
- Duration in seconds
- Total frame count
- Codec/format information

### Error Handling
- **OIIO Skipping**: Video files automatically skip OpenImageIO processing
- **Graceful Fallback**: If video frame extraction fails, placeholder thumbnail is shown
- **Detailed Logging**: Specific debug information for troubleshooting

## Technical Details

### Why OIIO Warnings Occurred
OpenImageIO is designed for still images and doesn't support video formats. The original code would attempt to read video files with OIIO, resulting in "format reader" warnings.

### Resolution
The refactored version:
1. **Checks file extension** before attempting OIIO processing
2. **Routes video files** directly to OpenCV processing
3. **Uses separate metadata extraction** for video files
4. **Logs appropriately** with debug-level messages for expected behaviors

### Performance Benefits
- **Faster Processing**: No unnecessary OIIO attempts for video files
- **Cleaner Logging**: Reduced noise in log files
- **Better UX**: More informative metadata for video files
- **Efficient Caching**: Same caching strategy works for both media types

## Usage Notes

- Video thumbnails show the frame at 1 second (when possible) to avoid black frames
- Large video files may take longer to process than images
- Video metadata is extracted quickly without full file processing
- Corrupted or unsupported video files show placeholder thumbnails

This improvement makes the Asset Browser more robust and user-friendly when working with mixed media projects containing both images and videos.
