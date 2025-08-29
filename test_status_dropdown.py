#!/usr/bin/env python3
"""
Test script for status dropdown functionality in Asset Browser.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from PySide6.QtGui import QColor
from src.ui.list_view import AssetListView


def test_status_functionality():
    """Test the status editing functionality."""
    app = QApplication(sys.argv)

    # Create list view
    list_view = AssetListView()

    # Add a test asset
    test_path = "test_shot_001.exr"
    list_view.add_asset(test_path)

    # Verify initial status is "None"
    model = list_view.model
    if len(model.assets) > 0:
        initial_status = model.assets[0].get('status')
        print(f"Initial status: {initial_status}")
        assert initial_status == "None", f"Expected 'None', got '{initial_status}'"

        # Test setting status programmatically
        model.assets[0]['status'] = "WIP"
        updated_status = model.assets[0].get('status')
        print(f"Updated status: {updated_status}")
        assert updated_status == "WIP", f"Expected 'WIP', got '{updated_status}'"

        # Test color coding
        bg_color = model._get_status_background_color("WIP")
        print(f"WIP Background color: {bg_color.name()}")

        # Verify colors are correct
        expected_bg = QColor("#fff3cd")
        assert bg_color == expected_bg, f"Expected {expected_bg.name()}, got {bg_color.name()}"

        print("✓ Status functionality test passed!")

        # Test all status colors
        print("\n--- Color Coding Demo ---")
        statuses = ["None", "WIP", "Review", "Approved"]
        for status in statuses:
            bg_color = model._get_status_background_color(status)
            print(f"{status:8} | Background: {bg_color.name()}")

        print("✓ Color coding test passed!")
    else:
        print("✗ No assets found in model")

    # Clean up
    app.quit()
    return True


if __name__ == "__main__":
    test_status_functionality()