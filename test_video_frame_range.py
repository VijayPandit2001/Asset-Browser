#!/usr/bin/env python3
"""
Test script to verify video frame range extraction functionality.
"""

import re
from typing import Optional

def _extract_frame_count_from_metadata(metadata: str) -> Optional[int]:
    """Extract frame count from video metadata."""
    if not metadata:
        return None
    
    # Look for "Frames: {count}" pattern in metadata
    match = re.search(r'Frames:\s*(\d+)', metadata, re.IGNORECASE)
    if match:
        try:
            frame_count = int(match.group(1))
            return frame_count if frame_count > 0 else None
        except ValueError:
            pass
    return None

def test_frame_extraction():
    """Test the frame extraction function."""
    test_cases = [
        ("Video: 1920x1080\nFPS: 30.00\nDuration: 10.00s\nFrames: 300\nCodec: MP4", 300),
        ("Video: 1280x720\nFPS: 24.00\nDuration: 5.00s\nFrames: 120\nCodec: MOV", 120),
        ("Video: 3840x2160\nFPS: 60.00\nDuration: 2.50s\nFrames: 150\nCodec: AVI", 150),
        ("Video: 1920x1080\nFPS: 30.00\nDuration: 0.00s\nFrames: 0\nCodec: MP4", None),  # Edge case: 0 frames
        ("Video: 1920x1080\nFPS: 30.00\nDuration: 10.00s\nFrames: Unknown\nCodec: MP4", None),  # Edge case: Unknown frames
        ("Some other metadata without frames", None),
        ("", None),
        ("Frames: not_a_number", None),
    ]
    
    print("Testing frame count extraction from metadata:")
    for metadata, expected in test_cases:
        result = _extract_frame_count_from_metadata(metadata)
        status = "✓" if result == expected else "✗"
        print(f"{status} Expected: {expected}, Got: {result}")
        if result != expected:
            print(f"   Metadata: {repr(metadata)}")

if __name__ == "__main__":
    test_frame_extraction()
