# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os

# Create a folder to save the debug images
OUTPUT_DIR = "debug_level_steps"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def save_step(name, img):
    """Helper to save an image with a specific name"""
    if img is None:
        print(f"⚠️ Skipping {name} (Image is None)")
        return
    path = os.path.join(OUTPUT_DIR, f"{name}.jpg")
    cv2.imwrite(path, img)
    print(f"✅ Saved: {path}")

def get_gstreamer_pipeline(sensor_id=0, capture_width=1920, capture_height=1080, 
                           framerate=30, flip_method=0, display_width=640, display_height=480):
    """
    Returns the GStreamer pipeline with MANUAL EXPOSURE and WHITE BALANCE.
    """
    return (
            "nvarguscamerasrc sensor-id=%d ! "
            "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
        % (
            sensor_id,
            capture_width,
            capture_height,
            framerate,
            flip_method,
            display_width,
            display_height,
        )
    )

def main():
    print("📷 Initializing Camera...")
    pipeline_str = get_gstreamer_pipeline()
    
    cap = cv2.VideoCapture(pipeline_str, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera.")
        return

    # Warm-up frames
    print("🔄 Stabilizing sensor...")
    for i in range(10):
        ret, _ = cap.read()
        if not ret: break
        
    print("📷 Capturing stable frame...")
    ret, full_frame = cap.read()
    cap.release()
    
    if not ret or full_frame is None:
        print("❌ Error: Could not read frame.")
        return

    h_frame, w_frame = full_frame.shape[:2]

    # --- STEP 0: Original Full Frame ---
    save_step("00_full_frame_original", full_frame)

    # --- DEFINE SEARCH ZONE (ROI) FOR LIQUID ---
    # Instead of detecting the bottle first, we assume the bottle is roughly centered.
    # We define a ROI that covers the bottom 70% of the image and the center 60% of the width.
    # This ensures we only look for liquid where it actually exists.
    
    roi_x_start = int(w_frame * 0.20) # Start at 20% width
    roi_x_end   = int(w_frame * 0.80) # End at 80% width
    roi_y_start = int(h_frame * 0.30) # Start at 30% height (ignore the neck/top)
    roi_y_end   = h_frame             # Go to the bottom
    
    # Extract the Liquid Search ROI
    liquid_roi = full_frame[roi_y_start:roi_y_end, roi_x_start:roi_x_end]
    
    # Visualize the Search Zone on the full frame
    debug_frame = full_frame.copy()
    cv2.rectangle(debug_frame, (roi_x_start, roi_y_start), (roi_x_end, roi_y_end), (255, 0, 255), 2)
    cv2.putText(debug_frame, "Liquid Search Zone", (roi_x_start, roi_y_start - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 0, 255), 2)
    save_step("01_liquid_search_zone_defined", debug_frame)
    
    save_step("02_liquid_roi_cropped", liquid_roi)

    # --- LEVEL DETECTION PIPELINE (ON THE SEARCH ZONE) ---
    
    # 1. Convert to HSV
    hsv = cv2.cvtColor(liquid_roi, cv2.COLOR_BGR2HSV)
    
    # Save channels for debugging
    h_chan, s_chan, v_chan = cv2.split(hsv)
    save_step("03_hsv_hue", h_chan)
    save_step("04_hsv_sat", s_chan)
    save_step("05_hsv_val", v_chan)

    # 2. Create Pink/Magenta Mask (Your Exact Ranges)
    # Range 1: Red-Pink
    mask1 = cv2.inRange(hsv, np.array([0, 35, 30]), np.array([20, 255, 255]))
    # Range 2: Magenta-Purple
    mask2 = cv2.inRange(hsv, np.array([145, 35, 30]), np.array([180, 255, 255]))
    
    liquid_mask_raw = cv2.bitwise_or(mask1, mask2)
    save_step("06_liquid_mask_raw_binary", liquid_mask_raw)

    # 3. Morphological Cleaning (Open/Close)
    kernel_liq = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    liquid_mask_clean = cv2.morphologyEx(liquid_mask_raw, cv2.MORPH_OPEN, kernel_liq, iterations=2)
    liquid_mask_clean = cv2.morphologyEx(liquid_mask_clean, cv2.MORPH_CLOSE, kernel_liq, iterations=4)
    save_step("07_liquid_mask_cleaned", liquid_mask_clean)

    # 4. Visualize Mask on Top of ROI
    mask_visual = cv2.cvtColor(liquid_mask_clean, cv2.COLOR_GRAY2BGR)
    overlay = cv2.addWeighted(liquid_roi, 0.6, mask_visual, 0.4, 0)
    
    # 5. Calculate Level
    roi_h, roi_w = liquid_roi.shape[:2]
    
    # Find the topmost row that has liquid pixels
    surface_y = None
    for row in range(roi_h):
        if np.any(liquid_mask_clean[row, :] > 0):
            surface_y = row
            break

    if surface_y is not None:
        # Height of liquid is from the bottom up to the surface
        liquid_px_height = roi_h - surface_y
        pourcentage = float(np.clip((liquid_px_height / roi_h) * 100.0, 0.0, 100.0))
        
        print(f"💧 Surface Row (in ROI): {surface_y}")
        print(f"💧 Liquid Height (px): {liquid_px_height}")
        print(f"💧 Calculated Level: {pourcentage:.1f}%")
        
        # Draw the level line on the overlay
        line_y = int(surface_y)
        cv2.line(overlay, (0, line_y), (roi_w, line_y), (0, 0, 255), 2)
        cv2.putText(overlay, f"Level: {pourcentage:.1f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
        
        save_step("08_level_result_on_roi", overlay)
        
        # Map back to full frame for final visualization
        full_frame_viz = full_frame.copy()
        
        # Calculate absolute coordinates for the line
        abs_line_y = roi_y_start + line_y
        abs_x_start = roi_x_start
        abs_x_end = roi_x_end
        
        # Draw the line on the full frame
        cv2.line(full_frame_viz, (abs_x_start, abs_line_y), (abs_x_end, abs_line_y), (0, 0, 255), 3)
        cv2.putText(full_frame_viz, f"Level: {pourcentage:.1f}%", (abs_x_start, abs_line_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Draw the search zone again for context
        cv2.rectangle(full_frame_viz, (roi_x_start, roi_y_start), (roi_x_end, roi_y_end), (255, 0, 255), 1)
        
        save_step("09_full_frame_final_level", full_frame_viz)
        
    else:
        print(" No liquid detected in search zone.")
        save_step("08_empty_result", overlay)
        
        full_frame_viz = full_frame.copy()
        cv2.rectangle(full_frame_viz, (roi_x_start, roi_y_start), (roi_x_end, roi_y_end), (255, 0, 255), 1)
        cv2.putText(full_frame_viz, "NO LIQUID DETECTED", (roi_x_start, roi_y_start - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        save_step("09_full_frame_empty", full_frame_viz)

    print("\n Debug complete! Check 'debug_level_steps' folder.")

if __name__ == "__main__":
    main()
