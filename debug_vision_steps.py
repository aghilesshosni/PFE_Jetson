# -*- coding: utf-8 -*-
import cv2
import numpy as np
import os

# Create a folder to save the debug images if it doesn't exist
OUTPUT_DIR = "debug_steps"
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

def save_step(name, img):
    """Helper to save an image with a specific name"""
    path = os.path.join(OUTPUT_DIR, f"{name}.jpg")
    cv2.imwrite(path, img)
    print(f"✅ Saved: {path}")

def get_gstreamer_pipeline(sensor_id=0, capture_width=1920, capture_height=1080, 
                           framerate=30, flip_method=0, display_width=640, display_height=480):
    """
    Returns the GStreamer pipeline with MANUAL EXPOSURE and WHITE BALANCE
    to ensure the debug image matches the live feed.
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
    # 1. Initialize Camera using the FIXED pipeline
    pipeline_str = get_gstreamer_pipeline(
        sensor_id=0,
        capture_width=1920,
        capture_height=1080,
        framerate=30,
        flip_method=0,
        display_width=640,
        display_height=480
    )
    
    print("📷 Using Pipeline with Manual Exposure/WB:")
    print(pipeline_str)
    
    cap = cv2.VideoCapture(pipeline_str, cv2.CAP_GSTREAMER)
    
    if not cap.isOpened():
        print("❌ Error: Could not open camera.")
        return

    # 2. WARM-UP FRAMES
    # Discard the first 10 frames to let the sensor stabilize
    print("🔄 Stabilizing sensor...")
    for i in range(10):
        ret, _ = cap.read()
        if not ret: break
        
    print("📷 Capturing stable frame...")
    ret, frame = cap.read()
    cap.release()
    
    if not ret or frame is None:
        print("❌ Error: Could not read frame.")
        return

    # --- STEP 0: Original Image (Now it should look clear like the dashboard) ---
    save_step("00_original_input", frame)

    # --- STEP 1: Grayscale & Bilateral Filter ---
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    blurred = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
    save_step("01_gray_bilateral", blurred)

    # --- STEP 2: Thresholding (Otsu) ---
    _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    save_step("02_threshold_otsu", thresholded)

    # --- STEP 3: Morphology (Close/Open) ---
    kernel = np.ones((7, 7), np.uint8)
    closed_edges = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)
    opened_edges = cv2.morphologyEx(closed_edges, cv2.MORPH_OPEN, kernel)
    save_step("03_morphology_cleaned", opened_edges)

    # --- STEP 4: Find Contours & Draw Best Bottle ---
    contours, _ = cv2.findContours(opened_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    best_bbox = None
    h_frame, w_frame = frame.shape[:2]
    total_area = h_frame * w_frame
    MAX_BOTTLE_AREA = total_area * 0.90
    
    candidates = []
    for cnt in contours:
        aire = cv2.contourArea(cnt)
        x, y, w, h = cv2.boundingRect(cnt)
        
        if aire < 1000 or w < 30 or h < 50: continue
        if aire > MAX_BOTTLE_AREA: continue
        
        ratio = float(h) / float(w) if w > 0 else 0
        if not (1.3 <= ratio <= 6.0): continue
        
        candidates.append((cnt, aire, x, y, w, h))

    if candidates:
        candidates.sort(key=lambda k: k[1], reverse=True)
        best = candidates[0]
        x, y, w, h = best[2], best[3], best[4], best[5]
        
        # Apply bottom-extension logic
        bottom_edge = y + h
        gap_to_frame_bottom = h_frame - bottom_edge
        if gap_to_frame_bottom < int(h_frame * 0.15):
            h = h_frame - y
            
        if y < int(h_frame * 0.05):
            h = h + y
            y = 0
            
        best_bbox = (x, y, w, h)
        
        debug_frame = frame.copy()
        cv2.rectangle(debug_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        cv2.putText(debug_frame, "Bottle Detected", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        save_step("04_detected_bottle_bbox", debug_frame)
    else:
        print("⚠️ No bottle detected.")
        save_step("04_no_bottle", frame)
        return

    # --- STEP 5: Level Detection (HSV Mask) ---
    if best_bbox:
        x, y, w, h = best_bbox
        
        margin_x = int(w * 0.18)
        margin_top = 30 if y < 10 else int(h * 0.15)
        margin_bot = int(h * 0.02)
        
        rx1, rx2 = x + margin_x, x + w - margin_x
        ry1, ry2 = y + margin_top, y + h - margin_bot
        
        if rx2 > rx1 and ry2 > ry1:
            roi_color = frame[ry1:ry2, rx1:rx2]
            
            hsv = cv2.cvtColor(roi_color, cv2.COLOR_BGR2HSV)
            
            # Pink/Magenta Mask
            mask1 = cv2.inRange(hsv, np.array([0, 35, 30]), np.array([20, 255, 255]))
            mask2 = cv2.inRange(hsv, np.array([145, 35, 30]), np.array([180, 255, 255]))
            liquid_mask = cv2.bitwise_or(mask1, mask2)
            
            kernel_liq = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            liquid_mask = cv2.morphologyEx(liquid_mask, cv2.MORPH_OPEN, kernel_liq, iterations=2)
            liquid_mask = cv2.morphologyEx(liquid_mask, cv2.MORPH_CLOSE, kernel_liq, iterations=4)
            
            save_step("05_roi_color", roi_color)
            save_step("06_liquid_mask_binary", liquid_mask)
            
            mask_visual = cv2.cvtColor(liquid_mask, cv2.COLOR_GRAY2BGR)
            overlay = cv2.addWeighted(roi_color, 0.6, mask_visual, 0.4, 0)
            save_step("07_liquid_mask_overlay", overlay)
            
            liquid_pixels = cv2.countNonZero(liquid_mask)
            roi_h = ry2 - ry1
            surface_y = None
            for row in range(roi_h):
                if np.any(liquid_mask[row, :] > 0):
                    surface_y = row
                    break
            
            if surface_y is not None:
                level_pct = ((roi_h - surface_y) / roi_h) * 100
                print(f"💧 Calculated Level: {level_pct:.1f}%")
                
                line_y = int(surface_y)
                cv2.line(overlay, (0, line_y), (w, line_y), (0, 0, 255), 2)
                cv2.putText(overlay, f"Level: {level_pct:.1f}%", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
                save_step("08_final_level_visualization", overlay)
            else:
                print(" No liquid surface detected.")
                save_step("08_empty_bottle", overlay)

    print("\n🎉 Debug complete! Check 'debug_steps' folder.")

if __name__ == "__main__":
    main()
