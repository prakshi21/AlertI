"""
hud.py - Handles all graphical overlay operations, drawing HUD widgets and eye overlays onto the OpenCV frame.
"""

import cv2
import numpy as np
import time

def draw_glass_card(img, x1, y1, x2, y2, alpha=0.6, bg_color=(20, 20, 20), border_color=(0, 255, 242)):
    """Draws a semi-transparent rounded-like card with a neon border for a premium HUD aesthetic."""
    # Crop the area of interest
    sub_img = img[y1:y2, x1:x2]
    
    # Create the card overlay
    rect = np.zeros(sub_img.shape, dtype=np.uint8)
    rect[:] = bg_color
    
    # Blend the overlay with the original image
    blend = cv2.addWeighted(sub_img, 1.0 - alpha, rect, alpha, 0)
    img[y1:y2, x1:x2] = blend
    
    # Draw neon border
    cv2.rectangle(img, (x1, y1), (x2, y2), border_color, 1)

def draw_hud(frame, stats, fps):
    """
    Overlays the main HUD panel, eye contours, status text, and alarms on the frame.
    """
    h, w, _ = frame.shape
    is_drowsy = stats["drowsy"]
    eye_status = stats["eye_status"]
    
    # Define primary theme colors
    neon_cyan = (242, 255, 0)     # BGR
    neon_green = (0, 255, 100)    # BGR
    neon_red = (0, 0, 255)        # BGR
    theme_gray = (120, 120, 120)  # BGR
    
    # --- 1. Draw Eye Contours ---
    # Draw right eye contour
    if len(stats["right_eye_contour"]) > 0:
        contour_color = neon_red if eye_status == "Closed" else neon_green
        cv2.polylines(frame, [stats["right_eye_contour"]], True, contour_color, 1)
        # Draw small landmark points for key vertices
        for pt in stats["right_eye_points"]:
            cv2.circle(frame, pt, 2, contour_color, -1)
            
    # Draw left eye contour
    if len(stats["left_eye_contour"]) > 0:
        contour_color = neon_red if eye_status == "Closed" else neon_green
        cv2.polylines(frame, [stats["left_eye_contour"]], True, contour_color, 1)
        # Draw small landmark points for key vertices
        for pt in stats["left_eye_points"]:
            cv2.circle(frame, pt, 2, contour_color, -1)

    # --- 2. Draw Side Control & Info Panel (Glass Card) ---
    card_x1, card_y1 = 15, 15
    card_x2, card_y2 = 280, 220
    draw_glass_card(frame, card_x1, card_y1, card_x2, card_y2, alpha=0.7)
    
    # HUD Title
    cv2.putText(frame, "AlertI - MONITOR", (card_x1 + 15, card_y1 + 25), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.6, neon_cyan, 2, cv2.LINE_AA)
    cv2.line(frame, (card_x1 + 15, card_y1 + 35), (card_x2 - 15, card_y1 + 35), (100, 100, 100), 1)
    
    # Dynamic values & colors
    ear_color = neon_green if stats["avg_ear"] >= stats["ear_threshold"] else neon_red
    status_color = neon_green if eye_status == "Open" else (neon_red if eye_status == "Closed" else neon_cyan)
    alarm_color = neon_red if is_drowsy else theme_gray
    alarm_text = "ACTIVE" if is_drowsy else "OFF"
    
    # Print HUD data lines
    y_offset = card_y1 + 60
    
    # Average EAR line
    cv2.putText(frame, f"EAR: {stats['avg_ear']:.3f}", (card_x1 + 15, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, ear_color, 1, cv2.LINE_AA)
    cv2.putText(frame, f"(Thresh: {stats['ear_threshold']:.3f})", (card_x1 + 140, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.4, theme_gray, 1, cv2.LINE_AA)
                
    # Eye status
    y_offset += 25
    cv2.putText(frame, f"EYES: {eye_status.upper()}", (card_x1 + 15, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, status_color, 2 if eye_status == "Closed" else 1, cv2.LINE_AA)
                
    # Alarm state
    y_offset += 25
    cv2.putText(frame, f"ALARM: {alarm_text}", (card_x1 + 15, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, alarm_color, 2 if is_drowsy else 1, cv2.LINE_AA)
                
    # Frame Rate (FPS)
    y_offset += 25
    cv2.putText(frame, f"FPS: {fps:.1f}", (card_x1 + 15, y_offset), 
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, neon_cyan, 1, cv2.LINE_AA)
                
    # Calibration Info & Progress Bar
    y_offset += 30
    cal_progress = stats["calibration_progress"]
    cal_status = stats["calibration_status"]
    
    if cal_progress < 1.0:
        # Drawing a small visual progress bar inside the card
        bar_x1 = card_x1 + 15
        bar_y1 = y_offset + 5
        bar_w = card_x2 - card_x1 - 30
        bar_h = 8
        
        # Draw bar background
        cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x1 + bar_w, bar_y1 + bar_h), (50, 50, 50), -1)
        # Draw bar fill
        cv2.rectangle(frame, (bar_x1, bar_y1), (bar_x1 + int(bar_w * cal_progress), bar_y1 + bar_h), neon_cyan, -1)
        # Draw status text above bar
        cv2.putText(frame, cal_status, (card_x1 + 15, y_offset - 2), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.45, neon_cyan, 1, cv2.LINE_AA)
    else:
        # Calibration complete message
        cv2.putText(frame, cal_status, (card_x1 + 15, y_offset + 5), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.4, neon_green, 1, cv2.LINE_AA)

    # --- 3. Draw Active Drowsiness Warning (Flashing Screen Elements) ---
    if is_drowsy:
        # Flash alarm state: flash every 300ms
        flash_state = int(time.time() * 4.0) % 2 == 0
        
        if flash_state:
            # 1. Full screen thick flashing red border
            border_thickness = 10
            cv2.rectangle(frame, (0, 0), (w, h), neon_red, border_thickness)
            
            # 2. Giant warning overlay box in upper center of screen
            warn_x1, warn_y1 = int(w * 0.15), int(h * 0.4)
            warn_x2, warn_y2 = int(w * 0.85), int(h * 0.6)
            
            # Draw solid dark red box
            draw_glass_card(frame, warn_x1, warn_y1, warn_x2, warn_y2, alpha=0.85, bg_color=(10, 10, 80))
            
            # Add text inside the warning box
            cv2.putText(frame, "DROWSINESS DETECTED!", (warn_x1 + 25, warn_y1 + 55), 
                        cv2.FONT_HERSHEY_TRIPLEX, 0.8, neon_red, 2, cv2.LINE_AA)
            cv2.putText(frame, "WAKE UP!", (warn_x1 + 140, warn_y1 + 85), 
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2, cv2.LINE_AA)
    
    # --- 4. No Face Alert ---
    elif not stats["face_detected"]:
        # Show warning that face is missing
        cv2.putText(frame, "NO FACE DETECTED", (int(w * 0.35), int(h * 0.5)), 
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, neon_cyan, 2, cv2.LINE_AA)
