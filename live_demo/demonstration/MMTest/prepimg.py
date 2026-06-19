import cv2
import numpy as np
import os
from glob import glob

INPUT_FOLDER = "pics"
OUTPUT_FOLDER = r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\cropped"
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

image_paths = glob(os.path.join(INPUT_FOLDER, r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\pics\*.jpg")) + \
              glob(os.path.join(INPUT_FOLDER, r"C:\Users\Faebe\Desktop\MLonMCU\project\demonstration\MMTest\pics\*.jpeg"))

def circularity(cnt):
    area = cv2.contourArea(cnt)
    perimeter = cv2.arcLength(cnt, True)
    if perimeter == 0:
        return 0
    return 4 * np.pi * (area / (perimeter * perimeter))

def process_image(image_path):
    img = cv2.imread(image_path)
    if img is None:
        return

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    h, s, v = cv2.split(hsv)

    # =========================
    # STRONG GREY / SHADOW REMOVAL
    # =========================

    # lenient saturation filter (allow muted colors)
    sat_mask = cv2.inRange(s, 50, 255)

    # allow darker pixels
    val_mask = cv2.inRange(v, 40, 255)

    # OPTIONAL: very light gray filter - mostly disabled to preserve edges
    gray_mask = cv2.inRange(cv2.absdiff(s, v), 0, 255)

    # combine (still AND, but now all are strong filters)
    mask = cv2.bitwise_and(sat_mask, val_mask)
    mask = cv2.bitwise_and(mask, gray_mask)

    # =========================
    # CLEANUP
    # =========================
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

    # =========================
    # FIND BEST OBJECT
    # =========================
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    best = None
    best_score = 0

    for cnt in contours:
        area = cv2.contourArea(cnt)

        if area < 250:
            continue

        c = circularity(cnt)
        score = area * (0.5 + c)

        if score > best_score:
            best_score = score
            best = cnt

    if best is None:
        print(f"No valid M&M in {image_path}")
        return

    if circularity(best) < 0.1:
        print(f"Low quality object (kept anyway): {image_path}")

    # =========================
    # TIGHT MASK CROPPING
    # =========================
    mask_clean = np.zeros_like(mask)
    cv2.drawContours(mask_clean, [best], -1, 255, -1)

    coords = cv2.findNonZero(mask_clean)
    if coords is None:
        print(f"Empty mask: {image_path}")
        return

    x, y, w, h = cv2.boundingRect(coords)

    pad = 20

    # Add padding first
    x -= pad
    y -= pad
    w += 2 * pad
    h += 2 * pad

    # Make square
    side = max(w, h)

    cx = x + w // 2
    cy = y + h // 2

    x = cx - side // 2
    y = cy - side // 2

    # Clamp to image bounds
    img_h, img_w = img.shape[:2]

    x = max(0, x)
    y = max(0, y)

    if x + side > img_w:
        x = img_w - side

    if y + side > img_h:
        y = img_h - side

    x = max(0, x)
    y = max(0, y)

    crop = img[y:y+side, x:x+side]

    base = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(OUTPUT_FOLDER, f"{base}.jpg")

    cv2.imwrite(out_path, crop)
    print(f"Saved: {out_path}")

for path in image_paths:
    process_image(path)

print("Done.")