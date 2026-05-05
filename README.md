# IIT BHU OMR Scanner

A highly robust, locally executable, and Android-compatible OMR scanner.

## Features
- **Unbeatable Precision**: Uses strict local adaptive thresholding (`C=30`) and area-fill percentage (`>40%`) to perfectly ignore heavy shadows, folds, and printed text inside empty bubbles.
- **Customizable**: Allows defining tight bubble grids per-sheet via an interactive GUI.
- **Cross-Platform Backend**: Run batch scanning purely in Python, or package it into a Kivy Android APK.

## 1. Setup

Create and activate a dedicated environment:
```bash
mamba create -n omr python=3.10 opencv-python numpy kivy pillow
mamba activate omr
```

## 2. Calibration (Run Once Per Sheet Design)

Before scanning, you must tell the scanner exactly where the bubbles are on your sheet.

1. Ensure you have a blank template of your printed OMR sheet (e.g. `image.png`).
2. Run the interactive selector:
   ```bash
   python select_regions.py image.png
   ```
3. A window will open showing your flattened sheet.
4. Click and drag to draw **tight boxes** around **ONLY the circular bubbles** for each requested section. Do not include the printed text headers or question numbers inside the green boxes.
5. This saves the perfect fractional coordinates into `regions.json`.

## 3. Local Batch Scanning

To scan a folder of filled OMR sheets locally and output to CSV:

```bash
python omr_scanner.py path/to/images/ output.csv
```
The scanner will parse `regions.json`, read the keys (`A.txt` through `D.txt`), evaluate the bubbles, grade the papers, and write the output.

## 4. Android App (Kivy / Buildozer)

The exact same OMR backend is integrated into a Kivy mobile app!
1. Ensure your calibrated `regions.json` and Answer Keys (`A.txt`, etc.) are in the root directory.
2. The UI is defined in `main.py`.
3. To compile to Android (on Linux/macOS):
   ```bash
   buildozer android debug
   ```
   *Note: This generates a `.apk` inside `bin/` which you can install on your phone to scan OMR sheets live via camera.*
