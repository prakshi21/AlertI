"""
config.py - Configuration constants for the Driver Drowsiness Detection System.
"""

# Video Capture Settings
CAMERA_INDEX = 0          # Default webcam source
FRAME_WIDTH = 640         # Capture width
FRAME_HEIGHT = 480        # Capture height

# Calibration Settings
CALIBRATION_DURATION_SEC = 5.0  # Duration in seconds to calibrate the base EAR
CALIBRATION_PROMPT = "CALIBRATING... LOOK STRAIGHT WITH EYES OPEN"

# Drowsiness Logic Parameters
# A dynamic threshold will be calculated as a percentage of the calibrated base EAR.
# If calibration fails or is disabled, this default threshold is used.
DEFAULT_EAR_THRESHOLD = 0.25
EAR_THRESHOLD_FACTOR = 0.75   # Threshold is set to 75% of the calibrated open-eye EAR

# Consecutive frames the eyes must be closed to trigger the alarm
CONSECUTIVE_FRAMES = 25       # Approx 1.25 seconds at 20 FPS

# MediaPipe Face Mesh Settings
MIN_DETECTION_CONFIDENCE = 0.5
MIN_TRACKING_CONFIDENCE = 0.5

# Warning System Settings
ALARM_SOUND_PATH = "alarm.wav"
ALARM_FREQUENCY = 1000        # Sound frequency in Hz (for programmatic beep generation)
ALARM_DURATION_SEC = 1.0       # Duration of one loop beep in seconds
TTS_ENABLED = True            # Enable text-to-speech warnings

# Landmark indices for EAR calculation in MediaPipe Face Mesh.
# The layout is:
# p1: outer corner, p4: inner corner
# p2: upper eyelid (outer-ish), p6: lower eyelid (outer-ish)
# p3: upper eyelid (inner-ish), p5: lower eyelid (inner-ish)

RIGHT_EYE_LANDMARKS = {
    'p1': 33,   # Outer corner
    'p2': 159,  # Upper eyelid (mid-outer)
    'p3': 158,  # Upper eyelid (mid-inner)
    'p4': 133,  # Inner corner
    'p5': 153,  # Lower eyelid (mid-inner)
    'p6': 145   # Lower eyelid (mid-outer)
}

LEFT_EYE_LANDMARKS = {
    'p1': 362,  # Outer corner (relative to image) / Inner corner (anatomical left)
    'p2': 386,  # Upper eyelid (mid-outer)
    'p3': 385,  # Upper eyelid (mid-inner)
    'p4': 263,  # Inner corner (relative to image) / Outer corner (anatomical left)
    'p5': 374,  # Lower eyelid (mid-inner)
    'p6': 380,  # Lower eyelid (mid-outer)
}

# Entire eye contours to draw visual overlays on screen
RIGHT_EYE_CONTOUR = [33, 160, 158, 133, 153, 144]
LEFT_EYE_CONTOUR = [362, 385, 387, 263, 373, 380]
