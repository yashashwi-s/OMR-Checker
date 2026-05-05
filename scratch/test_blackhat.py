import cv2
import numpy as np

img = cv2.imread('image.png', cv2.IMREAD_GRAYSCALE)
h, w = img.shape[:2]
s = 1500 / max(h, w)
img = cv2.resize(img, (int(w * s), int(h * s)))

k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (25, 25))
blackhat = cv2.morphologyEx(img, cv2.MORPH_BLACKHAT, k)

# Apply a simple threshold to the blackhat image
_, th = cv2.threshold(blackhat, 50, 255, cv2.THRESH_BINARY)
cv2.imwrite('debug_blackhat.png', th)

print(f"Total non-zero pixels in blackhat: {cv2.countNonZero(th)}")
