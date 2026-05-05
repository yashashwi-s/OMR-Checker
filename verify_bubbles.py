import cv2
import json
import numpy as np
import omr_scanner

def main():
    print("Loading image.png and regions.json...")
    raw_img = cv2.imread('image.png')
    h, w = raw_img.shape[:2]
    if max(h, w) > 1500:
        s = 1500 / max(h, w)
        raw_img = cv2.resize(raw_img, (int(w * s), int(h * s)))

    omr_scanner.BATCH = True
    gray, dil = omr_scanner.preprocess(raw_img)
    cnt = omr_scanner.find_sheet(raw_img, dil)
    wc, wg = omr_scanner.warp(raw_img, gray, cnt)

    with open('regions.json') as f:
        custom_regions = json.load(f)

    # We will draw on the color warped image
    debug_img = wc.copy()

    def draw_grid_dots(key, n_cols, n_rows, color=(0, 0, 255)):
        if key not in custom_regions: return
        x0f, y0f, x1f, y1f = custom_regions[key]
        H, W = wg.shape
        x0, y0, x1, y1 = int(x0f*W), int(y0f*H), int(x1f*W), int(y1f*H)
        
        cv2.rectangle(debug_img, (x0, y0), (x1, y1), color, 2)
        
        cw = (x1 - x0) / n_cols
        rh = (y1 - y0) / n_rows
        
        for c in range(n_cols):
            for r in range(n_rows):
                cx = int(x0 + (c + 0.5) * cw)
                cy = int(y0 + (r + 0.5) * rh)
                # Draw a small dot at the calculated center
                cv2.circle(debug_img, (cx, cy), 3, color, -1)
                # Draw the box_r that we test
                box_r = max(1, int(min(cw, rh) * 0.40))
                cv2.rectangle(debug_img, (cx-box_r, cy-box_r), (cx+box_r, cy+box_r), (0, 255, 0), 1)

    print("Drawing Roll...")
    draw_grid_dots("roll", 9, 10, (255, 0, 0)) # Blue
    print("Drawing DOB...")
    draw_grid_dots("dob", 8, 10, (0, 165, 255)) # Orange
    print("Drawing Paper...")
    draw_grid_dots("paper", 4, 1, (0, 255, 255)) # Yellow
    print("Drawing Category...")
    draw_grid_dots("category", 5, 1, (255, 0, 255)) # Pink
    print("Drawing Sub-Category...")
    draw_grid_dots("sub_category", 2, 1, (0, 255, 0)) # Green
    print("Drawing Gender...")
    draw_grid_dots("gender", 3, 1, (0, 0, 255)) # Red

    for c_key in ["answers_col1", "answers_col2", "answers_col3"]:
        if c_key in custom_regions:
            print(f"Drawing {c_key}...")
            ax0f, ay0f, ax1f, ay1f = custom_regions[c_key]
            H, W = wg.shape
            ax0, ay0, ax1, ay1 = int(ax0f*W), int(ay0f*H), int(ax1f*W), int(ay1f*H)
            cv2.rectangle(debug_img, (ax0, ay0), (ax1, ay1), (255, 255, 0), 2) # Cyan
            
            nq = 17 if c_key != "answers_col3" else 16
            OPTS = 4
            cw = (ax1 - ax0) / OPTS
            rh = (ay1 - ay0) / nq
            
            for q in range(nq):
                for o in range(OPTS):
                    cx = int(ax0 + (o + 0.5) * cw)
                    cy = int(ay0 + (q + 0.5) * rh)
                    cv2.circle(debug_img, (cx, cy), 3, (255, 255, 0), -1)
                    box_r = max(1, int(min(cw, rh) * 0.40))
                    cv2.rectangle(debug_img, (cx-box_r, cy-box_r), (cx+box_r, cy+box_r), (0, 255, 0), 1)

    cv2.imwrite("debug_backend_vision.jpg", debug_img)
    print("Saved 'debug_backend_vision.jpg'!")
    
if __name__ == "__main__":
    main()
