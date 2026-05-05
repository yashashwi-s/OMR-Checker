import cv2
import json
import numpy as np
import omr_scanner

omr_scanner.BATCH = True
raw_img = cv2.imread('image.png')
h, w = raw_img.shape[:2]
s = 1500 / max(h, w)
raw_img = cv2.resize(raw_img, (int(w * s), int(h * s)))

gray, dil = omr_scanner.preprocess(raw_img)
cnt = omr_scanner.find_sheet(raw_img, dil)
wc, wg = omr_scanner.warp(raw_img, gray, cnt)

with open('regions.json') as f:
    custom_regions = json.load(f)

for key in ["roll", "dob", "answers_col1"]:
    omr_scanner.REGIONS[key] = tuple(custom_regions[key])

print("Testing Roll Grid:")
patch = omr_scanner.crop(wg, "roll")
H, W = patch.shape
n_cols, n_rows = 9, 10
cw, rh = W / n_cols, H / n_rows
box_r = max(1, int(min(cw, rh) * 0.40))

max_ratio = 0
for c in range(n_cols):
    for r_idx in range(n_rows):
        cx = int((c + 0.5) * cw)
        cy = int((r_idx + 0.5) * rh)
        y0, y1 = max(0, cy-box_r), min(H, cy+box_r)
        x0, x1 = max(0, cx-box_r), min(W, cx+box_r)
        roi = patch[y0:y1, x0:x1]
        
        # Test adaptive threshold with C=25
        t = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 25)
        ratio = cv2.countNonZero(t) / t.size
        max_ratio = max(max_ratio, ratio)

print(f"Max fill ratio with C=25 is: {max_ratio:.2f}")

# What if we use C=30?
max_ratio_30 = 0
for c in range(n_cols):
    for r_idx in range(n_rows):
        cx = int((c + 0.5) * cw)
        cy = int((r_idx + 0.5) * rh)
        y0, y1 = max(0, cy-box_r), min(H, cy+box_r)
        x0, x1 = max(0, cx-box_r), min(W, cx+box_r)
        roi = patch[y0:y1, x0:x1]
        
        t = cv2.adaptiveThreshold(roi, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 30)
        ratio = cv2.countNonZero(t) / t.size
        max_ratio_30 = max(max_ratio_30, ratio)

print(f"Max fill ratio with C=30 is: {max_ratio_30:.2f}")
