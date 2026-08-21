import os
import cv2
import numpy as np
from pathlib import Path
from ai.model import classifier
from ai.shelf_life import ShelfLifeEstimator

BASE_DIR = Path(__file__).resolve().parent
samples = ['apple_fresh.jpg', 'banana_spotted.jpg', 'orange_spoiled.jpg', 'bread_spoiled.jpg', 'meat_fresh.jpg']

for name in samples:
    path = BASE_DIR / 'static' / 'samples' / name
    if not path.exists():
        print(f"File does not exist: {path}")
        continue
        
    with open(path, "rb") as f:
        bytes_data = f.read()
    img_bgr = cv2.imdecode(np.frombuffer(bytes_data, np.uint8), cv2.IMREAD_COLOR)
    
    status, conf, probs, defects = classifier.predict(img_bgr)
    shelf = ShelfLifeEstimator.estimate(status, 'Fruit', defects)
    print(f"=== {name} ===")
    print(f"Status: {status} (Confidence: {conf*100:.1f}%)")
    print(f"Probabilities: {probs}")
    print(f"Defect Metrics: {defects}")
    print(f"Shelf Life: {shelf['shelf_life_days']} days | {shelf['shelf_life_desc']}")
    print(f"Advice: {shelf['action_recommendation']}")
    print("-" * 50)
