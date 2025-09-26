"""
Tests for OpenFlexure microscope video recording functionality.

These tests validate the video recording methods in the MicroscopeDemo class
using mock objects to avoid requiring actual microscope hardware.
"""

import os
import tempfile
import threading
import time
import unittest
from unittest.mock import Mock, patch, MagicMock
from PIL import Image
import datetime

# Import the classes to test
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "ac_training_lab" / "openflexure"))

try:
    from microscope_demo_client import MicroscopeDemo
except ImportError:
    # Skip tests if dependencies not available
    import pytest
    pytestmark = pytest.mark.skip("OpenFlexure dependencies not available")


class TestOpenFlexureVideoRecording(unittest.TestCase):
    """Test cases for OpenFlexure microscope video recording functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        
        # Create a mock microscope with patched MQTT client
        with patch('microscope_demo_client.mqtt.Client'):
            self.mock_microscope = MicroscopeDemo(
                host="test_host",
                port=8883,
                username="test_user", 
                password="test_pass",
                microscope="test_microscope"
            )
            
        # Mock the take_image method to return test images
        self.test_image = Image.new('RGB', (640, 480), color='red')
        self.mock_microscope.take_image = Mock(return_value=self.test_image)

    def tearDown(self):
        """Clean up test fixtures."""
        # Clean up temp directory
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_start_video_recording(self):
        """Test that video recording can be started."""
        result = self.mock_microscope.start_video_recording(fps=5, output_dir=self.temp_dir)
        
        self.assertTrue(result)
        self.assertTrue(self.mock_microscope._recording)
        self.assertIsNotNone(self.mock_microscope._recording_thread)
        self.assertIsNotNone(self.mock_microscope._recording_start_time)
        
        # Stop recording
        self.mock_microscope.stop_video_recording()
        
    def test_stop_video_recording_without_start(self):
        """Test stopping recording when no recording is active."""
        result = self.mock_microscope.stop_video_recording()
        self.assertIsNone(result)

    def test_video_recording_captures_frames(self):
        """Test that video recording actually captures frames."""
        self.mock_microscope.start_video_recording(fps=10, output_dir=self.temp_dir)
        
        # Wait a short time for some frames to be captured
        time.sleep(0.5)
        
        # Should have captured some frames
        self.assertGreater(len(self.mock_microscope._frames), 0)
        
        # Stop recording
        video_path = self.mock_microscope.stop_video_recording()
        self.assertIsNotNone(video_path)
        self.assertTrue(os.path.exists(video_path))

    def test_record_video_for_duration(self):
        """Test the convenience method for recording with duration."""
        output_file = os.path.join(self.temp_dir, "test_recording.gif")
        
        result = self.mock_microscope.record_video_for_duration(
            duration_seconds=1,
            fps=5,
            output_filename=output_file
        )
        
        self.assertIsNotNone(result)
        self.assertTrue(os.path.exists(result))

    def test_concurrent_recording_prevention(self):
        """Test that starting a second recording while one is active fails."""
        self.mock_microscope.start_video_recording(fps=5, output_dir=self.temp_dir)
        
        # Try to start another recording
        result = self.mock_microscope.start_video_recording(fps=5, output_dir=self.temp_dir)
        self.assertIsNone(result)  # Should fail
        
        # Stop the first recording
        self.mock_microscope.stop_video_recording()

    def test_recording_with_failed_image_capture(self):
        """Test that recording handles image capture failures gracefully."""
        # Mock take_image to sometimes fail
        call_count = 0
        def mock_take_image():
            nonlocal call_count
            call_count += 1
            if call_count % 2 == 0:  # Fail every other call
                raise Exception("Mock image capture failure")
            return self.test_image
            
        self.mock_microscope.take_image = mock_take_image
        
        self.mock_microscope.start_video_recording(fps=10, output_dir=self.temp_dir)
        time.sleep(0.5)  # Let it try to capture some frames
        
        video_path = self.mock_microscope.stop_video_recording()
        
        # Should still work despite some failures
        self.assertIsNotNone(video_path)

    def test_end_connection_stops_recording(self):
        """Test that ending connection stops active recording."""
        self.mock_microscope.start_video_recording(fps=5, output_dir=self.temp_dir)
        self.assertTrue(self.mock_microscope._recording)
        
        self.mock_microscope.end_connection()
        self.assertFalse(self.mock_microscope._recording)

    def test_video_file_format_and_naming(self):
        """Test that video files are created with correct format and naming."""
        video_path = self.mock_microscope.record_video_for_duration(
            duration_seconds=0.5,
            fps=5,
            output_filename=None  # Auto-generate name
        )
        
        self.assertIsNotNone(video_path)
        self.assertTrue(video_path.endswith('.gif'))
        self.assertTrue('microscope_recording_' in os.path.basename(video_path))
        self.assertTrue(os.path.exists(video_path))


if __name__ == '__main__':
    unittest.main()