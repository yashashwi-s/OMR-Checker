#!/usr/bin/env python3
"""
Phase 1 — Synthetic OMR Sheet Generator
Renders filled IIT-BHU-style OMR sheets as PNG + ground-truth JSON.

Usage:
    python generate_omr.py --count 20 --out output/sheets/
"""

import argparse, json, os, random, string
from datetime import date, timedelta
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ── Sheet dimensions (A4 @ 200 dpi) ─────────────────────────────────────────
W, H = 1654, 2339
MARGIN = 60  # px from edge

# ── ArUco spec ───────────────────────────────────────────────────────────────
ARUCO_DICT = cv2.aruco.DICT_4X4_50
ARUCO_SIZE = 60  # px
ARUCO_MARGIN = 30  # px from sheet edge (inside border)

# ── Colors ───────────────────────────────────────────────────────────────────
BLACK = (0, 0, 0)
DARK = (40, 40, 40)
GRAY = (160, 160, 160)
LIGHT = (220, 220, 220)
WHITE = (255, 255, 255)
FILL_COLOR = (25, 25, 25)  # darkened bubble fill

# ── Layout constants (pixel coordinates on the 1654×2339 canvas) ─────────────
# Header section
HEADER_Y = 40
HEADER_H = 160

# Roll No grid
ROLL_REGION = (33, 210, 496, 890)  # x0, y0, x1, y1
ROLL_COLS = 9
ROLL_ROWS = 10

# DOB grid
DOB_REGION = (513, 210, 1092, 890)  # x0, y0, x1, y1
DOB_COLS = 8
DOB_ROWS = 10

# Paper / Category / Sub-Category / Gender rows
PAPER_REGION = (33, 890, 364, 1050)
CATEGORY_REGION = (397, 870, 990, 1050)
SUBCAT_REGION = (1010, 870, 1290, 1050)
GENDER_REGION = (1310, 870, 1637, 1050)

# Answer grid  (3 column groups)
ANS_TOP = 1090
ANS_BOTTOM = 2240
ANS_GROUPS = [
    (33, 530),      # group 1 x-range, 17 questions
    (546, 1043),    # group 2 x-range, 17 questions
    (1060, 1557),   # group 3 x-range, 16 questions
]
Q_PER_GROUP = [17, 17, 16]
OPTS = 4
LETTERS = "ABCD"

# Timing dots column (left of answer grid)
TIMING_DOT_X = 18
TIMING_DOT_R = 6

# Labels
PAPER_LABELS = ["A", "B", "C", "D"]
CATEGORY_LABELS = ["UR", "SC", "ST", "OBC", "EWS"]
SUBCAT_LABELS = ["PWD", "ESM"]
SUBCAT_BUBBLES = ["P", "E"]
GENDER_LABELS = ["M", "F", "O"]


# ── ArUco marker generation ─────────────────────────────────────────────────
def make_aruco(marker_id, size=ARUCO_SIZE):
    """Generate an ArUco marker image as numpy array."""
    dictionary = cv2.aruco.getPredefinedDictionary(ARUCO_DICT)
    marker = cv2.aruco.generateImageMarker(dictionary, marker_id, size)
    return marker


def place_aruco_markers(img_np):
    """Place 4 ArUco markers at the corners. Returns corner positions."""
    h, w = img_np.shape[:2]
    positions = [
        (ARUCO_MARGIN, ARUCO_MARGIN),                          # top-left,  ID 0
        (w - ARUCO_MARGIN - ARUCO_SIZE, ARUCO_MARGIN),         # top-right, ID 1
        (w - ARUCO_MARGIN - ARUCO_SIZE, h - ARUCO_MARGIN - ARUCO_SIZE),  # bottom-right, ID 2
        (ARUCO_MARGIN, h - ARUCO_MARGIN - ARUCO_SIZE),         # bottom-left, ID 3
    ]
    corners = []
    for marker_id, (x, y) in enumerate(positions):
        marker = make_aruco(marker_id)
        # Convert marker to 3-channel
        marker_rgb = cv2.cvtColor(marker, cv2.COLOR_GRAY2RGB)
        img_np[y:y + ARUCO_SIZE, x:x + ARUCO_SIZE] = marker_rgb
        # Store center position
        corners.append([int(x + ARUCO_SIZE // 2), int(y + ARUCO_SIZE // 2)])
    return corners


# ── Drawing helpers ──────────────────────────────────────────────────────────
def get_font(size=18):
    """Try to load a clean font, fall back to default."""
    for name in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/SFNSText.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]:
        if os.path.exists(name):
            try:
                return ImageFont.truetype(name, size)
            except Exception:
                pass
    return ImageFont.load_default()


def draw_bubble(draw, cx, cy, r, filled=False):
    """Draw a single bubble (circle), optionally filled."""
    bbox = [cx - r, cy - r, cx + r, cy + r]
    if filled:
        draw.ellipse(bbox, fill=FILL_COLOR, outline=DARK)
    else:
        draw.ellipse(bbox, fill=None, outline=GRAY, width=2)


def draw_digit_grid(draw, region, n_cols, n_rows, values, font):
    """Draw a digit bubble grid and fill the specified values."""
    x0, y0, x1, y1 = region
    cw = (x1 - x0) / n_cols
    rh = (y1 - y0) / n_rows
    r = int(min(cw, rh) * 0.32)

    # Column headers
    for c in range(n_cols):
        cx = int(x0 + (c + 0.5) * cw)
        # Draw header box
        draw.rectangle([cx - r - 2, y0 - 28, cx + r + 2, y0 - 4], outline=GRAY, width=1)

    # Row labels + bubbles
    for row in range(n_rows):
        ry = int(y0 + (row + 0.5) * rh)
        # Row label
        draw.text((x0 - 22, ry - 8), str(row), fill=DARK, font=font)
        for c in range(n_cols):
            cx = int(x0 + (c + 0.5) * cw)
            filled = (values is not None and c < len(values) and int(values[c]) == row)
            draw_bubble(draw, cx, ry, r, filled)


def draw_option_row(draw, region, labels, selected, font, bubbles=None):
    """Draw a single-row option selector."""
    x0, y0, x1, y1 = region
    n = len(labels)
    ow = (x1 - x0) / n
    r = int(min(ow, y1 - y0) * 0.25)
    cy = int((y0 + y1) / 2)

    for i, label in enumerate(labels):
        cx = int(x0 + (i + 0.5) * ow)
        filled = (selected is not None and i == selected)
        draw_bubble(draw, cx, cy, r, filled)
        
        # Text inside bubble if provided (like P, E)
        if bubbles:
            tw = font.getlength(bubbles[i]) if hasattr(font, 'getlength') else 8
            draw.text((cx - tw // 2, cy - 8), bubbles[i], fill=WHITE if filled else DARK, font=font)
            
        # Label below bubble
        tw = font.getlength(label) if hasattr(font, 'getlength') else len(label) * 8
        draw.text((cx - tw // 2, cy + r + 4), label, fill=DARK, font=font)


def draw_answer_grid(draw, all_answers, font):
    """Draw the 50-question answer grid with 3 column groups."""
    q_idx = 0
    timing_dots = []
    total_h = ANS_BOTTOM - ANS_TOP

    for g, (gx0, gx1) in enumerate(ANS_GROUPS):
        nq = Q_PER_GROUP[g]
        rh = total_h / nq
        ow = (gx1 - gx0) / OPTS
        r = int(min(rh, ow) * 0.28)

        # Column headers (A B C D)
        for o in range(OPTS):
            cx = int(gx0 + (o + 0.5) * ow)
            draw.text((cx - 4, ANS_TOP - 24), LETTERS[o], fill=DARK, font=font)

        for q in range(nq):
            ry = int(ANS_TOP + (q + 0.5) * rh)
            # Question number label
            qn = q_idx + 1
            draw.text((gx0 - 30, ry - 8), str(qn), fill=DARK, font=font)

            # Timing dot for this row (left edge)
            if g == 0:  # Only first column group gets timing dots
                dot_y = ry
                timing_dots.append([TIMING_DOT_X, dot_y])
                draw.ellipse(
                    [TIMING_DOT_X - TIMING_DOT_R, dot_y - TIMING_DOT_R,
                     TIMING_DOT_X + TIMING_DOT_R, dot_y + TIMING_DOT_R],
                    fill=BLACK
                )

            for o in range(OPTS):
                cx = int(gx0 + (o + 0.5) * ow)
                filled = (all_answers is not None and q_idx < len(all_answers)
                          and all_answers[q_idx] == o)
                draw_bubble(draw, cx, ry, r, filled)
            q_idx += 1

    return timing_dots


# ── Random data generation ───────────────────────────────────────────────────
def random_roll():
    return "".join(random.choices(string.digits, k=9))


def random_dob():
    start = date(1998, 1, 1)
    end = date(2006, 12, 31)
    d = start + timedelta(days=random.randint(0, (end - start).days))
    return d.strftime("%d%m%Y")


def random_answers(n=50):
    return [random.randint(0, OPTS - 1) for _ in range(n)]


# ── Sheet renderer ───────────────────────────────────────────────────────────
def render_sheet(sheet_id=1):
    """Render a complete OMR sheet. Returns (PIL Image, ground_truth dict)."""
    img = Image.new("RGB", (W, H), WHITE)
    draw = ImageDraw.Draw(img)
    font = get_font(16)
    font_lg = get_font(22)
    font_title = get_font(28)

    # ── Border ───────────────────────────────────────────────────────────
    draw.rectangle([MARGIN, MARGIN, W - MARGIN, H - MARGIN], outline=BLACK, width=3)

    # ── Header ───────────────────────────────────────────────────────────
    title = "Indian Institute of Technology (BHU) Varanasi"
    subtitle = "OMR ANSWER SHEET"
    tw = font_title.getlength(title) if hasattr(font_title, 'getlength') else 400
    draw.text(((W - tw) // 2, HEADER_Y + 20), title, fill=BLACK, font=font_title)
    sw = font_lg.getlength(subtitle) if hasattr(font_lg, 'getlength') else 200
    draw.text(((W - sw) // 2, HEADER_Y + 60), subtitle, fill=BLACK, font=font_lg)

    # Sheet number
    sid_text = f"Sheet S.No. {sheet_id:04d}"
    draw.text((W - MARGIN - 260, HEADER_Y + 20), sid_text, fill=BLACK, font=font_lg)

    # ── Section labels ───────────────────────────────────────────────────
    draw.text((ROLL_REGION[0], ROLL_REGION[1] - 30), "1. Roll No.", fill=BLACK, font=font_lg)
    draw.text((DOB_REGION[0], DOB_REGION[1] - 30), "2. Date of Birth", fill=BLACK, font=font_lg)
    draw.text((PAPER_REGION[0], PAPER_REGION[1] - 30), "4. Question Paper Set", fill=BLACK, font=font)
    draw.text((CATEGORY_REGION[0], CATEGORY_REGION[1] - 30), "5. Category", fill=BLACK, font=font)
    draw.text((SUBCAT_REGION[0], SUBCAT_REGION[1] - 30), "6. Sub-Category", fill=BLACK, font=font)
    draw.text((GENDER_REGION[0], GENDER_REGION[1] - 30), "7. Gender", fill=BLACK, font=font)

    # ── Separator lines ──────────────────────────────────────────────────
    draw.line([(MARGIN, ANS_TOP - 40), (W - MARGIN, ANS_TOP - 40)], fill=GRAY, width=2)
    draw.line([(MARGIN, PAPER_REGION[1] - 40), (W - MARGIN, PAPER_REGION[1] - 40)], fill=GRAY, width=1)

    # ── Generate random data ─────────────────────────────────────────────
    if sheet_id == 0:
        # Blank template
        roll, dob = None, None
        gender_idx, paper_idx, cat_idx, subcat_idx = None, None, None, None
        answers = []
    else:
        roll = random_roll()
        dob = random_dob()
        gender_idx = random.randint(0, len(GENDER_LABELS) - 1)
        paper_idx = random.randint(0, len(PAPER_LABELS) - 1)
        cat_idx = random.randint(0, len(CATEGORY_LABELS) - 1)
        subcat_idx = random.randint(0, len(SUBCAT_LABELS) - 1) if random.random() > 0.5 else None
        answers = random_answers(50)

    # ── Draw grids ───────────────────────────────────────────────────────
    draw_digit_grid(draw, ROLL_REGION, ROLL_COLS, ROLL_ROWS, roll, font)
    draw_digit_grid(draw, DOB_REGION, DOB_COLS, DOB_ROWS, dob, font)
    draw_option_row(draw, PAPER_REGION, PAPER_LABELS, paper_idx, font)
    draw_option_row(draw, CATEGORY_REGION, CATEGORY_LABELS, cat_idx, font)
    draw_option_row(draw, SUBCAT_REGION, SUBCAT_LABELS, subcat_idx, font, bubbles=SUBCAT_BUBBLES)
    draw_option_row(draw, GENDER_REGION, GENDER_LABELS, gender_idx, font)
    timing_dots = draw_answer_grid(draw, answers if answers else None, font)

    # ── Convert to numpy for ArUco placement ─────────────────────────────
    img_np = np.array(img)
    aruco_corners = place_aruco_markers(img_np)
    img = Image.fromarray(img_np)

    # ── Signature area ───────────────────────────────────────────────────
    draw2 = ImageDraw.Draw(img)
    draw2.rectangle([MARGIN + 10, H - MARGIN - 80, W // 2, H - MARGIN - 10], outline=GRAY, width=1)
    draw2.text((MARGIN + 14, H - MARGIN - 75), "Signature of Candidate", fill=GRAY, font=font)
    draw2.rectangle([W // 2 + 40, H - MARGIN - 80, W - MARGIN - 10, H - MARGIN - 10], outline=GRAY, width=1)
    draw2.text((W // 2 + 44, H - MARGIN - 75), "Signature of Invigilator", fill=GRAY, font=font)

    # ── Ground truth ─────────────────────────────────────────────────────
    if sheet_id > 0:
        dob_fmt = f"{dob[0:2]}/{dob[2:4]}/{dob[4:8]}"
        ground_truth = {
            "sheet_id": f"omr_{sheet_id:04d}",
            "roll_no": roll,
            "dob": dob_fmt,
            "gender": GENDER_LABELS[gender_idx],
            "paper_set": PAPER_LABELS[paper_idx],
            "category": CATEGORY_LABELS[cat_idx],
            "sub_category": SUBCAT_LABELS[subcat_idx] if subcat_idx is not None else "",
            "answers": [LETTERS[a] for a in answers],
            "aruco_corners": aruco_corners,
            "timing_dots": timing_dots,
        }
    else:
        ground_truth = {"sheet_id": "blank_template", "aruco_corners": aruco_corners, "timing_dots": timing_dots}

    return img, ground_truth


# ── Main ─────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Generate synthetic OMR sheets")
    parser.add_argument("--count", type=int, default=10, help="Number of sheets to generate")
    parser.add_argument("--out", type=str, default="output/sheets/", help="Output directory")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    print(f"Generating {args.count} OMR sheets → {out}/")
    
    # Generate blank template first
    img, gt = render_sheet(sheet_id=0)
    img.save(str(out / "blank_template.png"))
    with open(out / "blank_template.json", "w") as f:
        json.dump(gt, f, indent=2)
    print("  [0] Generated blank_template.png")

    for i in range(1, args.count + 1):
        img, gt = render_sheet(sheet_id=i)
        png_path = out / f"omr_{i:04d}.png"
        json_path = out / f"omr_{i:04d}.json"
        img.save(str(png_path))
        with open(json_path, "w") as f:
            json.dump(gt, f, indent=2)
        print(f"  [{i}/{args.count}] {png_path.name}  roll={gt['roll_no']}")

    print(f"Done. {args.count} sheets saved to {out}/")


if __name__ == "__main__":
    main()
