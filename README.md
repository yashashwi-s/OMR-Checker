# IIT BHU OMR Scanner

Scans OMR answer sheets, detects paper code (A/B/C/D), grades against the matching answer key, and saves results to a single CSV.

## Quick Start

```bash
# 1. Install dependencies (once)
mamba run -n omr pip install -r requirements.txt

# 2. Place scanned images in responses/
#    Place answer keys as A.txt, B.txt, C.txt, D.txt

# 3. Run — that's it
mamba run -n omr python omr_scanner.py
```

Results appear in `grades.csv`.

---

## How to Capture Images

| Tip | Why |
|-----|-----|
| **Lay sheet flat** on a dark surface | Helps edge detection find the boundary |
| **Shoot from directly above** | Minimises perspective distortion |
| **Good even lighting**, no shadows | Shadows confuse bubble detection |
| **Resolution ≥ 1500px** on longest side | Needed for accurate bubble reading |
| **Avoid flash glare** on the paper | Washes out bubbles |

Phone camera in document mode works well. Scanners at 200+ dpi are ideal.

---

## File Structure

```
omr/
├── omr_scanner.py      # Main scanner — just run it
├── generate_omr.py     # Generate synthetic test sheets
├── augment.py          # Augment images (noise, blur, tilt, etc.)
├── eval_accuracy.py    # Compare grades.csv vs ground-truth
├── run_all.py          # One-command end-to-end pipeline
├── requirements.txt    # Python dependencies
├── A.txt … D.txt       # Answer keys per paper code
├── responses/          # ← Put scanned images here
├── output/
│   ├── sheets/         # Generated synthetic sheets
│   ├── augmented/      # Augmented images + ground truth
│   └── results/        # Evaluation report
└── grades.csv          # ← Output: one row per image
```

---

## Usage

### Grade real sheets
```bash
# Put images in responses/, keys in A.txt-D.txt, then:
mamba run -n omr python omr_scanner.py
```

### Grade a single image
```bash
mamba run -n omr python omr_scanner.py photo.jpg
```

### Run full synthetic test pipeline
```bash
mamba run -n omr python run_all.py --sheets 10 --augments 3 --clean
```

### Generate synthetic sheets only
```bash
mamba run -n omr python generate_omr.py --count 20 --out output/sheets/
```

### Augment images only
```bash
mamba run -n omr python augment.py --input output/sheets/ --output output/augmented/ --per-image 5
```

---

## Interpreting grades.csv

| Column | Meaning |
|--------|---------|
| `image` | Filename of the scanned image |
| `roll_no` | Detected 9-digit roll number |
| `dob` | Date of birth (DD/MM/YYYY) |
| `gender` | M / F / O |
| `paper_set` | Detected paper code (A/B/C/D) |
| `category` | UR / SC / ST / OBC / EWS |
| `score` | Number of correct answers (vs matching key) |
| `total` | Total questions in key |
| `Q1`…`Q50` | Detected answer for each question |
| `Q1_conf`…`Q50_conf` | Confidence score (0–1) for each bubble |
| `Q1_ok`…`Q50_ok` | Y/N — correct vs answer key |

**Low confidence** (`< 0.35`): bubble detection was uncertain — check manually.

---

## Answer Key Format

One answer per line (A/B/C/D), Q1 to Q50:
```
A
B
C
D
A
...
```

Create separate files: `A.txt`, `B.txt`, `C.txt`, `D.txt` — one per paper code.

---

## Tuning

Edit the top of `omr_scanner.py`:
```python
REGIONS = {
    "roll":     (0.02, 0.09, 0.30, 0.38),  # x0 y0 x1 y1 (fractions)
    "dob":      (0.31, 0.09, 0.66, 0.38),
    "paper":    (0.02, 0.38, 0.22, 0.45),
    "category": (0.24, 0.37, 0.67, 0.45),
    "gender":   (0.78, 0.37, 0.99, 0.45),
}
GRID_TOP    = 0.44
GRID_BOTTOM = 0.96
```

In single-image mode, each region flashes on screen so you can see if it's misaligned.
