"""
drowsiness_detector.py - Coordinates facial landmark detection, EAR calculation, and drowsiness detection logic.
Uses the modern MediaPipe Tasks FaceLandmarker API.
"""

import time
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from scipy.spatial import distance as dist
import config

class DrowsinessDetector:
    def __init__(self):
        # Configure Face Landmarker Tasks API
        base_options = python.BaseOptions(model_asset_path='face_landmarker.task')
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=1
        )
        self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
        
        # State variables
        self.closed_frames_counter = 0
        self.drowsy = False
        self.ear_threshold = config.DEFAULT_EAR_THRESHOLD
        
        # Calibration variables
        self.calibration_active = True
        self.calibration_start_time = None
        self.calibration_ears = []
        self.base_ear = None
        self.is_calibrated = False

    def calculate_ear(self, eye_points):
        """
        Calculates the Eye Aspect Ratio (EAR) for a single eye.
        Formula: EAR = (||p2 - p6|| + ||p3 - p5||) / (2 * ||p1 - p4||)
        """
        # Vertical distances
        v1 = dist.euclidean(eye_points[1], eye_points[5])  # p2 - p6
        v2 = dist.euclidean(eye_points[2], eye_points[4])  # p3 - p5
        
        # Horizontal distance
        h = dist.euclidean(eye_points[0], eye_points[3])   # p1 - p4
        
        # Avoid division by zero
        if h == 0:
            return 0.0
            
        # Calculate EAR
        ear = (v1 + v2) / (2.0 * h)
        return ear

    def get_eye_coordinates(self, landmarks, indices_dict, img_w, img_h):
        """
        Extracts the (x, y) pixel coordinates of the eye landmarks.
        Returns a list of points ordered: [p1, p2, p3, p4, p5, p6]
        """
        points = []
        # We need the points in order p1, p2, p3, p4, p5, p6
        for key in ['p1', 'p2', 'p3', 'p4', 'p5', 'p6']:
            idx = indices_dict[key]
            landmark = landmarks[idx]
            # Convert normalized coordinates to pixel values
            x = int(landmark.x * img_w)
            y = int(landmark.y * img_h)
            points.append((x, y))
        return points

    def get_contour_coordinates(self, landmarks, indices_list, img_w, img_h):
        """Extracts (x, y) coordinates for a list of indices, for drawing contours."""
        points = []
        for idx in indices_list:
            landmark = landmarks[idx]
            x = int(landmark.x * img_w)
            y = int(landmark.y * img_h)
            points.append((x, y))
        return np.array(points, dtype=np.int32)

    def process_frame(self, frame):
        """
        Processes a single video frame.
        Detects faces, calculates EAR, handles calibration, updates counters.
        Returns a dictionary of statistics.
        """
        h, w, _ = frame.shape
        
        # Convert the BGR image to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image object from RGB frame
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Process the image to find face landmarks
        results = self.face_landmarker.detect(mp_image)
        
        # Default status dictionary
        status = {
            "face_detected": False,
            "left_ear": 0.0,
            "right_ear": 0.0,
            "avg_ear": 0.0,
            "ear_threshold": self.ear_threshold,
            "closed_frames": self.closed_frames_counter,
            "drowsy": self.drowsy,
            "eye_status": "Unknown",
            "calibration_progress": 0.0,
            "calibration_status": "No Face Detected",
            "left_eye_points": [],
            "right_eye_points": [],
            "left_eye_contour": [],
            "right_eye_contour": []
        }
        
        # If no face is detected
        if not results.face_landmarks:
            # We don't reset the counters if face is lost, but we stop the alarm
            # and wait for face to appear again.
            self.drowsy = False
            status["drowsy"] = False
            return status
            
        # Extract landmarks for the first detected face
        face_landmarks = results.face_landmarks[0]
        status["face_detected"] = True
        
        # Get coordinates for the eye EAR points
        left_eye_pts = self.get_eye_coordinates(face_landmarks, config.LEFT_EYE_LANDMARKS, w, h)
        right_eye_pts = self.get_eye_coordinates(face_landmarks, config.RIGHT_EYE_LANDMARKS, w, h)
        
        status["left_eye_points"] = left_eye_pts
        status["right_eye_points"] = right_eye_pts
        
        # Get coordinates for eye drawing contours
        status["left_eye_contour"] = self.get_contour_coordinates(face_landmarks, config.LEFT_EYE_CONTOUR, w, h)
        status["right_eye_contour"] = self.get_contour_coordinates(face_landmarks, config.RIGHT_EYE_CONTOUR, w, h)
        
        # Calculate EAR for both eyes
        left_ear = self.calculate_ear(left_eye_pts)
        right_ear = self.calculate_ear(right_eye_pts)
        avg_ear = (left_ear + right_ear) / 2.0
        
        status["left_ear"] = left_ear
        status["right_ear"] = right_ear
        status["avg_ear"] = avg_ear
        
        # Handle calibration phase
        if self.calibration_active:
            current_time = time.time()
            if self.calibration_start_time is None:
                self.calibration_start_time = current_time
                
            elapsed = current_time - self.calibration_start_time
            progress = min(elapsed / config.CALIBRATION_DURATION_SEC, 1.0)
            
            status["calibration_progress"] = progress
            status["calibration_status"] = f"Calibrating: {int(progress * 100)}%"
            
            # Record EAR values when eyes are open (assuming driver looks straight during start)
            self.calibration_ears.append(avg_ear)
            
            if elapsed >= config.CALIBRATION_DURATION_SEC:
                # Finished calibrating
                self.calibration_active = False
                self.is_calibrated = True
                
                if self.calibration_ears:
                    # Exclude outliers (e.g. blinks during calibration) by taking the top 80% EAR values
                    self.calibration_ears.sort()
                    valid_ears = self.calibration_ears[int(len(self.calibration_ears) * 0.2):]
                    self.base_ear = sum(valid_ears) / len(valid_ears)
                    self.ear_threshold = self.base_ear * config.EAR_THRESHOLD_FACTOR
                else:
                    self.base_ear = config.DEFAULT_EAR_THRESHOLD / config.EAR_THRESHOLD_FACTOR
                    self.ear_threshold = config.DEFAULT_EAR_THRESHOLD
                    
                print(f"Calibration complete. Base EAR: {self.base_ear:.3f}, Dynamic Threshold: {self.ear_threshold:.3f}")
                
            status["ear_threshold"] = self.ear_threshold
            status["eye_status"] = "Calibrating"
            return status

        # Main detection logic
        status["calibration_progress"] = 1.0
        status["calibration_status"] = f"Calibrated (Base: {self.base_ear:.3f})"
        
        if avg_ear < self.ear_threshold:
            status["eye_status"] = "Closed"
            self.closed_frames_counter += 1
        else:
            status["eye_status"] = "Open"
            self.closed_frames_counter = 0
            
        status["closed_frames"] = self.closed_frames_counter
        
        if self.closed_frames_counter >= config.CONSECUTIVE_FRAMES:
            self.drowsy = True
        else:
            self.drowsy = False
            
        status["drowsy"] = self.drowsy
        return status

    def reset(self):
        """Resets the state of the detector."""
        self.closed_frames_counter = 0
        self.drowsy = False
        
    def close(self):
        """Closes the MediaPipe face landmarker instance."""
        self.face_landmarker.close()
