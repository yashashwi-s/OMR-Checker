#!/usr/bin/env python3
"""
Phase 4 — Accuracy Evaluation
Compares scanner output (grades.csv) against ground-truth JSONs.

Usage:
    python eval_accuracy.py --csv grades.csv --ground-truth output/augmented/ --report output/results/eval_report.md
"""

import argparse, csv, json, os
from pathlib import Path
from collections import defaultdict


def load_ground_truth(gt_dir):
    """Load all ground-truth JSONs into a dict keyed by image basename (no ext)."""
    gt = {}
    for jf in Path(gt_dir).glob("*.json"):
        with open(jf) as f:
            data = json.load(f)
        # key by sheet_id or filename stem
        key = jf.stem
        gt[key] = data
    return gt


def load_csv(csv_path):
    """Load grades.csv rows into a list of dicts."""
    rows = []
    with open(csv_path) as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows


def evaluate(csv_rows, gt_dict):
    """Compare scanner output to ground truth. Returns metrics dict."""
    metrics = {
        "total_images": 0,
        "matched_images": 0,
        "field_correct": defaultdict(int),
        "field_total": defaultdict(int),
        "q_correct": 0,
        "q_total": 0,
        "per_augment": defaultdict(lambda: {"correct": 0, "total": 0}),
        "errors": [],
    }

    for row in csv_rows:
        img_name = row.get("image", "")
        stem = os.path.splitext(img_name)[0]
        gt = gt_dict.get(stem)

        metrics["total_images"] += 1

        if gt is None:
            metrics["errors"].append(f"{img_name}: no ground-truth JSON found")
            continue

        metrics["matched_images"] += 1

        # Field comparisons
        field_map = {
            "roll_no": "roll_no",
            "dob": "dob",
            "gender": "gender",
            "paper_set": "paper_set",
            "category": "category",
            "sub_category": "sub_category",
        }
        for csv_field, gt_field in field_map.items():
            csv_val = row.get(csv_field, "").strip()
            gt_val = str(gt.get(gt_field, "")).strip()
            metrics["field_total"][csv_field] += 1
            if csv_val == gt_val:
                metrics["field_correct"][csv_field] += 1

        # Answer comparisons
        gt_answers = gt.get("answers", [])
        aug_names = gt.get("augmentations", ["unknown"])
        for i, gt_ans in enumerate(gt_answers):
            csv_ans = row.get(f"Q{i+1}", "")
            metrics["q_total"] += 1
            correct = (csv_ans.upper() == gt_ans.upper())
            if correct:
                metrics["q_correct"] += 1
            for aug in aug_names:
                metrics["per_augment"][aug]["total"] += 1
                if correct:
                    metrics["per_augment"][aug]["correct"] += 1

    return metrics


def format_report(metrics):
    """Format metrics as a markdown report."""
    lines = []
    lines.append("# OMR Scanner — Accuracy Evaluation Report\n")

    total = metrics["total_images"]
    matched = metrics["matched_images"]
    lines.append(f"**Images scanned:** {total}  ")
    lines.append(f"**Matched to ground truth:** {matched}  ")
    if metrics["errors"]:
        lines.append(f"**Unmatched:** {len(metrics['errors'])}\n")

    # Overall answer accuracy
    qc, qt = metrics["q_correct"], metrics["q_total"]
    pct = (qc / qt * 100) if qt else 0
    lines.append(f"\n## Overall Answer Accuracy\n")
    lines.append(f"**{qc} / {qt}  ({pct:.1f}%)**\n")

    # Per-field accuracy
    lines.append("## Per-Field Accuracy\n")
    lines.append("| Field | Correct | Total | Accuracy |")
    lines.append("|-------|---------|-------|----------|")
    for field in ["roll_no", "dob", "gender", "paper_set", "category", "sub_category"]:
        c = metrics["field_correct"].get(field, 0)
        t = metrics["field_total"].get(field, 0)
        p = (c / t * 100) if t else 0
        lines.append(f"| {field} | {c} | {t} | {p:.1f}% |")

    # Per-augmentation accuracy
    lines.append("\n## Per-Augmentation Accuracy\n")
    lines.append("| Augmentation | Correct | Total | Accuracy |")
    lines.append("|-------------|---------|-------|----------|")
    for aug, vals in sorted(metrics["per_augment"].items()):
        c, t = vals["correct"], vals["total"]
        p = (c / t * 100) if t else 0
        lines.append(f"| {aug} | {c} | {t} | {p:.1f}% |")

    # Errors
    if metrics["errors"]:
        lines.append("\n## Errors\n")
        for e in metrics["errors"][:20]:
            lines.append(f"- {e}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate OMR scanner accuracy")
    parser.add_argument("--csv", type=str, default="grades.csv", help="Scanner output CSV")
    parser.add_argument("--ground-truth", type=str, default="output/augmented/",
                        help="Folder with ground-truth JSONs")
    parser.add_argument("--report", type=str, default="output/results/eval_report.md",
                        help="Output report path")
    args = parser.parse_args()

    print(f"Loading CSV: {args.csv}")
    csv_rows = load_csv(args.csv)
    print(f"  {len(csv_rows)} rows loaded")

    print(f"Loading ground truth: {args.ground_truth}")
    gt = load_ground_truth(args.ground_truth)
    print(f"  {len(gt)} JSONs loaded")

    print("Evaluating...")
    metrics = evaluate(csv_rows, gt)
    report = format_report(metrics)

    # Save report
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        f.write(report)

    # Print summary
    print(f"\n{report}\n")
    print(f"Report saved to {report_path}")


if __name__ == "__main__":
    main()
