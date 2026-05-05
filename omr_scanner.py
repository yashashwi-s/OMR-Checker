#!/usr/bin/env python3
"""
IIT BHU OMR Scanner — Zero-config batch grading.

Just run:
    python omr_scanner.py

It will:
  1. Read all images from  responses/
  2. Detect each sheet's Paper Code (A/B/C/D)
  3. Grade using the matching key file  A.txt / B.txt / C.txt / D.txt
  4. Append every row to  grades.csv

Optional overrides:
    python omr_scanner.py <folder_or_image> [out.csv]
"""

import cv2, numpy as np, sys, os, csv, glob
from datetime import datetime

# ── Hardcoded paths ───────────────────────────────────────────────────────────
SCAN_FOLDER = "responses"
CSV_PATH    = "grades.csv"
KEY_FILES   = {"A": "A.txt", "B": "B.txt", "C": "C.txt", "D": "D.txt"}

# ── Layout ────────────────────────────────────────────────────────────────────
GRID_TOP    = 0.44
GRID_BOTTOM = 0.96
COL_GROUPS  = [(0.01, 0.33), (0.33, 0.65), (0.65, 0.99)]
Q_PER_GROUP = [17, 17, 16]
OPTS        = 4

# Default Regions (will be overridden by regions.json if it exists)
REGIONS = {
    "roll":         (0.02, 0.09, 0.30, 0.38),
    "dob":          (0.31, 0.09, 0.66, 0.38),
    "paper":        (0.02, 0.38, 0.22, 0.45),
    "category":     (0.24, 0.37, 0.60, 0.45),
    "sub_category": (0.61, 0.37, 0.78, 0.45),
    "gender":       (0.79, 0.37, 0.99, 0.45),
}

import json
if os.path.exists("regions.json"):
    try:
        with open("regions.json") as f:
            custom_regions = json.load(f)
            
        # Load custom regions if present
        for key in ["roll", "dob", "paper", "category", "sub_category", "gender", "answers_col1", "answers_col2", "answers_col3"]:
            if key in custom_regions:
                REGIONS[key] = tuple(custom_regions[key])
            
        print("Loaded custom regions from regions.json")
    except Exception as e:
        print(f"[WARN] Could not load regions.json: {e}")

ROLL_COLS       = 9
DOB_COLS        = 8
CATEGORY_LABELS = ["UR", "SC", "ST", "OBC", "EWS"]
SUBCAT_LABELS   = ["PWD", "ESM"]
GENDER_LABELS   = ["M", "F", "O"]
PAPER_LABELS    = ["A", "B", "C", "D"]
LETTERS         = "ABCD"
IMG_EXTS        = ("*.jpg","*.jpeg","*.png","*.bmp","*.tiff","*.webp")

WIN = "OMR Scanner"
cv2.namedWindow(WIN, cv2.WINDOW_NORMAL)
cv2.resizeWindow(WIN, 820, 1020)

# batch mode silences per-step windows; single mode shows everything
BATCH = False


# ── Display ───────────────────────────────────────────────────────────────────

def lbl(img, text, pos=(12,36), color=(0,255,80), sc=0.82):
    cv2.putText(img,text,pos,cv2.FONT_HERSHEY_SIMPLEX,sc,(0,0,0),4)
    cv2.putText(img,text,pos,cv2.FONT_HERSHEY_SIMPLEX,sc,color,2)

def show(img, title="", wait=700):
    if BATCH: return
    f = img.copy() if img.ndim==3 else cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
    if title: lbl(f,title)
    # Automatically save steps
    safe_title = title.replace(" ", "_").replace("→", "to").lower()
    cv2.imwrite(f"{safe_title}.jpg", f)

def scan(img, text="Scanning", steps=50, speed=15):
    if BATCH: return
    h,w = img.shape[:2]
    base = img if img.ndim==3 else cv2.cvtColor(img,cv2.COLOR_GRAY2BGR)
    for i in range(steps+1):
        y = int(h*i/steps)
        f = base.copy(); ov=f.copy()
        cv2.rectangle(ov,(0,max(0,y-20)),(w,y),(0,255,80),-1)
        cv2.addWeighted(ov,0.10,f,0.90,0,f)
        cv2.line(f,(0,y),(w,y),(0,255,80),2)
        lbl(f,f"{text}  {int(100*i/steps)}%")

def flash_region(base,x0,y0,x1,y1,label_text,color=(0,220,255),wait=300):
    if BATCH: return
    f=base.copy()
    cv2.rectangle(f,(x0,y0),(x1,y1),color,2)
    ov=f.copy(); cv2.rectangle(ov,(x0,y0),(x1,y1),color,-1)
    cv2.addWeighted(ov,0.15,f,0.85,0,f)
    lbl(f,label_text,pos=(x0,max(22,y0-6)),color=color)

def show_batch_progress(img, label, idx, total):
    f = img.copy()
    lbl(f, f"[{idx}/{total}]  {label}", color=(0,220,255))
    cv2.imshow(WIN, f); cv2.waitKey(1)


# ── Core CV ───────────────────────────────────────────────────────────────────

def order_pts(pts):
    pts = pts.reshape(4,2).astype("float32")
    s,d = pts.sum(1), np.diff(pts,axis=1)
    return np.array([pts[np.argmin(s)],pts[np.argmin(d)],
                     pts[np.argmax(s)],pts[np.argmax(d)]],dtype="float32")

def preprocess(img):
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray,(7,7),0)
    edges = cv2.Canny(blur,25,110)
    k = cv2.getStructuringElement(cv2.MORPH_RECT,(5,5))
    dil = cv2.dilate(edges,k,iterations=2)
    show(gray,"1  Grayscale"); show(dil,"2  Edges")
    return gray, dil

def find_sheet(img,dilated):
    cnts,_ = cv2.findContours(dilated,cv2.RETR_EXTERNAL,cv2.CHAIN_APPROX_SIMPLE)
    cnts   = sorted(cnts,key=cv2.contourArea,reverse=True)
    min_a  = img.shape[0]*img.shape[1]*0.07
    debug  = img.copy(); result=None
    for cnt in cnts[:20]:
        if cv2.contourArea(cnt)<min_a: break
        approx = cv2.approxPolyDP(cnt,0.02*cv2.arcLength(cnt,True),True)
        cv2.drawContours(debug,[approx],-1,(0,60,255),1)
        if len(approx)==4:
            result=approx
            cv2.drawContours(debug,[result],-1,(0,255,80),3)
            break
    if result is None:
        h,w=img.shape[:2]
        result=np.array([[0,0],[w,0],[w,h],[0,h]],dtype="float32").reshape(-1,1,2)
    show(debug,"3  Sheet Boundary",900)
    return result

def warp(img,gray,cnt):
    rect=order_pts(cnt)
    tl,tr,br,bl=rect
    w=int(max(np.linalg.norm(br-bl),np.linalg.norm(tr-tl)))
    h=int(max(np.linalg.norm(tr-br),np.linalg.norm(tl-bl)))
    M=cv2.getPerspectiveTransform(rect,np.float32([[0,0],[w-1,0],[w-1,h-1],[0,h-1]]))
    wc=cv2.warpPerspective(img,M,(w,h))
    wg=cv2.warpPerspective(gray,M,(w,h))
    show(wc,"4  Perspective Corrected",900)
    return wc,wg

def crop(wg, key):
    if key not in REGIONS: return None
    H, W = wg.shape
    x0, y0, x1, y1 = REGIONS[key]
    return wg[int(y0 * H):int(y1 * H), int(x0 * W):int(x1 * W)]

def check_bubble_fill(bubble_gray):
    """Calculates the percentage of dark pixels in a single bubble ROI."""
    if bubble_gray.size == 0: return 0.0
    # Use local adaptive threshold to ignore shadows.
    # Block size 21 is typically larger than the bubble, perfectly thresholding it locally.
    # C=30 heavily suppresses background shadows and thin printed lines.
    t = cv2.adaptiveThreshold(bubble_gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY_INV, 21, 30)
    return cv2.countNonZero(t) / t.size

def read_digit_grid(gray_patch, n_cols, n_rows=10):
    if gray_patch is None: return "", []
    H, W = gray_patch.shape
    cw, rh = W / n_cols, H / n_rows
    box_r = max(1, int(min(cw, rh) * 0.40))
    
    digits, confs = [], []
    for c in range(n_cols):
        ratios = []
        for r_idx in range(n_rows):
            cx = int((c + 0.5) * cw)
            cy = int((r_idx + 0.5) * rh)
            y0, y1 = max(0, cy-box_r), min(H, cy+box_r)
            x0, x1 = max(0, cx-box_r), min(W, cx+box_r)
            roi = gray_patch[y0:y1, x0:x1]
            fill_ratio = check_bubble_fill(roi)
            ratios.append(fill_ratio)
            
        best = int(np.argmax(ratios))
        # Pen mark occupies > 50%, printed text occupies < 30%
        if ratios[best] > 0.40:
            digits.append(str(best))
            confs.append(round(ratios[best], 2))
        else:
            digits.append("?")
            confs.append(0.0)
    return "".join(digits), confs

def read_option_row(gray_row, labels):
    if gray_row is None: return "?", 0.0
    H, W = gray_row.shape
    n = len(labels)
    cw = W / n
    box_r = max(1, int(min(cw, H) * 0.40))
    
    ratios = []
    for i in range(n):
        cx = int((i + 0.5) * cw)
        cy = int(H * 0.5)
        y0, y1 = max(0, cy-box_r), min(H, cy+box_r)
        x0, x1 = max(0, cx-box_r), min(W, cx+box_r)
        roi = gray_row[y0:y1, x0:x1]
        ratios.append(check_bubble_fill(roi))
        
    best = int(np.argmax(ratios))
    if ratios[best] > 0.40:
        return labels[best], round(ratios[best], 2)
    return "?", 0.0

def read_answers(wg):
    all_ans = []
    # Process each of the 3 answer columns specifically mapped by the user
    col_keys = ["answers_col1", "answers_col2", "answers_col3"]
    
    for g, c_key in enumerate(col_keys):
        gray_grid = crop(wg, c_key)
        if gray_grid is None:
            all_ans.extend([(-1, 0.0)] * Q_PER_GROUP[g])
            continue
            
        nq = Q_PER_GROUP[g]
        H, W = gray_grid.shape
        cw = W / OPTS; rh = H / nq
        box_r = max(1, int(min(cw, rh) * 0.40)) # Use larger box for adaptive thresholding
        
        for q in range(nq):
            ratios = []
            for o in range(OPTS):
                cx = int((o + 0.5) * cw)
                cy = int((q + 0.5) * rh)
                y0, y1 = max(0, cy-box_r), min(H, cy+box_r)
                x0, x1 = max(0, cx-box_r), min(W, cx+box_r)
                roi = gray_grid[y0:y1, x0:x1]
                ratios.append(check_bubble_fill(roi))
            
            best = int(np.argmax(ratios))
            if ratios[best] > 0.40:
                all_ans.append((best, round(ratios[best], 2)))
            else:
                all_ans.append((-1, 0.0))
    return all_ans


# ── Overlay (single mode only) ────────────────────────────────────────────────

def overlay_header(wc,wg,fields):
    H,W=wg.shape; result=wc.copy()
    colors={"roll":(0,220,255),"dob":(255,180,0),"paper":(0,255,80),
            "category":(180,80,255),"gender":(0,200,255)}
    for key,(x0,y0,x1,y1) in REGIONS.items():
        px0,py0,px1,py1=int(x0*W),int(y0*H),int(x1*W),int(y1*H)
        c=colors.get(key,(200,200,200))
        cv2.rectangle(result,(px0,py0),(px1,py1),c,2)
        ov=result.copy(); cv2.rectangle(ov,(px0,py0),(px1,py1),c,-1)
        cv2.addWeighted(ov,0.12,result,0.88,0,result)
        cv2.putText(result,f"{key}:{fields.get(key,'')}",
                    (px0+2,py1+13),cv2.FONT_HERSHEY_SIMPLEX,0.45,c,1)
    show(result,"5  Header Fields",1200)
    cv2.imwrite("debug_header.jpg", result)

def overlay_answers(wc,wg,all_ans,key=None):
    H,W=wg.shape; y0=int(H*GRID_TOP); gh=int(H*(GRID_BOTTOM-GRID_TOP))
    result=wc.copy(); scan(result,"Reading answers",steps=60)
    score=0; q_idx=0
    for g,(x0f,x1f) in enumerate(COL_GROUPS):
        nq=Q_PER_GROUP[g]; gx0,gx1=int(W*x0f),int(W*x1f)
        ow=(gx1-gx0)/OPTS; rh=gh/nq
        for i,(ans,conf) in enumerate(all_ans[q_idx:q_idx+nq]):
            cy=int(y0+i*rh+rh*0.5); cx=int(gx0+(ans+0.5)*ow)
            rad=int(min(rh,ow)*0.30)
            
            if ans == -1:
                # No answer filled
                continue
                
            if key is not None and q_idx+i<len(key):
                ok=(ans==key[q_idx+i]); color=(0,230,80) if ok else (0,50,235)
                if ok: score+=1
            else: color=(0,200,255)
            cv2.circle(result,(cx,cy),rad,color,2)
            cv2.putText(result,f"Q{q_idx+i+1}{'?' if conf<0.35 else ''}",
                        (gx0+2,cy-rad-2),cv2.FONT_HERSHEY_SIMPLEX,0.22,color,1)
        q_idx+=nq
    if key: lbl(result,f"Score:{score}/{len(key)}",pos=(10,H-18),sc=1.1)
    show(result,"6  Results  (any key → next)",wait=0 if not BATCH else 1)
    cv2.imwrite("debug_overlay.jpg", result)
    return score


# ── CSV ────────────────────────────────────────────────────────────────────────

def save_csv(csv_path,record):
    is_new=not os.path.exists(csv_path)
    with open(csv_path,"a",newline="") as f:
        w=csv.DictWriter(f,fieldnames=list(record.keys()))
        if is_new: w.writeheader()
        w.writerow(record)


# ── Key loader ─────────────────────────────────────────────────────────────────

def load_key(path):
    """Load an answer key file. Returns list of int indices (0=A,1=B,...) or None."""
    if not path or not os.path.exists(path):
        return None
    lines=open(path).read().upper().split()
    return [LETTERS.index(c) for c in lines if c in LETTERS]

def load_all_keys():
    """Load all four paper-code key files. Returns dict {code: [int,...]} ."""
    keys = {}
    for code, filename in KEY_FILES.items():
        k = load_key(filename)
        if k is not None:
            keys[code] = k
            print(f"  Key loaded: {filename}  ({len(k)} answers)")
        else:
            print(f"  Key missing: {filename}  (sheets with paper={code} won't be graded)")
    return keys


# ── Per-image pipeline ────────────────────────────────────────────────────────

def process_image(img_path, all_keys, csv_path, idx=1, total=1):
    """Process one OMR image. Detects paper code, picks correct key, grades."""
    img=cv2.imread(img_path)
    if img is None:
        print(f"  [SKIP] Cannot read: {img_path}"); return

    h,w=img.shape[:2]
    if max(h,w)>1500:
        s=1500/max(h,w); img=cv2.resize(img,(int(w*s),int(h*s)))

    if BATCH:
        show_batch_progress(img, os.path.basename(img_path), idx, total)
    else:
        show(img,"0  Original",800)
        scan(img,"Preprocessing")

    gray,dil=preprocess(img)
    cnt=find_sheet(img,dil)
    wc,wg=warp(img,gray,cnt)
    H,W=wg.shape

    if not BATCH:
        for key_r,(x0,y0,x1,y1) in REGIONS.items():
            flash_region(wc,int(x0*W),int(y0*H),int(x1*W),int(y1*H),key_r)
        scan(wc,"Reading header",steps=30)

    roll,_    = read_digit_grid(crop(wg,"roll"),  ROLL_COLS)
    dob_raw,_ = read_digit_grid(crop(wg,"dob"), DOB_COLS)
    dob       = f"{dob_raw[0:2]}/{dob_raw[2:4]}/{dob_raw[4:8]}" if len(dob_raw)==8 else dob_raw
    paper,_   = read_option_row(crop(wg,"paper"),    PAPER_LABELS)
    cat,_     = read_option_row(crop(wg,"category"), CATEGORY_LABELS)
    subcat,_  = read_option_row(crop(wg,"sub_category"), SUBCAT_LABELS)
    gender,_  = read_option_row(crop(wg,"gender"),   GENDER_LABELS)

    # Pick the right answer key based on detected paper code
    key = all_keys.get(paper)
    key_status = f"key={paper}.txt" if key else f"NO KEY for paper={paper}"

    print(f"  Roll:{roll}  DOB:{dob}  Paper:{paper}  Cat:{cat}  SubCat:{subcat}  Gender:{gender}  ({key_status})")

    if not BATCH:
        overlay_header(wc,wg,{"roll":roll,"dob":dob,"paper":paper,"category":cat,"sub_category":subcat,"gender":gender})

    all_ans = read_answers(wg)
    ans_str="".join(LETTERS[a] if a != -1 else "-" for a,_ in all_ans)
    print(f"  Answers: {ans_str}")

    score=overlay_answers(wc,wg,all_ans,key)

    record={
        "image":     os.path.basename(img_path),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "roll_no":   roll, "dob": dob, "gender": gender,
        "paper_set": paper,"category": cat, "sub_category": subcat,
        "score":     score if key else "",
        "total":     len(key) if key else 50,
    }
    for i,(ans,conf) in enumerate(all_ans):
        record[f"Q{i+1}"]=LETTERS[ans] if ans != -1 else ""; record[f"Q{i+1}_conf"]=conf
        if key and i<len(key):
            record[f"Q{i+1}_ok"]="Y" if ans==key[i] else "N"

    save_csv(csv_path,record)
    print(f"  → saved to {csv_path}")


# ── Main ───────────────────────────────────────────────────────────────────────

def main():
    global BATCH

    # Allow overrides, but defaults work out of the box
    inp      = sys.argv[1] if len(sys.argv)>1 else SCAN_FOLDER
    csv_path = sys.argv[2] if len(sys.argv)>2 else CSV_PATH

    print("=" * 60)
    print("  IIT BHU OMR Scanner")
    print("=" * 60)
    print(f"  Images folder : {os.path.abspath(inp)}")
    print(f"  Output CSV    : {os.path.abspath(csv_path)}")
    print(f"  Key files     : {', '.join(KEY_FILES.values())}")
    print("=" * 60)

    # Load all answer keys up front
    all_keys = load_all_keys()
    if not all_keys:
        print("\n  [WARN] No answer key files found — scoring will be skipped.")
        print(f"         Place A.txt / B.txt / C.txt / D.txt in {os.getcwd()}")

    if os.path.isdir(inp):
        # ── BATCH MODE (default)
        BATCH = True
        images=[]
        for ext in IMG_EXTS:
            images+=glob.glob(os.path.join(inp,ext))
            images+=glob.glob(os.path.join(inp,ext.upper()))
        images=sorted(set(images))
        if not images:
            sys.exit(f"\n[ERROR] No images found in: {os.path.abspath(inp)}\n"
                     f"        Place scanned OMR sheets in the '{inp}/' folder.")
        print(f"\n[Batch] {len(images)} images  →  {csv_path}\n")
        for idx,path in enumerate(images,1):
            print(f"[{idx}/{len(images)}] {os.path.basename(path)}")
            try:
                process_image(path, all_keys, csv_path, idx, len(images))
            except Exception as e:
                print(f"  [ERROR] {e}")
        print(f"\n{'=' * 60}")
        print(f"  DONE — {len(images)} sheets processed")
        print(f"  Results : {os.path.abspath(csv_path)}")
        print(f"{'=' * 60}")
    else:
        # ── SINGLE IMAGE MODE
        BATCH = False
        if not os.path.isfile(inp):
            sys.exit(f"\n[ERROR] Not found: {inp}")
        print(f"\n[Single] {inp}\n")
        process_image(inp, all_keys, csv_path)

    cv2.destroyAllWindows()


if __name__=="__main__":
    main()
