"""
main.py - Main entry point for the AlertI Driver Drowsiness Detection System.
"""

import sys
import time
import cv2
import config
from drowsiness_detector import DrowsinessDetector
from alarm_manager import AlarmManager
import hud

def main():
    print("=========================================================")
    print("      AlertI - Driver Drowsiness Detection System        ")
    print("=========================================================")
    print("Initialising systems...")
    
    # Initialize components
    detector = DrowsinessDetector()
    alarm_manager = AlarmManager()
    
    # Initialize video capture (Webcam)
    cap = cv2.VideoCapture(config.CAMERA_INDEX)
    if not cap.isOpened():
        print(f"Error: Could not open video source at index {config.CAMERA_INDEX}.")
        print("Please check webcam connection and permissions.")
        alarm_manager.cleanup()
        sys.exit(1)
        
    # Configure capture parameters
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)
    
    # Let webcam sensor warm up
    time.sleep(1.0)
    
    # Timing variables for FPS
    prev_time = time.time()
    fps = 0.0
    
    print("\nSystem running! Press:")
    print("  'q' or 'ESC' to exit")
    print("  'r' to recalibrate the baseline eye aspect ratio")
    print("---------------------------------------------------------")
    
    # Create output window
    window_name = "AlertI - Driver Drowsiness Detection System"
    cv2.namedWindow(window_name, cv2.WINDOW_AUTOSIZE)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                print("Failed to capture image from webcam.")
                break
                
            # Flip the image horizontally for a mirror view (more natural for user calibration)
            frame = cv2.flip(frame, 1)
            
            # Process frame through drowsiness detector
            stats = detector.process_frame(frame)
            
            # Control alarm output
            if stats["drowsy"]:
                alarm_manager.trigger_alarm()
            else:
                alarm_manager.stop_alarm()
                
            # Calculate frames per second (FPS)
            current_time = time.time()
            elapsed_time = current_time - prev_time
            if elapsed_time > 0:
                # Simple low-pass filter to smooth FPS readings
                current_fps = 1.0 / elapsed_time
                fps = 0.9 * fps + 0.1 * current_fps
            prev_time = current_time
            
            # Draw HUD and eye contours on the frame
            hud.draw_hud(frame, stats, fps)
            
            # Show processed frame in a window
            cv2.imshow(window_name, frame)
            
            # Key handlers
            key = cv2.waitKey(1) & 0xFF
            
            # Quit on 'q' or ESC (27)
            if key == ord('q') or key == 27:
                print("Exit signal received. Terminating...")
                break
                
            # Recalibrate on 'r'
            elif key == ord('r'):
                print("\nRecalibration triggered! Keep your eyes open and look at the camera.")
                alarm_manager.stop_alarm()
                detector.reset()
                detector.calibration_active = True
                detector.calibration_start_time = None
                detector.calibration_ears = []
                detector.is_calibrated = False
                
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received. Terminating...")
    finally:
        # Graceful cleanup
        print("Cleaning up resources...")
        alarm_manager.cleanup()
        cap.release()
        cv2.destroyAllWindows()
        detector.close()
        print("System safely shut down. Goodbye!")

if __name__ == "__main__":
    main()
