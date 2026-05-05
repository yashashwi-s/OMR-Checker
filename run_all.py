#!/usr/bin/env python3
"""
End-to-End OMR Pipeline Driver
Generates synthetic sheets → augments → scans → evaluates.

Usage:
    python run_all.py                       # defaults: 10 sheets, 3 augments each
    python run_all.py --sheets 20 --augments 5
"""

import argparse, os, subprocess, sys, shutil


PYTHON = sys.executable  # use same interpreter


def run(cmd, desc):
    print(f"\n{'='*60}")
    print(f"  STEP: {desc}")
    print(f"  CMD:  {' '.join(cmd)}")
    print(f"{'='*60}\n")
    result = subprocess.run(cmd, cwd=os.path.dirname(os.path.abspath(__file__)))
    if result.returncode != 0:
        print(f"\n[FAIL] {desc} exited with code {result.returncode}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Run full OMR pipeline")
    parser.add_argument("--sheets", type=int, default=10, help="Number of synthetic sheets")
    parser.add_argument("--augments", type=int, default=3, help="Augmented copies per sheet")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--clean", action="store_true", help="Remove old output before running")
    args = parser.parse_args()

    base = os.path.dirname(os.path.abspath(__file__))

    if args.clean:
        for d in ["output/sheets", "output/augmented", "output/results"]:
            p = os.path.join(base, d)
            if os.path.exists(p):
                shutil.rmtree(p)
                print(f"  Cleaned: {p}")

    # 1. Generate synthetic sheets
    run([PYTHON, "generate_omr.py",
         "--count", str(args.sheets),
         "--out", "output/sheets/",
         "--seed", str(args.seed)],
        f"Generate {args.sheets} synthetic OMR sheets")

    # 2. Augment
    run([PYTHON, "augment.py",
         "--input", "output/sheets/",
         "--output", "output/augmented/",
         "--per-image", str(args.augments),
         "--seed", str(args.seed)],
        f"Augment sheets ({args.augments}× each)")

    # 3. Copy augmented images to responses/ for scanning
    responses = os.path.join(base, "responses")
    os.makedirs(responses, exist_ok=True)
    aug_dir = os.path.join(base, "output", "augmented")
    count = 0
    for f in sorted(os.listdir(aug_dir)):
        if f.lower().endswith(".png"):
            shutil.copy2(os.path.join(aug_dir, f), os.path.join(responses, f))
            count += 1
    print(f"\n  Copied {count} augmented images → responses/")

    # 4. Remove old grades.csv so we start fresh
    csv_path = os.path.join(base, "grades.csv")
    if os.path.exists(csv_path):
        os.remove(csv_path)

    # 5. Run scanner
    run([PYTHON, "omr_scanner.py"],
        "Scan all images in responses/")

    # 6. Evaluate
    run([PYTHON, "eval_accuracy.py",
         "--csv", "grades.csv",
         "--ground-truth", "output/augmented/",
         "--report", "output/results/eval_report.md"],
        "Evaluate accuracy")

    print(f"\n{'='*60}")
    print(f"  ALL DONE")
    print(f"  Sheets generated : output/sheets/")
    print(f"  Augmented images : output/augmented/")
    print(f"  Grades CSV       : grades.csv")
    print(f"  Eval report      : output/results/eval_report.md")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
