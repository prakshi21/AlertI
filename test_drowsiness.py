"""
test_drowsiness.py - Test suite for verifying the math and core classes of the Drowsiness Detection System.
"""

import os
import time
import unittest
import numpy as np
from drowsiness_detector import DrowsinessDetector
from alarm_manager import AlarmManager
import config

class TestDrowsinessSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        print("Setting up test dependencies...")
        # Create a detector instance (this checks if MediaPipe is working)
        cls.detector = DrowsinessDetector()
        # Create an alarm manager instance (this checks if sound generation is working)
        cls.alarm_manager = AlarmManager()

    @classmethod
    def tearDownClass(cls):
        print("Tearing down test dependencies...")
        cls.detector.close()
        cls.alarm_manager.cleanup()

    def test_ear_calculation_math(self):
        """Tests the EAR calculation formula with predefined coordinates."""
        # Define mock eye points where vertical distances are known and horizontal distance is known.
        # Format: [p1, p2, p3, p4, p5, p6]
        # Let:
        # p1 (0, 0), p4 (10, 0) -> horizontal distance = 10
        # p2 (3, 3), p6 (3, 0) -> vertical distance 1 = 3
        # p3 (7, 3), p5 (7, 0) -> vertical distance 2 = 3
        # Expected EAR = (3 + 3) / (2 * 10) = 6 / 20 = 0.3
        
        mock_eye_points = [
            (0, 0),   # p1 (outer corner)
            (3, 3),   # p2 (top-left)
            (7, 3),   # p3 (top-right)
            (10, 0),  # p4 (inner corner)
            (7, 0),   # p5 (bottom-right)
            (3, 0)    # p6 (bottom-left)
        ]
        
        calculated_ear = self.detector.calculate_ear(mock_eye_points)
        self.assertAlmostEqual(calculated_ear, 0.3, places=5)
        print(f"EAR calculation test passed. Expected 0.3, got {calculated_ear:.3f}")

    def test_alarm_wav_file_generation(self):
        """Verifies that the alarm WAV sound file is programmatically generated and exists."""
        self.assertTrue(os.path.exists(config.ALARM_SOUND_PATH))
        self.assertTrue(os.path.getsize(config.ALARM_SOUND_PATH) > 0)
        print(f"Alarm WAV file generation test passed. File size: {os.path.getsize(config.ALARM_SOUND_PATH)} bytes")

    def test_audio_playback_functions(self):
        """Verifies triggering and stopping the alarm doesn't raise errors."""
        try:
            print("Triggering alarm for 1 second in test...")
            self.alarm_manager.trigger_alarm()
            self.assertTrue(self.alarm_manager.is_alarm_playing)
            time.sleep(1.0)
            
            print("Stopping alarm in test...")
            self.alarm_manager.stop_alarm()
            self.assertFalse(self.alarm_manager.is_alarm_playing)
            print("Audio playback functionality test passed.")
        except Exception as e:
            self.fail(f"Audio playback raised an exception: {e}")

    def test_text_to_speech_engine(self):
        """Tests that text-to-speech triggers successfully without exceptions."""
        try:
            print("Testing text-to-speech message queue...")
            self.alarm_manager.speak_warning_async("System check successful.")
            # Small sleep to allow thread to spawn
            time.sleep(0.5)
            print("Text-to-Speech call verification passed.")
        except Exception as e:
            self.fail(f"Text-to-Speech raised an exception: {e}")

if __name__ == '__main__':
    unittest.main()
