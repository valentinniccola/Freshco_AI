import os
import cv2
import numpy as np
from pathlib import Path

samples_dir = Path(__file__).resolve().parent / "static" / "samples"
samples_dir.mkdir(parents=True, exist_ok=True)

def safe_imwrite(filepath: Path, img: np.ndarray):
    is_success, buffer = cv2.imencode(".jpg", img)
    if is_success:
        with open(filepath, "wb") as f:
            f.write(buffer)

def create_apple_fresh():
    img = np.full((300, 300, 3), (210, 215, 220), dtype=np.uint8)
    cv2.circle(img, (150, 160), 100, (40, 45, 215), -1, cv2.LINE_AA)
    cv2.circle(img, (130, 140), 40, (70, 75, 235), -1, cv2.LINE_AA)
    cv2.line(img, (150, 60), (145, 25), (30, 60, 100), 5, cv2.LINE_AA)
    pts = np.array([[145, 30], [180, 20], [170, 45]], np.int32)
    cv2.fillPoly(img, [pts], (40, 160, 50))
    safe_imwrite(samples_dir / "apple_fresh.jpg", img)

def create_banana_spotted():
    img = np.full((300, 300, 3), (210, 215, 220), dtype=np.uint8)
    pts = np.array([[60, 200], [150, 220], [240, 160], [230, 130], [150, 180], [70, 160]], np.int32)
    cv2.fillPoly(img, [pts], (30, 210, 245)) # Bright yellow body
    np.random.seed(42)
    # Distinct aging brown sugar spots (Nearly Spoiled)
    for _ in range(22):
        x = np.random.randint(90, 210)
        y = np.random.randint(155, 200)
        r = np.random.randint(2, 5)
        cv2.circle(img, (x, y), r, (25, 45, 75), -1, cv2.LINE_AA)
    safe_imwrite(samples_dir / "banana_spotted.jpg", img)

def create_tomato_fresh():
    img = np.full((300, 300, 3), (210, 215, 220), dtype=np.uint8)
    cv2.circle(img, (150, 155), 95, (30, 35, 220), -1, cv2.LINE_AA)
    cv2.circle(img, (120, 125), 30, (60, 70, 245), -1, cv2.LINE_AA)
    for angle in [0, 60, 120, 180, 240, 300]:
        rad = np.deg2rad(angle)
        ex = int(150 + 35 * np.cos(rad))
        ey = int(70 + 20 * np.sin(rad))
        cv2.line(img, (150, 70), (ex, ey), (40, 170, 50), 4, cv2.LINE_AA)
    safe_imwrite(samples_dir / "tomato_fresh.jpg", img)

def create_orange_spoiled():
    img = np.full((300, 300, 3), (210, 215, 220), dtype=np.uint8)
    cv2.circle(img, (150, 150), 95, (20, 120, 230), -1, cv2.LINE_AA)
    cv2.ellipse(img, (130, 130), (55, 45), 25, 0, 360, (50, 70, 80), -1)
    cv2.ellipse(img, (135, 135), (40, 30), 25, 0, 360, (140, 180, 130), -1)
    cv2.ellipse(img, (140, 140), (22, 16), 25, 0, 360, (210, 230, 215), -1)
    safe_imwrite(samples_dir / "orange_spoiled.jpg", img)

def create_bread_spoiled():
    img = np.full((300, 300, 3), (210, 215, 220), dtype=np.uint8)
    pts = np.array([[70, 110], [90, 80], [150, 75], [210, 80], [230, 110], [225, 230], [75, 230]], np.int32)
    cv2.fillPoly(img, [pts], (160, 205, 235))
    cv2.polylines(img, [pts], True, (60, 110, 160), 5)
    for center, rad in [((115, 135), 34), ((175, 170), 40), ((145, 195), 30), ((185, 120), 25)]:
        cv2.circle(img, center, rad, (40, 65, 45), -1)
        cv2.circle(img, center, rad - 8, (80, 130, 95), -1)
        cv2.circle(img, center, rad - 16, (170, 205, 185), -1)
    safe_imwrite(samples_dir / "bread_spoiled.jpg", img)

def create_meat_fresh():
    img = np.full((300, 300, 3), (210, 215, 220), dtype=np.uint8)
    pts = np.array([[70, 150], [110, 90], [190, 85], [240, 130], [230, 210], [150, 225], [80, 200]], np.int32)
    cv2.fillPoly(img, [pts], (45, 45, 185))
    cv2.ellipse(img, (140, 130), (35, 10), 30, 0, 360, (215, 220, 240), 2)
    cv2.ellipse(img, (180, 165), (25, 8), -20, 0, 360, (215, 220, 240), 2)
    safe_imwrite(samples_dir / "meat_fresh.jpg", img)

if __name__ == "__main__":
    create_apple_fresh()
    create_banana_spotted()
    create_tomato_fresh()
    create_orange_spoiled()
    create_bread_spoiled()
    create_meat_fresh()
    print("Generated all food freshness sample images successfully.")
