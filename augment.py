#!/usr/bin/env python3
"""
Phase 2 — Image Augmentation Pipeline
Applies realistic distortions to synthetic OMR sheets.

Usage:
    python augment.py --input output/sheets/ --output output/augmented/ --per-image 5
"""

import argparse, json, os, random, shutil
from pathlib import Path

import cv2
import numpy as np


# ── Augmentation functions ───────────────────────────────────────────────────

def perspective_warp(img, strength=0.08):
    """Random 4-corner perspective shift."""
    h, w = img.shape[:2]
    margin = int(max(h, w) * strength)
    src = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    dst = np.float32([
        [random.randint(0, margin), random.randint(0, margin)],
        [w - random.randint(0, margin), random.randint(0, margin)],
        [w - random.randint(0, margin), h - random.randint(0, margin)],
        [random.randint(0, margin), h - random.randint(0, margin)],
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def gaussian_noise(img, sigma=None):
    """Additive Gaussian noise."""
    if sigma is None:
        sigma = random.randint(5, 25)
    noise = np.random.normal(0, sigma, img.shape).astype(np.float32)
    noisy = np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)
    return noisy


def salt_pepper(img, density=None):
    """Salt and pepper noise."""
    if density is None:
        density = random.uniform(0.005, 0.02)
    out = img.copy()
    # Salt
    n_salt = int(density * img.size / 2)
    coords = [np.random.randint(0, max(1, i - 1), n_salt) for i in img.shape]
    out[coords[0], coords[1]] = 255
    # Pepper
    coords = [np.random.randint(0, max(1, i - 1), n_salt) for i in img.shape]
    out[coords[0], coords[1]] = 0
    return out


def motion_blur(img, kernel_size=None):
    """Directional motion blur."""
    if kernel_size is None:
        kernel_size = random.choice(range(3, 16, 2))
    angle = random.uniform(0, 360)
    M = cv2.getRotationMatrix2D((kernel_size // 2, kernel_size // 2), angle, 1)
    kernel = np.zeros((kernel_size, kernel_size))
    kernel[kernel_size // 2, :] = 1.0
    kernel = cv2.warpAffine(kernel, M, (kernel_size, kernel_size))
    kernel /= kernel.sum()
    return cv2.filter2D(img, -1, kernel)


def brightness_shift(img, gamma=None):
    """Gamma correction for brightness change."""
    if gamma is None:
        gamma = random.uniform(0.5, 1.8)
    table = np.array([((i / 255.0) ** (1.0 / gamma)) * 255
                      for i in range(256)]).astype(np.uint8)
    return cv2.LUT(img, table)


def shadow_overlay(img, alpha=None):
    """Overlay a random dark polygon to simulate shadow."""
    if alpha is None:
        alpha = random.uniform(0.3, 0.6)
    h, w = img.shape[:2]
    overlay = img.copy()
    n_pts = random.randint(3, 6)
    pts = np.array([[random.randint(0, w), random.randint(0, h)] for _ in range(n_pts)])
    cv2.fillConvexPoly(overlay, pts, (0, 0, 0) if img.ndim == 3 else 0)
    return cv2.addWeighted(overlay, alpha, img, 1 - alpha, 0)


def jpeg_artifacts(img, quality=None):
    """Simulate JPEG compression artifacts."""
    if quality is None:
        quality = random.randint(40, 95)
    encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), quality]
    _, buf = cv2.imencode(".jpg", img, encode_param)
    return cv2.imdecode(buf, cv2.IMREAD_COLOR if img.ndim == 3 else cv2.IMREAD_GRAYSCALE)


def rotation_crop(img, angle=None):
    """Random rotation with border replication."""
    if angle is None:
        angle = random.uniform(-12, 12)
    h, w = img.shape[:2]
    M = cv2.getRotationMatrix2D((w // 2, h // 2), angle, 1.0)
    return cv2.warpAffine(img, M, (w, h), borderMode=cv2.BORDER_REPLICATE)


def page_curl(img, amplitude=None):
    """Sinusoidal x/y remapping to simulate page bending."""
    if amplitude is None:
        amplitude = random.uniform(5, 20)
    h, w = img.shape[:2]
    map_x = np.zeros((h, w), dtype=np.float32)
    map_y = np.zeros((h, w), dtype=np.float32)
    freq = random.uniform(1, 3)
    for y in range(h):
        for x in range(w):
            map_x[y, x] = x + amplitude * np.sin(2 * np.pi * y / h * freq)
            map_y[y, x] = y + amplitude * np.sin(2 * np.pi * x / w * freq)
    return cv2.remap(img, map_x, map_y, cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)


# ── Registry ─────────────────────────────────────────────────────────────────

AUGMENTATIONS = {
    "perspective":  perspective_warp,
    "gauss_noise":  gaussian_noise,
    "salt_pepper":  salt_pepper,
    "motion_blur":  motion_blur,
    "brightness":   brightness_shift,
    "shadow":       shadow_overlay,
    "jpeg":         jpeg_artifacts,
    "rotation":     rotation_crop,
    "page_curl":    page_curl,
}


# ── Pipeline ─────────────────────────────────────────────────────────────────

def augment_image(img, n_augments=None):
    """Apply a random subset of augmentations. Returns (augmented_img, list_of_names)."""
    if n_augments is None:
        n_augments = random.randint(2, 5)
    names = random.sample(list(AUGMENTATIONS.keys()), min(n_augments, len(AUGMENTATIONS)))
    result = img.copy()
    for name in names:
        result = AUGMENTATIONS[name](result)
    return result, names


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Augment synthetic OMR sheets")
    parser.add_argument("--input", type=str, default="output/sheets/", help="Input folder with PNGs + JSONs")
    parser.add_argument("--output", type=str, default="output/augmented/", help="Output folder")
    parser.add_argument("--per-image", type=int, default=5, help="Augmented copies per input image")
    parser.add_argument("--seed", type=int, default=None, help="Random seed")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    inp = Path(args.input)
    out = Path(args.output)
    out.mkdir(parents=True, exist_ok=True)

    pngs = sorted(inp.glob("*.png"))
    if not pngs:
        print(f"[ERROR] No PNG files in {inp}")
        return

    total = len(pngs) * args.per_image
    count = 0
    print(f"Augmenting {len(pngs)} sheets × {args.per_image} = {total} images → {out}/\n")

    for png_path in pngs:
        json_path = png_path.with_suffix(".json")
        img = cv2.imread(str(png_path))
        if img is None:
            print(f"  [SKIP] Cannot read: {png_path}")
            continue

        # Load ground truth if exists
        gt = None
        if json_path.exists():
            with open(json_path) as f:
                gt = json.load(f)

        # Also copy the clean original
        stem = png_path.stem
        shutil.copy2(str(png_path), str(out / f"{stem}_clean.png"))
        if gt:
            gt_copy = gt.copy()
            gt_copy["augmentations"] = ["clean"]
            with open(out / f"{stem}_clean.json", "w") as f:
                json.dump(gt_copy, f, indent=2)

        for a in range(1, args.per_image + 1):
            count += 1
            aug_img, aug_names = augment_image(img)
            aug_stem = f"{stem}_aug{a:02d}"
            cv2.imwrite(str(out / f"{aug_stem}.png"), aug_img)

            if gt:
                gt_copy = gt.copy()
                gt_copy["augmentations"] = aug_names
                gt_copy["sheet_id"] = aug_stem
                with open(out / f"{aug_stem}.json", "w") as f:
                    json.dump(gt_copy, f, indent=2)

            print(f"  [{count}/{total}] {aug_stem}.png  augments={aug_names}")

    print(f"\nDone. {count} augmented images saved to {out}/")


if __name__ == "__main__":
    main()
