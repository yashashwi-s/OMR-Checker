#!/usr/bin/env python3
"""
Interactive ROI (Region of Interest) Selector
Allows you to click and drag over the actual boxes on your OMR sheet to
calculate perfectly accurate fractional regions for the scanner.

Usage:
    mamba run -n omr python select_regions.py image.png
"""

import cv2
import json
import sys
import numpy as np
import os
import omr_scanner

REGIONS_TO_SELECT = [
    "roll",
    "dob",
    "paper",
    "category",
    "sub_category",
    "gender",
    "answers_col1",
    "answers_col2",
    "answers_col3"
]

current_region_idx = 0
drawing = False
ix, iy = -1, -1
img = None
original_img = None
regions = {}

def draw_rectangle(event, x, y, flags, param):
    global ix, iy, drawing, img, original_img, current_region_idx, regions

    if current_region_idx >= len(REGIONS_TO_SELECT):
        return

    if event == cv2.EVENT_LBUTTONDOWN:
        drawing = True
        ix, iy = x, y

    elif event == cv2.EVENT_MOUSEMOVE:
        if drawing:
            img = original_img.copy()
            cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 2)
            region_name = REGIONS_TO_SELECT[current_region_idx]
            cv2.putText(img, f"Drawing: {region_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    elif event == cv2.EVENT_LBUTTONUP:
        drawing = False
        img = original_img.copy()
        cv2.rectangle(img, (ix, iy), (x, y), (0, 255, 0), 2)
        
        # Ensure correct coordinates regardless of drag direction
        x0, y0 = min(ix, x), min(iy, y)
        x1, y1 = max(ix, x), max(iy, y)
        
        # Calculate fractions based on image size
        h, w = original_img.shape[:2]
        fx0 = round(x0 / w, 4)
        fy0 = round(y0 / h, 4)
        fx1 = round(x1 / w, 4)
        fy1 = round(y1 / h, 4)
        
        region_name = REGIONS_TO_SELECT[current_region_idx]
        regions[region_name] = [fx0, fy0, fx1, fy1]
        
        print(f"Captured '{region_name}': {fx0}, {fy0}, {fx1}, {fy1}")
        
        # Highlight permanently
        cv2.rectangle(original_img, (x0, y0), (x1, y1), (0, 255, 0), 2)
        cv2.putText(original_img, region_name, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        current_region_idx += 1
        update_instructions()

def update_instructions():
    global img
    if current_region_idx < len(REGIONS_TO_SELECT):
        region_name = REGIONS_TO_SELECT[current_region_idx]
        print(f"\n---> Please click and drag to draw a box around: {region_name.upper()}")
        cv2.putText(img, f"Next: {region_name}", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
    else:
        print("\nAll regions selected! Saving to regions.json...")
        with open("regions.json", "w") as f:
            json.dump(regions, f, indent=4)
        print("Saved. You can close the window now.")
        cv2.putText(img, "Done! Saved to regions.json. Press any key to exit.", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 0, 0), 2)

def main():
    global img, original_img

    if len(sys.argv) < 2:
        print("Usage: python select_regions.py <image_path>")
        sys.exit(1)

    img_path = sys.argv[1]
    raw_img = cv2.imread(img_path)
    if raw_img is None:
        print(f"Could not read {img_path}")
        sys.exit(1)

    # Resize just like the scanner does
    h, w = raw_img.shape[:2]
    if max(h, w) > 1500:
        s = 1500 / max(h, w)
        raw_img = cv2.resize(raw_img, (int(w * s), int(h * s)))

    # Apply the scanner's warping to get the flattened image
    print("Flattening image using scanner logic...")
    omr_scanner.BATCH = True # Silence popups
    gray, dil = omr_scanner.preprocess(raw_img)
    cnt = omr_scanner.find_sheet(raw_img, dil)
    wc, wg = omr_scanner.warp(raw_img, gray, cnt)

    original_img = wc

    # Resize to fit screen for comfortable drawing
    h, w = original_img.shape[:2]
    max_dim = 900
    if max(h, w) > max_dim:
        s = max_dim / max(h, w)
        original_img = cv2.resize(original_img, (int(w * s), int(h * s)))

    img = original_img.copy()

    cv2.namedWindow('Interactive ROI Selector')
    cv2.setMouseCallback('Interactive ROI Selector', draw_rectangle)

    print("=" * 50)
    print(" INTERACTIVE REGION SELECTOR")
    print("=" * 50)
    print("Instructions:")
    print("1. A window will open showing your flattened image.")
    print("2. Click and drag to draw a tight box around ONLY THE BUBBLES for the requested section.")
    print("   Do NOT include the question numbers or the headers in the box!")
    print("3. Check the terminal to see what section you should draw next.")
    print("=" * 50)

    update_instructions()

    while True:
        cv2.imshow('Interactive ROI Selector', img)
        k = cv2.waitKey(20) & 0xFF
        if k == 27 or current_region_idx >= len(REGIONS_TO_SELECT): 
            # Exit on ESC or completion (wait for final keypress)
            if current_region_idx >= len(REGIONS_TO_SELECT):
                cv2.waitKey(0)
            break

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
