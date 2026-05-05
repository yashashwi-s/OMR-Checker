import cv2
import numpy as np

img = cv2.imread('image.png', cv2.IMREAD_GRAYSCALE)
h, w = img.shape[:2]
s = 1500 / max(h, w)
img = cv2.resize(img, (int(w * s), int(h * s)))

t = cv2.adaptiveThreshold(img, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 151, 40)

cv2.imwrite('debug_thresh_151_40.png', t)

# Let's count non-zero pixels in the whole image. If it's an empty sheet, there should be very few non-zero pixels inside the bubbles (the borders might be visible, but we can filter those out by checking only the center).
print(f"Total non-zero pixels: {cv2.countNonZero(t)}")
