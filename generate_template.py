import json

SCALE = 200 / 72.0
PAGE_HEIGHT_PT = 841.89
PAGE_WIDTH_PT = 595.27

def pt_to_px(x, y):
    return [int(round(x * SCALE)), int(round((PAGE_HEIGHT_PT - y) * SCALE))]

def dist_to_px(d):
    return int(round(d * SCALE))

template = {
    "pageDimensions": [
        int(round(PAGE_WIDTH_PT * SCALE)),
        int(round(PAGE_HEIGHT_PT * SCALE))
    ],
    "bubbleDimensions": [
        dist_to_px(10), # diameter is 10 pt
        dist_to_px(10)
    ],
    "customLabels": {},
    "fieldBlocks": {},
    "preProcessors": []
}

# --- Application Number ---
# x starts at 58, y starts at 615 (for j=0)
# Gap in x = 16, Gap in y = 16 (downwards)
app_origin_px = pt_to_px(58, 615)
template["fieldBlocks"]["Application_Number"] = {
    "fieldType": "QTYPE_INT",
    "fieldLabels": ["app1..10"],
    "bubblesGap": dist_to_px(16),
    "labelsGap": dist_to_px(16),
    "origin": app_origin_px
}

# --- Date of Birth ---
# x starts at 258, y starts at 615 (for j=0)
dob_origin_px = pt_to_px(258, 615)
template["fieldBlocks"]["Date_of_Birth"] = {
    "fieldType": "QTYPE_INT",
    "fieldLabels": ["dob1..8"],
    "bubblesGap": dist_to_px(16),
    "labelsGap": dist_to_px(16),
    "origin": dob_origin_px
}

# --- Category ---
# i = 0 to 4. x = 463, y = 615 - i*16
cat_origin_px = pt_to_px(463, 615)
template["fieldBlocks"]["Category"] = {
    "bubbleValues": ["GEN", "EWS", "OBC", "SC", "ST"],
    "fieldLabels": ["Category"],
    "direction": "vertical",
    "bubblesGap": dist_to_px(16),
    "labelsGap": 0,
    "origin": cat_origin_px
}

# --- Answers ---
# 4 columns, 10 rows per column.
# col = 0 to 3, row = 0 to 9
# x_offset = 50 + col * 125. Option A starts at x_offset + 37. Gap is 20.
# y starts at 375. Gap is 22 (downwards).
for col in range(4):
    start_q = col * 10 + 1
    end_q = col * 10 + 10
    x_pt = 50 + col * 125 + 37
    y_pt = 375
    
    ans_origin_px = pt_to_px(x_pt, y_pt)
    
    block_name = f"Answers_Q{start_q}_to_Q{end_q}"
    template["fieldBlocks"][block_name] = {
        "fieldType": "QTYPE_MCQ4",
        "fieldLabels": [f"q{start_q}..{end_q}"],
        "bubblesGap": dist_to_px(20),
        "labelsGap": dist_to_px(22),
        "origin": ans_origin_px
    }

with open("template.json", "w") as f:
    json.dump(template, f, indent=2)

print("Generated template.json successfully.")
